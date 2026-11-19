# Reporting rules and verified results

Labels: **0 = affirmed; 1 = reversed/vacated**. All conditions use identical development cases.

Accuracy is the overall correct fraction, shown alongside the training-majority baseline. Balanced accuracy is the mean recall across labels 0 and 1 and the primary selection metric. Macro F1 averages the two label F1 scores and breaks selection ties. Per-class recall appears below. Scores are fractions.

## Class counts

Counts cover the cases included in this run. CV training and held-out counts refer only to the training period; folds reuse cases and must not be summed as independent samples.

| Split/role | Fold | Total | Label 0 | Label 1 |
|---|---:|---:|---:|---:|
| train |  | 279 | 181 | 98 |
| validation |  | 42 | 25 | 17 |
| cv_training | 1 | 185 | 120 | 65 |
| cv_held_out | 1 | 94 | 61 | 33 |
| cv_training | 2 | 186 | 121 | 65 |
| cv_held_out | 2 | 93 | 60 | 33 |
| cv_training | 3 | 187 | 121 | 66 |
| cv_held_out | 3 | 92 | 60 | 32 |

## Evaluation metrics

| Model | Variant | Accuracy | Balanced accuracy | Macro F1 | Recall 0 | Recall 1 |
|---|---|---:|---:|---:|---:|---:|
| Majority | FULL | 0.5952 | 0.5000 | 0.3731 | 1.0000 | 0.0000 |
| Majority | MASKED | 0.5952 | 0.5000 | 0.3731 | 1.0000 | 0.0000 |
| TFIDF_LR | FULL | 0.8095 | 0.8212 | 0.8078 | 0.7600 | 0.8824 |
| TFIDF_LR | MASKED | 0.5714 | 0.5365 | 0.5333 | 0.7200 | 0.3529 |
| TFIDF_SVM | FULL | 0.8810 | 0.8812 | 0.8776 | 0.8800 | 0.8824 |
| TFIDF_SVM | MASKED | 0.5476 | 0.5071 | 0.4997 | 0.7200 | 0.2941 |
| LEGAL_BERT_LR | FULL | 0.8810 | 0.8812 | 0.8776 | 0.8800 | 0.8824 |
| LEGAL_BERT_LR | MASKED | 0.4762 | 0.5035 | 0.4750 | 0.3600 | 0.6471 |

## Confusion matrices

True labels are rows; predictions are columns. Both axes use order **0, 1**. Each cell shows **raw count (row-normalized fraction)**. Exact numeric arrays are saved in `reporting_summary.json`.

### Majority · FULL

| True / predicted | 0 | 1 |
|---|---:|---:|
| 0 | 25 (1.0000) | 0 (0.0000) |
| 1 | 17 (1.0000) | 0 (0.0000) |

### Majority · MASKED

| True / predicted | 0 | 1 |
|---|---:|---:|
| 0 | 25 (1.0000) | 0 (0.0000) |
| 1 | 17 (1.0000) | 0 (0.0000) |

### TFIDF_LR · FULL

| True / predicted | 0 | 1 |
|---|---:|---:|
| 0 | 19 (0.7600) | 6 (0.2400) |
| 1 | 2 (0.1176) | 15 (0.8824) |

### TFIDF_LR · MASKED

| True / predicted | 0 | 1 |
|---|---:|---:|
| 0 | 18 (0.7200) | 7 (0.2800) |
| 1 | 11 (0.6471) | 6 (0.3529) |

### TFIDF_SVM · FULL

| True / predicted | 0 | 1 |
|---|---:|---:|
| 0 | 22 (0.8800) | 3 (0.1200) |
| 1 | 2 (0.1176) | 15 (0.8824) |

### TFIDF_SVM · MASKED

| True / predicted | 0 | 1 |
|---|---:|---:|
| 0 | 18 (0.7200) | 7 (0.2800) |
| 1 | 12 (0.7059) | 5 (0.2941) |

### LEGAL_BERT_LR · FULL

| True / predicted | 0 | 1 |
|---|---:|---:|
| 0 | 22 (0.8800) | 3 (0.1200) |
| 1 | 2 (0.1176) | 15 (0.8824) |

### LEGAL_BERT_LR · MASKED

| True / predicted | 0 | 1 |
|---|---:|---:|
| 0 | 9 (0.3600) | 16 (0.6400) |
| 1 | 6 (0.3529) | 11 (0.6471) |

Derived from the original saved predictions and splits without retraining. Original data-review assumptions, split versions and run metadata remain in `run.json`. Source and reporting-code checksums are recorded in `reporting_summary.json`.
