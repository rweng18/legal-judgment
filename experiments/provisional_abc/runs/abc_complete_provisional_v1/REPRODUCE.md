# A-C run handoff

This directory contains the complete eight-condition comparison: four models × FULL/MASKED, on the same 42 development cases. All 336 per-case predictions are preserved, including failures. Training uses 279 cases from 2010–2020; evaluation uses 2021–2022. No reserved 2023–2024 test cases were evaluated.

## Required reporting files

| Output | File |
|---|---|
| Accuracy, balanced accuracy, macro F1, per-class recall, C and evaluation size | [results.csv](results.csv) |
| Per-case labels, predictions, signed decision scores, batch and family IDs | [predictions.csv](predictions.csv) |
| Case-level split and held-out CV fold membership | [splits.csv](splits.csv) |
| Class counts for each split and each fold's training/held-out portions | [class_counts.csv](class_counts.csv) |
| Class counts by batch and split | [batch_class_counts.csv](batch_class_counts.csv) |
| Raw confusion-matrix counts | [confusion_matrices.json](confusion_matrices.json) |
| Exact row-normalized matrices and verified metrics | [reporting_summary.json](reporting_summary.json) |
| Raw counts and row percentages in a figure | [confusion_matrices.png](confusion_matrices.png) |
| Readable tables and matrices | [REPORTING.md](REPORTING.md) |
| Parameters, seed, data/split versions, software versions, encoder revision and source hashes | [run.json](run.json) |
| All C candidates and MASKED training-fold scores | [selection.json](selection.json) |
| Exact installed packages | [requirements-lock.txt](requirements-lock.txt) |
| Cached opinion vectors and their case/text index | `embeddings_FULL.npy`, `embeddings_MASKED.npy`, [embedding_index.json](embedding_index.json) |
| Executed results and independent checks | [A_C_complete_results.ipynb](A_C_complete_results.ipynb) |
| Checksums of this reporting package | [artifact_checksums.json](artifact_checksums.json) |

All matrices have **true rows and predicted columns**, both ordered **[0, 1]**: 0 affirmed; 1 reversed/vacated. Row-normalized entries divide each cell by its true-label row total. Accuracy is the overall correct fraction; balanced accuracy is mean recall across the two labels; macro F1 is mean F1 across both labels.

Training counts are 181 / 98 for labels 0 / 1. Development counts are 25 / 17. Seed: **20261023**. Selected C values: LR **10**, SVM **10**, encoder LR **0.1**. Each setting was selected only on MASKED training folds and held fixed across the two final text variants.

## Reproduce from the repository

Use the repository containing this workspace, its prepared `inputs/abc_provisional_v1` release, the saved SVM reference run, and the shared `experiments/provisional_b` implementation. Preserve the relative directory structure. The recorded runtime is Python 3.11.16; exact library versions are in `requirements-lock.txt`. From `experiments/provisional_abc`:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r runs/abc_complete_provisional_v1/requirements-lock.txt
.venv/bin/python ../provisional_b/download_encoder.py
HF_HUB_OFFLINE=1 .venv/bin/python run_comparison.py inputs/abc_provisional_v1/release.json runs/abc_svm_provisional_v1 runs/abc_complete_reproduction
.venv/bin/python comparison_notebook.py runs/abc_complete_reproduction
```

The download step needs network access only if the pinned checkpoint is absent. The reproduction runner checks the reference dataset and folds, reproduces earlier lexical predictions, and caches encoder vectors. It rejects existing output directories. If reproducing the SVM stage too, run `run_comparison.py` with `--lexical-only`, using `runs/abc_logistic_provisional_v1` as the reference, then use that new SVM run as the full comparison's reference.

Encoder: `nlpaueb/legal-bert-base-uncased`, revision `15b570cbf88259610b082a167dacc190124f60f6`. It stays frozen and processes all non-overlapping 510-content-token chunks, excluding specials/padding from pooling and weighting chunks by content-token count. The saved matrices permit inspection without downloading the checkpoint. The notebook reads saved artifacts rather than retraining; select the installed environment's kernel when opening it interactively.

The source hashes in `run.json` identify the actual experiment implementation; its Git commit is the base commit at execution time. The A-C workspace was not yet committed when the run was created, so that base commit alone is insufficient to reconstruct it: retain this workspace and verify the recorded implementation hashes.

A retains its team-reviewed status. B/C use the explicit provisional assumptions recorded in `run.json` and the dataset release. Their original pending-review statuses, cross-batch family links, companion warnings and batch-specific masking remain documented. These are development estimates, not a final human-gold or untouched-test evaluation. Do not replace failed predictions or relabel cases when reproducing.
