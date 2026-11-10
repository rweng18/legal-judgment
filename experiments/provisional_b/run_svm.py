"""Add Batch B linear SVM using the saved logistic-regression folds."""
import argparse
import csv
import json
import warnings
from pathlib import Path

import numpy as np
from sklearn.exceptions import ConvergenceWarning

from data import sha_file
from experiment import save_run
from modeling import evaluate
from run_majority import csv_by_id, load_assumed_batch_b


def load_reference(package, logistic_run, assume_labels_reviewed=False):
    release, rows = load_assumed_batch_b(package, assume_labels_reviewed)
    original = json.loads((logistic_run / "run.json").read_text())
    if release["inputs"] != original["release"]["inputs"]:
        raise ValueError("Input files differ from the logistic-regression run.")
    previous = csv_by_id(logistic_run / "splits.csv")
    fields = ("case_id", "batch", "family_id", "date_filed", "label", "period")
    if ({r["case_id"] for r in rows} != previous.keys()
            or any(str(row[k]) != previous[row["case_id"]][k] for row in rows for k in fields)):
        raise ValueError("Case membership or labels differ from the saved run.")
    training = [r for r in rows if r["period"] == "train"]
    membership = np.array([int(previous[r["case_id"]]["held_out_cv_fold"]) for r in training])
    expected_folds = set(range(1, original["cv_folds"] + 1))
    if set(membership) != expected_folds or len(expected_folds) not in (2, 3):
        raise ValueError("Expected two or three saved training folds.")
    folds = [(np.flatnonzero(membership != f), np.flatnonzero(membership == f))
             for f in sorted(expected_folds)]
    for fit, hold in folds:
        if not {training[i]["family_id"] for i in fit}.isdisjoint(
                {training[i]["family_id"] for i in hold}):
            raise ValueError("A saved family crosses folds.")
        if any({training[i]["label"] for i in indices} != {0, 1} for indices in (fit, hold)):
            raise ValueError("A saved fold lacks one of the outcome classes.")
    return release, rows, folds, original


def run(package, logistic_run, destination, assume_labels_reviewed=False):
    if destination.exists():
        raise FileExistsError(f"Choose a fresh output directory: {destination}")
    release, rows, folds, original = load_reference(package, logistic_run, assume_labels_reviewed)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        results = [evaluate(name, rows, folds) for name in ("Majority", "TFIDF_LR", "TFIDF_SVM")]
    saved_selection = json.loads((logistic_run / "selection.json").read_text())
    with (logistic_run / "predictions.csv").open(newline="", encoding="utf-8") as stream:
        old_predictions = list(csv.DictReader(stream))
    for result in results[:2]:
        if saved_selection[result["model"]] != {"selected_C": result["selected_C"], "grid": result["cv"]}:
            raise ValueError(f"{result['model']} selection changed during reproduction.")
        expected = [r for r in old_predictions if r["model"] == result["model"]]
        actual = [{k: "" if v is None else str(v) for k, v in r.items()} for r in result["predictions"]]
        if actual != expected:
            raise ValueError(f"{result['model']} predictions changed during reproduction.")
    release["logistic_reference"] = {
        name: sha_file(logistic_run / name)
        for name in ("run.json", "splits.csv", "selection.json", "predictions.csv")
    }
    release["majority_reference"] = original["release"]["majority_reference"]
    output = save_run(destination, release, rows, folds, results)
    print(json.dumps({"output": str(output), "selected_C": results[2]["selected_C"],
                      "cv": results[2]["cv"], "metrics": results[2]["metrics"],
                      "previous_baselines_reproduced": True}, indent=2))
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("logistic_run", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--assume-labels-reviewed", action="store_true", required=True)
    args = parser.parse_args()
    run(args.package, args.logistic_run, args.out, args.assume_labels_reviewed)
