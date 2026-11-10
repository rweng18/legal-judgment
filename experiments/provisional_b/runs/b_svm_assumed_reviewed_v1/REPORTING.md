# Reporting rules and verified results

Labels: **0 = affirmed; 1 = reversed/vacated**. All conditions use identical development cases.

Accuracy is the overall correct fraction, shown alongside the training-majority baseline. Balanced accuracy is the mean recall across labels 0 and 1 and the primary selection metric. Macro F1 averages the two label F1 scores and breaks selection ties. Per-class recall appears below. Scores are fractions.

## Class counts

Counts cover the cases included in this run. CV training and held-out counts refer only to the training period; folds reuse cases and must not be summed as independent samples.

| Split/role | Fold | Total | Label 0 | Label 1 |
|---|---:|---:|---:|---:|
| train |  | 97 | 64 | 33 |
| validation |  | 15 | 12 | 3 |
| cv_training | 1 | 64 | 42 | 22 |
| cv_held_out | 1 | 33 | 22 | 11 |
| cv_training | 2 | 65 | 43 | 22 |
| cv_held_out | 2 | 32 | 21 | 11 |
| cv_training | 3 | 65 | 43 | 22 |
| cv_held_out | 3 | 32 | 21 | 11 |

## Evaluation metrics

| Model | Variant | Accuracy | Balanced accuracy | Macro F1 | Recall 0 | Recall 1 |
|---|---|---:|---:|---:|---:|---:|
| Majority | FULL | 0.8000 | 0.5000 | 0.4444 | 1.0000 | 0.0000 |
| Majority | MASKED | 0.8000 | 0.5000 | 0.4444 | 1.0000 | 0.0000 |
| TFIDF_LR | FULL | 0.8000 | 0.6250 | 0.6400 | 0.9167 | 0.3333 |
| TFIDF_LR | MASKED | 0.8000 | 0.5000 | 0.4444 | 1.0000 | 0.0000 |
| TFIDF_SVM | FULL | 0.8000 | 0.6250 | 0.6400 | 0.9167 | 0.3333 |
| TFIDF_SVM | MASKED | 0.7333 | 0.4583 | 0.4231 | 0.9167 | 0.0000 |

## Confusion matrices

True labels are rows; predictions are columns. Both axes use order **0, 1**. Each cell shows **raw count (row-normalized fraction)**. Exact numeric arrays are saved in `reporting_summary.json`.

### Majority · FULL

| True / predicted | 0 | 1 |
|---|---:|---:|
| 0 | 12 (1.0000) | 0 (0.0000) |
| 1 | 3 (1.0000) | 0 (0.0000) |

### Majority · MASKED

| True / predicted | 0 | 1 |
|---|---:|---:|
| 0 | 12 (1.0000) | 0 (0.0000) |
| 1 | 3 (1.0000) | 0 (0.0000) |

### TFIDF_LR · FULL

| True / predicted | 0 | 1 |
|---|---:|---:|
| 0 | 11 (0.9167) | 1 (0.0833) |
| 1 | 2 (0.6667) | 1 (0.3333) |

### TFIDF_LR · MASKED

| True / predicted | 0 | 1 |
|---|---:|---:|
| 0 | 12 (1.0000) | 0 (0.0000) |
| 1 | 3 (1.0000) | 0 (0.0000) |

### TFIDF_SVM · FULL

| True / predicted | 0 | 1 |
|---|---:|---:|
| 0 | 11 (0.9167) | 1 (0.0833) |
| 1 | 2 (0.6667) | 1 (0.3333) |

### TFIDF_SVM · MASKED

| True / predicted | 0 | 1 |
|---|---:|---:|
| 0 | 11 (0.9167) | 1 (0.0833) |
| 1 | 3 (1.0000) | 0 (0.0000) |

Derived from the original saved predictions and splits without retraining. Original data-review assumptions, split versions and run metadata remain in `run.json`. Source and reporting-code checksums are recorded in `reporting_summary.json`.
