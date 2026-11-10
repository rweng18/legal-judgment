# Batch B linear SVM and combined lexical comparison

Run under the user's assumption that the supplied Batch B labels have been reviewed. The source label field is `draft_label_if_unanimous_include`, whose recorded adjudication status is `pending_human_review`. The supplied family assignments remain provisional. These statuses and the user's assumption are retained in `run.json`.

The experiment uses the same 97 training cases and 15 validation cases as the saved majority and logistic-regression runs. Training contains 64 affirmed and 33 reversed/vacated cases. Validation contains 12 affirmed and 3 reversed/vacated cases. Input hashes, case IDs, dates, labels and family assignments were checked against the logistic-regression run before fitting.

## Training and model selection

The SVM uses `LinearSVC` with balanced class weights, L2 regularization, squared-hinge loss and seed 20261023. Its TF-IDF pipeline uses word unigrams/bigrams, `min_df=2`, at most 30,000 features and L2 document-vector normalization. Vocabulary, IDF and class weights are fitted within each training fold. TF-IDF normalization is the normalization step for both lexical models.

The run loads the three saved family-grouped folds directly from the logistic-regression run. Their holdout class counts are 22/11, 21/11 and 21/11 (affirmed/reversed-vacated). Both classes are present in each fit and holdout portion, and families are disjoint between them.

All C selection uses MASKED training text within 2010–2020. Selection maximizes mean balanced accuracy, then mean macro F1, then prefers smaller C. The SVM scores are shown below.

| C | Mean fold balanced accuracy | Mean fold macro F1 |
|---|---:|---:|
| 0.1 | 0.5714 | 0.5668 |
| **1** | **0.5945** | **0.5896** |
| 10 | 0.5801 | 0.5791 |

SVM selects C = 1. Logistic regression independently reproduces its earlier C = 10 selection. Each model's selected C is held fixed while separate FULL and MASKED pipelines are refitted on all training cases. Evaluation uses the identical 15 development cases from 2021–2022.

## Combined evaluation

| Model | Text | C | Accuracy | Balanced accuracy | Macro F1 | Affirmed recall | Reversed/vacated recall |
|---|---|---:|---:|---:|---:|---:|---:|
| Majority | FULL and MASKED | — | 0.8000 | 0.5000 | 0.4444 | 1.0000 | 0.0000 |
| TF-IDF + LR | FULL | 10 | 0.8000 | 0.6250 | 0.6400 | 0.9167 | 0.3333 |
| TF-IDF + LR | MASKED | 10 | 0.8000 | 0.5000 | 0.4444 | 1.0000 | 0.0000 |
| TF-IDF + SVM | FULL | 1 | 0.8000 | 0.6250 | 0.6400 | 0.9167 | 0.3333 |
| TF-IDF + SVM | MASKED | 1 | 0.7333 | 0.4583 | 0.4231 | 0.9167 | 0.0000 |

With true rows and predicted columns ordered [affirmed, reversed/vacated], SVM FULL has confusion matrix `[[11, 1], [2, 1]]` and SVM MASKED has `[[11, 1], [3, 0]]`.

SVM FULL correctly identifies one of the three reversed/vacated cases and misclassifies one affirmed case. MASKED misses all three reversed/vacated cases and misclassifies one affirmed case. Its balanced accuracy is 4.17 percentage points below majority and 16.67 points below SVM FULL. The small evaluation set, with only three reversed/vacated cases, limits how precisely these differences characterize performance.

## Reproduce

From the repository root, run the following in the project environment with a fresh output directory.

```sh
python experiments/provisional_b/run_svm.py annotation/submissions/hyunsang/preprocessing/batch_b/provisional_v1 experiments/provisional_b/runs/b_logistic_assumed_reviewed_v1 experiments/provisional_b/runs/b_svm_assumed_reviewed_v2 --assume-labels-reviewed
```

The actual runtime uses Python 3.9.12 and scikit-learn 1.6.1. The reference requirements specify scikit-learn 1.7.2. Full runtime versions are recorded in `run.json` so reproductions can account for that difference.

`selection.json` records all training-fold scores and selected settings. `splits.csv` preserves the saved fold assignments. `predictions.csv`, `results.csv` and the confusion-matrix JSON/figure include all three models and both text variants. `run.json` records source hashes, reference-run hashes, class counts, parameters, seed, software and the review assumption.

The run reproduced majority and logistic-regression predictions exactly, including logistic-regression decision scores and CV selection. Saved folds and split files match the earlier run. Independent metric recomputation confirmed all six model/variant conditions on the same 15 case IDs and labels. All fits completed without convergence warnings.
