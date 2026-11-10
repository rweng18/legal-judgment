# Batch B TF-IDF logistic regression

Run on November 9, 2026 under the user's assumption that the supplied Batch B labels have been reviewed. The source field is `draft_label_if_unanimous_include`. Its stored adjudication status remains `pending_human_review`, and the supplied family assignments are provisional. These statuses and the assumption are recorded in `run.json`.

The experiment uses the same 97 training cases and 15 validation cases as the majority baseline. Input hashes, all IDs, labels, dates and family assignments were checked against that saved run before fitting. Training has 64 affirmed and 33 reversed/vacated cases. Validation has 12 affirmed and 3 reversed/vacated cases.

## Training and selection

TF-IDF uses word unigrams and bigrams, `min_df=2`, at most 30,000 features and L2 vector normalization. Logistic regression uses L2 regularization, balanced training-class weights, the liblinear solver and seed 20261023.

Three family-grouped folds were formed within the 2010–2020 training period. Holdout class counts were 22/11, 21/11 and 21/11 (affirmed/reversed-vacated). Each fold fitted vocabulary, IDF and the classifier from its training portion. All candidate settings were evaluated on MASKED training text.

| C | Mean fold balanced accuracy | Mean fold macro F1 |
|---|---:|---:|
| 0.1 | 0.5696 | 0.5486 |
| 1 | 0.5714 | 0.5668 |
| **10** | **0.5869** | **0.5816** |

C = 10 won on mean balanced accuracy. FULL and MASKED were then fitted separately on all 97 training cases with that same C. The development labels were used for evaluation after selection.

## Evaluation

| Model | Text | Accuracy | Balanced accuracy | Macro F1 | Affirmed recall | Reversed/vacated recall |
|---|---|---:|---:|---:|---:|---:|
| Majority | FULL and MASKED | 0.8000 | 0.5000 | 0.4444 | 1.0000 | 0.0000 |
| TF-IDF + LR | FULL | 0.8000 | 0.6250 | 0.6400 | 0.9167 | 0.3333 |
| TF-IDF + LR | MASKED | 0.8000 | 0.5000 | 0.4444 | 1.0000 | 0.0000 |

With class order [affirmed, reversed/vacated], true rows and predicted columns, the FULL confusion matrix is `[[11, 1], [2, 1]]`. MASKED and majority both produce `[[12, 0], [3, 0]]`.

FULL identifies one of the three reversed/vacated cases while misclassifying one affirmed case. MASKED predicts affirmed for every validation case. FULL therefore improves balanced accuracy by 12.5 percentage points over MASKED and majority while matching their overall accuracy. With only three reversed/vacated evaluation cases, one correct reversal changes that class's recall by 33.3 percentage points. This comparison describes the current Batch B sample and supplied masks.

## Reproduce and inspect

From the repository root, run the following in the project environment using a fresh output directory.

```sh
python experiments/provisional_b/run_logistic.py annotation/submissions/hyunsang/preprocessing/batch_b/provisional_v1 experiments/provisional_b/runs/b_majority_assumed_reviewed_v1 experiments/provisional_b/runs/b_logistic_assumed_reviewed_v2 --assume-labels-reviewed
```

The actual runtime used Python 3.9.12 and scikit-learn 1.6.1. The full software inventory is saved in `run.json`; the repository's reference requirements specify scikit-learn 1.7.2. Reproduction should account for this version difference.

`selection.json` records all nine fold evaluations and the selected C. `splits.csv` records each training case's holdout fold and the shared evaluation IDs. `predictions.csv` contains labels, predictions and decision scores. `results.csv` and the confusion-matrix JSON/figure contain the evaluation summary. `run.json` records input hashes, the majority reference, settings, seed, review assumption, source-code hashes and software versions.

Checks confirmed disjoint case families within each CV fold, identical evaluation IDs and labels across every condition, identical majority predictions to the earlier run, and independently recomputed evaluation metrics. The six synthetic protocol checks also passed.
