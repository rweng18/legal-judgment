# Combined A-C majority and logistic-regression results

Training: 279 cases (0: 181, 1: 98). Evaluation: the same 42 development cases for every condition. The training-majority classifier always predicts 0.

A retains its team-reviewed source status. B and C labels are used under explicit user-authorized provisional assumptions; their pending-human-review statuses are preserved. No reserved test cases are evaluated.

## MASKED training selection

3 family-grouped folds within 2010–2020; batch-spanning families stay together. Select by mean balanced accuracy, then mean macro F1, then smaller C. Selected **C = 10** is held fixed for the FULL/MASKED comparison.

| C | Mean balanced accuracy | Mean macro F1 |
|---:|---:|---:|
| 0.1 | 0.6231 | 0.6073 |
| 1 | 0.5893 | 0.5893 |
| 10 | 0.6272 | 0.6301 |

## Development results

| Model | Variant | Accuracy | Balanced accuracy | Macro F1 | Recall 0 | Recall 1 |
|---|---|---:|---:|---:|---:|---:|
| Majority | FULL | 0.5952 | 0.5000 | 0.3731 | 1.0000 | 0.0000 |
| Majority | MASKED | 0.5952 | 0.5000 | 0.3731 | 1.0000 | 0.0000 |
| TFIDF_LR | FULL | 0.8095 | 0.8212 | 0.8078 | 0.7600 | 0.8824 |
| TFIDF_LR | MASKED | 0.5714 | 0.5365 | 0.5333 | 0.7200 | 0.3529 |

TF-IDF uses word unigrams/bigrams, min_df=2, max_features=30000 and L2 vector normalization. Logistic regression uses L2 regularization, balanced training-class weights, liblinear, max_iter=10000 and seed 20261023. Each fold and each final text variant gets a fresh fitted pipeline. Vocabulary, IDF and class weights are learned from that fit subset only. No independent learned scaler is used for sparse TF-IDF.

[Detailed reporting tables](REPORTING.md) include counts for each split and fold, raw and row-normalized confusion matrices, true rows and predicted columns ordered 0, 1. `batch_class_counts.csv` adds batch-specific split counts. `predictions.csv` retains all predictions and signed decision scores (not calibrated probabilities). `splits.csv` retains family IDs and CV membership; `selection.json` retains all candidate fold metrics.

## Limits and reproduction

These are development estimates on 42 decisions, not final-test results. A/B validation cases have been inspected previously. A and B/C use different upstream masking implementations. Two unresolved companion warnings and provisional family links remain. No labels, masks, source texts or earlier results were changed for this run.

From `experiments/provisional_abc`, use the recorded Python version, install `requirements-lock.txt` from this run in a virtual environment, and run:

```sh
python run_logistic.py inputs/abc_provisional_v1/release.json runs/abc_logistic_reproduction
```

Use a fresh output directory. `run.json` records the prepared release, exact source and implementation hashes, parameters, seed and software versions. `verification.json` records the run checks. The comparison is computed without loading an encoder or test texts.
