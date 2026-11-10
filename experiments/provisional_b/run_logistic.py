"""Run Batch B TF-IDF logistic regression against the saved majority baseline."""
import argparse
import csv
import json
from pathlib import Path

from data import sha_file
from experiment import save_run
from modeling import evaluate, grouped_folds
from run_majority import load_assumed_batch_b


def run(package, majority_run, destination, assume_labels_reviewed=False):
    if destination.exists():
        raise FileExistsError(f"Choose a fresh output directory: {destination}")
    release, rows = load_assumed_batch_b(package, assume_labels_reviewed)
    original = json.loads((majority_run / "run.json").read_text())
    if release["inputs"] != original["release"]["inputs"]:
        raise ValueError("Input files differ from the majority run.")
    with (majority_run / "splits.csv").open(newline="", encoding="utf-8") as stream:
        previous = list(csv.DictReader(stream))
    fields = ("case_id", "batch", "family_id", "date_filed", "label", "period")
    current_cases = {tuple(str(row[k]) for k in fields) for row in rows}
    previous_cases = {tuple(row[k] for k in fields) for row in previous}
    if len(previous) != len(rows) or current_cases != previous_cases:
        raise ValueError("Case membership or labels differ from the majority run.")
    training = [row for row in rows if row["period"] == "train"]
    folds = grouped_folds(training)
    for fit, hold in folds:
        if not {training[i]["family_id"] for i in fit}.isdisjoint(
                {training[i]["family_id"] for i in hold}):
            raise ValueError("Family overlap in training cross-validation.")
    release["majority_reference"] = {
        "run_json_sha256": sha_file(majority_run / "run.json"),
        "splits_sha256": sha_file(majority_run / "splits.csv"),
        "results_sha256": sha_file(majority_run / "results.csv"),
    }
    results = [evaluate(name, rows, folds) for name in ("Majority", "TFIDF_LR")]
    output = save_run(destination, release, rows, folds, results)
    print(json.dumps({"output": str(output), "selected_C": results[1]["selected_C"],
                      "cv": results[1]["cv"], "metrics": results[1]["metrics"]}, indent=2))
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("majority_run", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--assume-labels-reviewed", action="store_true", required=True)
    args = parser.parse_args()
    run(args.package, args.majority_run, args.out, args.assume_labels_reviewed)
