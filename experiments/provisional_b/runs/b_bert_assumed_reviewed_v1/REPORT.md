# Batch B · Frozen LEGAL-BERT and combined model results

The [reporting supplement](REPORTING.md) adds explicit split/fold class counts and raw plus row-normalized confusion matrices for every condition. The [updated executed notebook](Batch_B_reporting_results.ipynb) verifies these outputs against the saved predictions. Original predictions and model-run metadata are unchanged.

This run uses the user's assumption that the supplied Batch B labels have been reviewed. The source label field is `draft_label_if_unanimous_include`; its stored adjudication status is `pending_human_review`. Family assignments retain their provisional status. The assumption, source statuses and input hashes are preserved in `run.json`.

All models use 97 training cases from 2010–2020 and the identical 15 development cases from 2021–2022. Training contains 64 affirmed and 33 reversed/vacated cases. Development contains 12 affirmed and 3 reversed/vacated cases.

## Frozen representation and model selection

The encoder is `nlpaueb/legal-bert-base-uncased`, pinned to revision `15b570cbf88259610b082a167dacc190124f60f6`. The slow BertTokenizer processes each complete FULL and MASKED text independently. Every contiguous chunk contains up to 510 content tokens, followed by per-chunk CLS/SEP insertion. All chunks, including short final chunks, contribute to the opinion vector.

The encoder runs on CPU in evaluation mode with gradients disabled. Pooling averages final-hidden-layer content-token vectors across the entire opinion, excluding special tokens and padding. This weights each chunk by its content-token count. One 768-dimensional float32 vector is saved per opinion per variant. Across the 112 development opinions, FULL uses 216 chunks and MASKED uses 204. The measured word, token and chunk counts match the supplied pinned-tokenizer report for every case.

Logistic regression uses training-only StandardScaler transformations, balanced training-class weights and L2 regularization. C is selected using MASKED vectors and the same three family-grouped training folds used by the lexical models. Fold holdout class counts are 22/11, 21/11 and 21/11 (affirmed/reversed-vacated). Selection maximizes mean balanced accuracy, then macro F1, then prefers smaller C.

| Encoder LR C | Mean fold balanced accuracy | Mean fold macro F1 |
|---|---:|---:|
| **0.1** | **0.5541** | **0.5309** |
| 1 | 0.5393 | 0.5190 |
| 10 | 0.5242 | 0.5082 |

The encoder classifier selects C = 0.1. Separate FULL and MASKED scaler/classifier pipelines are then fitted on all training cases at that C. The encoder weights remain frozen throughout.

## Results on the shared development cases

| Model | Text | C | Accuracy | Balanced accuracy | Macro F1 | Affirmed recall | Reversed/vacated recall |
|---|---|---:|---:|---:|---:|---:|---:|
| Majority | FULL and MASKED | — | 0.8000 | 0.5000 | 0.4444 | 1.0000 | 0.0000 |
| TF-IDF + LR | FULL | 10 | 0.8000 | 0.6250 | 0.6400 | 0.9167 | 0.3333 |
| TF-IDF + LR | MASKED | 10 | 0.8000 | 0.5000 | 0.4444 | 1.0000 | 0.0000 |
| TF-IDF + SVM | FULL | 1 | 0.8000 | 0.6250 | 0.6400 | 0.9167 | 0.3333 |
| TF-IDF + SVM | MASKED | 1 | 0.7333 | 0.4583 | 0.4231 | 0.9167 | 0.0000 |
| Frozen LEGAL-BERT + LR | FULL | 0.1 | 0.7333 | 0.7083 | 0.6591 | 0.7500 | 0.6667 |
| Frozen LEGAL-BERT + LR | MASKED | 0.1 | 0.6667 | 0.6667 | 0.6032 | 0.6667 | 0.6667 |

Confusion matrices use true rows and predicted columns in the fixed order [affirmed, reversed/vacated]. LEGAL-BERT FULL produces `[[9, 3], [1, 2]]`; MASKED produces `[[8, 4], [1, 2]]`.

Each encoder variant identifies two of the three reversed/vacated outcomes. FULL correctly identifies 9 of 12 affirmed outcomes, while MASKED identifies 8. This yields higher balanced accuracy than the lexical models on this sample, alongside lower ordinary accuracy because more affirmed cases are misclassified. The FULL-minus-MASKED balanced-accuracy difference is 4.17 percentage points.

The comparison has only 15 development cases and three reversed/vacated outcomes. One reversal changes balanced accuracy by 16.67 percentage points. Interpret these scores with the small sample, the stated label-review assumption and provisional family assignments in view.

## Saved artifacts

- `Batch_B_results.ipynb` is an executed notebook with tables, figures and independent checks of predictions and embedding files.
- `results.csv`, `predictions.csv`, `confusion_matrices.json` and `confusion_matrices.png` cover all four models and both text variants. The 120 prediction rows represent 15 shared cases across eight conditions.
- `selection.json` records each candidate C and its MASKED training-fold metrics. `splits.csv` records case IDs, labels, dates, batches, families, periods and fold membership.
- `run.json` records data/split versions, review assumptions, input and source-code hashes, model parameters, seed 20261023, software versions and encoder revision.
- `embeddings_FULL.npy` and `embeddings_MASKED.npy` contain the reusable opinion vectors. `embedding_index.json` records their row-to-case mapping, text hashes, protocol and file checksums.
- `case_lengths.csv` and `length_summary.json` document complete word/token/chunk coverage.
- `verification.json` records checkpoint-file checksums, tokenizer properties, reproduction checks and timings. `requirements-lock.txt` captures the full installed environment.

The checkpoint and per-opinion vector caches are stored under `experiments/provisional_b/.cache/`. The portable run package includes both embedding matrices so the classifier stage can also be reproduced directly from those saved vectors.

## Reproduction

The combined run uses Python 3.11.16, NumPy 2.3.4, scikit-learn 1.7.2, Transformers 4.57.1 and PyTorch 2.9.1. From `experiments/provisional_b`, activate a Python 3.11 environment and run the following with a fresh output directory.

```sh
python -m pip install -r runs/b_bert_assumed_reviewed_v1/requirements-lock.txt
python download_encoder.py
HF_HUB_OFFLINE=1 python run_bert.py ../../annotation/submissions/hyunsang/preprocessing/batch_b/provisional_v1 runs/b_svm_assumed_reviewed_v1 runs/b_bert_assumed_reviewed_v2 --assume-labels-reviewed
python results_notebook.py runs/b_bert_assumed_reviewed_v2
```

The runner checks the input files and saved folds against the preceding SVM run, reproduces the lexical conditions, extracts or reuses frozen vectors, selects the encoder classifier's C and saves a complete package. To rerun the opened notebook, select the Python kernel for the installed environment.

The earlier lexical runs used Python 3.9.12 and scikit-learn 1.6.1. Their selected settings, CV metrics and predicted labels reproduced in the pinned environment. Decision scores differed by at most 3.7 × 10⁻¹⁵. All six protocol checks passed. The executed notebook independently verified all eight conditions on the same evaluation IDs, recomputed their metrics and checked embedding shapes and checksums.
