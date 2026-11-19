# A-C model comparison

279 training cases from 2010–2020; the same 42 development cases from 2021–2022 for every model and text variant. Training labels: 181 affirmed / 98 reversed-vacated. Evaluation labels: 25 / 17. The majority classifier predicts label 0 throughout.

A retains team-reviewed status. B/C use explicit user-authorized provisional assumptions; source review statuses remain pending. The original combined logistic run and prepared dataset are preserved. No test texts, labels or model evaluations enter this run.

## Selection and transformations

The 3 saved training folds are reused exactly, preserving cross-batch families. Each learned model selects its own C on MASKED training-fold performance: mean balanced accuracy first, mean macro F1 next, then smaller C for a tie. Its selected C is fixed for separate FULL/MASKED fits.

| Model | C | Mean CV balanced accuracy | Mean CV macro F1 | Selected |
|---|---:|---:|---:|---|
| TFIDF_LR | 0.1 | 0.6231 | 0.6073 |  |
| TFIDF_LR | 1 | 0.5893 | 0.5893 |  |
| TFIDF_LR | 10 | 0.6272 | 0.6301 | yes |
| TFIDF_SVM | 0.1 | 0.5841 | 0.5846 |  |
| TFIDF_SVM | 1 | 0.6296 | 0.6318 |  |
| TFIDF_SVM | 10 | 0.6326 | 0.6360 | yes |
| LEGAL_BERT_LR | 0.1 | 0.6260 | 0.6131 | yes |
| LEGAL_BERT_LR | 1 | 0.6085 | 0.5995 |  |
| LEGAL_BERT_LR | 10 | 0.6143 | 0.6070 |  |

TF-IDF LR and linear SVM share word unigrams/bigrams, min_df=2, max_features=30000 and L2 TF-IDF normalization. Vocabulary, IDF and balanced class weights are fitted only within the relevant training fold. The final variants each fit a fresh pipeline on all training cases. No additional learned scaler is needed for TF-IDF. Seed: 20261023. Full parameters and effective class weights are saved in `run.json`.

Frozen encoder: `nlpaueb/legal-bert-base-uncased`, revision `15b570cbf88259610b082a167dacc190124f60f6`. Each chunk contains at most 510 content tokens plus CLS/SEP; no overlap or truncation. Mean pooling excludes specials and padding, and opinion pooling weights chunks by content-token count. Every chunk contributes. The encoder runs in evaluation/inference mode with gradients disabled and is never fine-tuned. StandardScaler and balanced L2 logistic regression stay inside the training-fold pipeline. Cache keys include exact text, pinned settings, encoder code and software versions; cache-only reload was checked.

## Shared development results

| Model | Variant | C | Accuracy | Balanced accuracy | Macro F1 | Recall 0 | Recall 1 |
|---|---|---:|---:|---:|---:|---:|---:|
| Majority | FULL | — | 0.5952 | 0.5000 | 0.3731 | 1.0000 | 0.0000 |
| Majority | MASKED | — | 0.5952 | 0.5000 | 0.3731 | 1.0000 | 0.0000 |
| TFIDF_LR | FULL | 10 | 0.8095 | 0.8212 | 0.8078 | 0.7600 | 0.8824 |
| TFIDF_LR | MASKED | 10 | 0.5714 | 0.5365 | 0.5333 | 0.7200 | 0.3529 |
| TFIDF_SVM | FULL | 10 | 0.8810 | 0.8812 | 0.8776 | 0.8800 | 0.8824 |
| TFIDF_SVM | MASKED | 10 | 0.5476 | 0.5071 | 0.4997 | 0.7200 | 0.2941 |
| LEGAL_BERT_LR | FULL | 0.1 | 0.8810 | 0.8812 | 0.8776 | 0.8800 | 0.8824 |
| LEGAL_BERT_LR | MASKED | 0.1 | 0.4762 | 0.5035 | 0.4750 | 0.3600 | 0.6471 |

[REPORTING.md](REPORTING.md) provides raw and row-normalized confusion matrices (true rows, predicted columns; labels 0, 1), per-class recall, and split/fold counts. `predictions.csv` preserves every prediction, including failures; `splits.csv` records the identical evaluation IDs and family-grouped CV assignments. `batch_class_counts.csv` preserves split counts by source batch.

## Reproduction and limitations

The FULL/MASKED comparison uses fixed selected settings but separately fitted pipelines; it is not a same-model phrase-deletion experiment. The small development set, previous A/B development inspection, different upstream masking pipelines, pending B/C human review and unresolved family-companion warnings limit interpretation. No labels or masks were changed to improve results.

Install this run’s `requirements-lock.txt` using the Python version in `run.json`. From `experiments/provisional_abc`, use a fresh output directory:

```sh
HF_HUB_OFFLINE=1 python run_comparison.py inputs/abc_provisional_v1/release.json runs/abc_svm_provisional_v1 runs/abc_complete_reproduction
```

For the encoder stage, the checkpoint must already be installed in the shared B cache; `../provisional_b/download_encoder.py` downloads the pinned revision when needed. The completed B checkpoint checksums are verified before use. Full runs save both portable embedding matrices and their row index. No encoder access is needed to inspect or verify the saved results. `run.json`, `selection.json`, `verification.json` and implementation hashes document the run.
