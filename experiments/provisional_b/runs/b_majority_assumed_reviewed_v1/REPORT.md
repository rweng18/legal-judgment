# Batch B training-majority baseline

Run on November 9, 2026 under the user's instruction to assume the supplied labels have been reviewed. The label source is `draft_label_if_unanimous_include` in the supplied three-reviewer audit. Its source adjudication status is `pending_human_review`; the run records the user's assumption explicitly in `run.json`.

The training set contains 97 cases from 2010–2020, with 64 affirmed and 33 reversed/vacated. The learned majority is affirmed (0). Every evaluation case receives that prediction.

The 15 validation cases from 2021–2022 contain 12 affirmed and 3 reversed/vacated outcomes. FULL and MASKED use these identical case IDs and yield identical predictions.

| Variant | Cases | Accuracy | Balanced accuracy | Macro F1 | Affirmed recall | Reversed/vacated recall |
|---|---:|---:|---:|---:|---:|---:|
| FULL | 15 | 0.8000 | 0.5000 | 0.4444 | 1.0000 | 0.0000 |
| MASKED | 15 | 0.8000 | 0.5000 | 0.4444 | 1.0000 | 0.0000 |

The confusion matrix uses true outcomes as rows and predictions as columns.

| True outcome | Predicted affirmed | Predicted reversed/vacated |
|---|---:|---:|
| Affirmed | 12 | 0 |
| Reversed/vacated | 3 | 0 |

The classifier matches all 12 affirmed outcomes and misses all three reversed/vacated outcomes. Its 80% accuracy reflects the evaluation class distribution. The balanced accuracy of 50% is the reference for the later model comparisons.

## Reproduce

From the repository root, use the project environment and a fresh output directory.

```sh
python experiments/provisional_b/run_majority.py annotation/submissions/hyunsang/preprocessing/batch_b/provisional_v1 experiments/provisional_b/runs/b_majority_assumed_reviewed_v2 --assume-labels-reviewed
```

The run uses the 112 development IDs in the supplied Batch B package. Family IDs retain the package's provisional assignments. `run.json` preserves source paths and hashes, the review assumption, family status, training class counts, software versions and code hashes. `splits.csv` preserves the exact train/validation membership and labels, and `predictions.csv` provides every evaluation prediction.

Later models must use the same validation IDs and label mapping for a direct comparison. If the dataset expands to B+C or changes after review, rerun this baseline alongside those models on the new shared case set.
