"""Verify and report saved predictions without retraining or changing run provenance."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np

from data import sha_file
from modeling import scores
from outputs import write_csv, write_json


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def class_counts(splits):
    def count(scope, fold, subset):
        counts = Counter(int(row["label"]) for row in subset)
        return {"scope": scope, "fold": fold, "n": len(subset),
                "label_0": counts[0], "label_1": counts[1]}

    rows = [count(period, "", [r for r in splits if r["period"] == period])
            for period in dict.fromkeys(r["period"] for r in splits)]
    training = [r for r in splits if r["period"] == "train"]
    folds = sorted({int(r["held_out_cv_fold"]) for r in training if r["held_out_cv_fold"]})
    if folds and any(not r["held_out_cv_fold"] for r in training):
        raise ValueError("Training fold membership is incomplete.")
    for fold in folds:
        for role, held_out in (("cv_training", False), ("cv_held_out", True)):
            subset = [r for r in training if (int(r["held_out_cv_fold"]) == fold) == held_out]
            rows.append(count(role, fold, subset))
    return rows


def report(run):
    run = Path(run)
    splits = read_csv(run / "splits.csv")
    predictions = read_csv(run / "predictions.csv")
    results = read_csv(run / "results.csv")
    expected = {r["case_id"]: int(r["label"]) for r in splits if r["period"] == "validation"}
    if set(expected.values()) != {0, 1}:
        raise ValueError("Both labels must occur in this development evaluation.")
    conditions = []
    stored = json.loads((run / "confusion_matrices.json").read_text())
    if stored["class_order"] != [0, 1] or stored["axes"] != ["true", "predicted"]:
        raise ValueError("Unexpected confusion-matrix class order or axes.")
    for result in results:
        selected = [p for p in predictions
                    if (p["model"], p["variant"]) == (result["model"], result["variant"])]
        if len(selected) != len(expected) or {p["case_id"]: int(p["label"]) for p in selected} != expected:
            raise ValueError("Evaluation cases or labels differ across conditions.")
        measured = scores([int(p["label"]) for p in selected], [int(p["prediction"]) for p in selected])
        for key in ("accuracy", "balanced_accuracy", "macro_f1", "recall_0", "recall_1"):
            if not np.isclose(float(result[key]), measured[key], rtol=0, atol=1e-12):
                raise ValueError(f"Saved {key} differs from predictions.")
        matrix = np.asarray(measured.pop("confusion_matrix"))
        original = next(c for c in stored["conditions"]
                        if (c["model"], c["variant"]) == (result["model"], result["variant"]))
        if matrix.tolist() != original["counts"]:
            raise ValueError("Saved confusion matrix differs from predictions.")
        normalized = matrix / matrix.sum(axis=1, keepdims=True)
        assert np.isclose(measured["balanced_accuracy"], np.diag(normalized).mean())
        conditions.append({"model": result["model"], "variant": result["variant"],
                           **measured, "counts": matrix.tolist(), "row_normalized": normalized.tolist()})
    for variant in {r["variant"] for r in conditions}:
        if not any(r["model"] == "Majority" and r["variant"] == variant for r in conditions):
            raise ValueError("Every variant must include the majority comparison.")
    counts = class_counts(splits)
    write_csv(run / "class_counts.csv", counts)
    source_names = ("run.json", "splits.csv", "predictions.csv", "results.csv", "confusion_matrices.json")
    write_json(run / "reporting_summary.json", {
        "class_order": [0, 1], "axes": ["true", "predicted"],
        "normalization": "Each true-label row divided by its case count; values in [0, 1].",
        "selection_metric": "balanced_accuracy", "selection_tie_breaker": "macro_f1",
        "class_counts": counts, "conditions": conditions,
        "source_sha256": {name: sha_file(run / name) for name in source_names},
        "reporting_code_sha256": {name: sha_file(Path(__file__).parent / name)
                                  for name in ("reporting.py", "modeling.py", "outputs.py", "data.py")},
        "provenance": "Derived from saved predictions and splits; original run metadata is unchanged.",
    })
    lines = ["# Reporting rules and verified results", "",
             "Labels: **0 = affirmed; 1 = reversed/vacated**. All conditions use identical development cases.", "",
             "Accuracy is the overall correct fraction, shown alongside the training-majority baseline. "
             "Balanced accuracy is the mean recall across labels 0 and 1 and the primary selection metric. "
             "Macro F1 averages the two label F1 scores and breaks selection ties. "
             "Per-class recall appears below. Scores are fractions.", "",
             "## Class counts", "",
             "Counts cover the cases included in this run. CV training and held-out counts refer only to "
             "the training period; folds reuse cases and must not be summed as independent samples.", "",
             "| Split/role | Fold | Total | Label 0 | Label 1 |", "|---|---:|---:|---:|---:|"]
    lines += [f"| {r['scope']} | {r['fold']} | {r['n']} | {r['label_0']} | {r['label_1']} |" for r in counts]
    lines += ["", "## Evaluation metrics", "",
              "| Model | Variant | Accuracy | Balanced accuracy | Macro F1 | Recall 0 | Recall 1 |",
              "|---|---|---:|---:|---:|---:|---:|"]
    for r in conditions:
        values = " | ".join(f"{r[k]:.4f}" for k in ("accuracy", "balanced_accuracy", "macro_f1", "recall_0", "recall_1"))
        lines.append(f"| {r['model']} | {r['variant']} | {values} |")
    lines += ["", "## Confusion matrices", "",
              "True labels are rows; predictions are columns. Both axes use order **0, 1**. "
              "Each cell shows **raw count (row-normalized fraction)**. "
              "Exact numeric arrays are saved in `reporting_summary.json`.", ""]
    for r in conditions:
        lines += [f"### {r['model']} · {r['variant']}", "",
                  "| True / predicted | 0 | 1 |", "|---|---:|---:|"]
        for i in (0, 1):
            cells = " | ".join(f"{r['counts'][i][j]} ({r['row_normalized'][i][j]:.4f})" for j in (0, 1))
            lines.append(f"| {i} | {cells} |")
        lines.append("")
    lines += ["Derived from the original saved predictions and splits without retraining. "
              "Original data-review assumptions, split versions and run metadata remain in `run.json`. "
              "Source and reporting-code checksums are recorded in `reporting_summary.json`.", ""]
    (run / "REPORTING.md").write_text("\n".join(lines), encoding="utf-8")
    return run / "REPORTING.md"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", type=Path, nargs="+")
    for path in parser.parse_args().runs:
        print(report(path))
