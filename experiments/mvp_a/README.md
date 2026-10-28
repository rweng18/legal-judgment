# Team 11 — reviewed-data MVP checkpoint

**October 25, 2026: team-reviewed data; preliminary validation results.** The team confirmed independent review of Becca's and Hayden's work today. The integrated manifest and notebook now say `team_reviewed`. Original submissions and the [earlier provisional trial](../provisional_a/README.md) remain historical records.

Start with the [executed notebook](Team_11_MVP.ipynb) or the [IEEE report source](../../reports/Team_11_MVP_IEEE/main.tex). The report is a complete LaTeX project: download its whole directory, including tables and `images/`, and compile `main.tex` with IEEEtran available. The built-in Codex LaTeX compiler successfully compiled it. No edits to the proposal are required.

## Checkpoint deliverables

| Requirement | Completed evidence |
|---|---|
| Working core system / MVP | Notebook executes preparation, training, predictions, evaluation, diagnostics and verification in 14 code cells |
| Data and evaluation pipeline | Immutable input hashes, 120-case selection manifest, chronological family-aware splits, text variants and review provenance |
| Baselines | Majority class, TF-IDF logistic regression and linear SVM |
| First experiments | FULL/MASKED comparisons for all three learned models; frozen LEGAL-BERT; five-seed matched random removal for LR; small C grid |
| Preliminary results | Accuracy, balanced accuracy, macro F1, class counts, per-class recall, raw/normalized confusion matrices, lengths and error review |

## Data integrated from GitHub

All 16 repository PRs available at the October 25 review were merged. Relevant preparation work is pinned to main commit `ecca2a41c96ad80f6d9f91a90bb894fa2ddad9b8`:

- [PR 12](https://github.com/rweng18/legal-judgment/pull/12): Becca's FULL cleaning.
- [PR 13](https://github.com/rweng18/legal-judgment/pull/13): initial masking.
- [PR 14](https://github.com/rweng18/legal-judgment/pull/14): training residual review, MASKED v2 and model-input guard.
- [PR 15](https://github.com/rweng18/legal-judgment/pull/15): word/token-length pipeline.
- [PR 16](https://github.com/rweng18/legal-judgment/pull/16): Hayden's six accepted additions.

The selected pool is Becca's 114 unanimous inclusions plus Hayden's six additions. Five additions enter training and one enters the reserved test period. Existing assignments and development FULL/MASKED texts are unchanged. Sodhi (`NY-4655053`) remains held for unresolved companion identity/date. The team's review confirmation does not supply that missing information.

| Use | Affirmed (0) | Reversed/vacated (1) | Total |
|---|---:|---:|---:|
| Train: 2010–2020 | 59 | 27 | 86 |
| Validation: 2021–2022 | 8 | 8 | 16 |
| Reserved test: 2023–2024 | 12 | 5 | 17 |
| Unassigned companion hold | 1 | 0 | 1 |
| Selected pool | 80 | 40 | 120 |

There are **119 assigned cases**, of which **102 enter development experiments**. The other 35 review candidates and 14 withheld candidates in Partition A stay outside the selected pool. The current coverage is below the proposal's 150-reviewed-case MVP target. We have an operational checkpoint, not a large-sample benchmark.

Labels describe the current whole appeal, not the winning party or future judgments. Review acceptance is recorded in [team_review_confirmation.json](team_review_confirmation.json); no additional blinded annotation protocol or inter-human agreement measurement is inferred. Original draft-agreement statistics are labeled separately.

## Experiment protocol and feedback

- Family links and calibration exposure are applied before modeling; no known selected family crosses splits. Only source opinion text becomes a feature. Labels, review notes, IDs and selected annotation quotations are not appended to it.
- FULL uses Becca's frozen cleaner; MASKED uses frozen v2. A Windows adapter normalizes file CRLF to LF, checks against committed Git blobs, retains her strict record validator, and checks all export/split/base-text checksums. It also avoids the original loader's Windows path-key mismatch.
- **Masking audit:** before fitting, the assistant read eight full cleaned opinions and removed spans: two from each class in both train and validation. [Audit findings](outputs/masking_audit_review.json) record retained reasoning/history and residual concerns. The audit did not lead to validation-specific mask changes. This technical audit is separate from the team's review confirmation.
- **Random-removal control:** LR uses seeds 11, 23, 37, 51 and 71. Each opinion loses exactly the MASKED number of whitespace-delimited words. Random sentence selection with a partial final sentence preserves the remaining word order. All seeds are reported, including accidental removal of outcome words.
- TF-IDF: word unigrams/bigrams, `min_df=2`, maximum 30,000 features, L2 normalization. LR and linear SVM use balanced class weights. Fit vocabulary/IDF/scaling only on training cases.
- Frozen LEGAL-BERT: pinned revision in [model_lock.json](../provisional_a/model_lock.json), slow uncased tokenizer, no truncation, 510 content tokens plus CLS/SEP, no chunk overlap, batches of four. Mean content-token vectors, then a content-count-weighted chunk mean, give 768 features per opinion. StandardScaler and balanced LR fit on training only. The reused encoder function does not execute the older trial.
- Main controlled comparison fixes **C=1**. Secondary selection tries 0.1, 1 and 10 using validation balanced accuracy, then macro F1, then smaller C. Its scores use the selection set and are not independent generalization estimates.
- The **17 test cases remain reserved**: no test embeddings, predictions or scores. Earlier source review and preprocessing handoff included test records, so “reserved” means no model evaluation, not that nobody has ever seen the opinions.

## First results

These are fixed-C=1 scores on the same 16 validation opinions, with eight cases per class. Accuracy equals balanced accuracy for this balanced set.

| Model | FULL balanced accuracy | MASKED balanced accuracy | FULL macro F1 | MASKED macro F1 |
|---|---:|---:|---:|---:|
| TF-IDF LR | 68.75% | 62.50% | 0.676 | 0.600 |
| TF-IDF SVM | 75.00% | 50.00% | 0.733 | 0.418 |
| Frozen LEGAL-BERT + LR | 87.50% | 56.25% | 0.875 | 0.561 |

Majority: 50% balanced accuracy, macro F1 0.333. LR random removal: mean 67.50% balanced accuracy, SD 5.23 percentage points across five seeds. The pattern suggests sensitivity to outcome language, but one validation error is 6.25 percentage points. The control does not completely isolate outcome semantics from lost reasoning.

Validation-selected MASKED configurations all reach 62.50% balanced accuracy (LR C=1, SVM C=0.1, BERT LR C=10). Keep those secondary scores separate from the fixed-C comparison. [Metrics](outputs/metrics.json), [predictions](outputs/validation_predictions.jsonl), [error observations](ERROR_OBSERVATIONS.md), and [the full 16-case review packet](outputs/ERROR_REVIEW_PACKET.md) preserve the evidence.

The notebook includes min/median/mean/P90/max word and content-token lengths, over-510-token proportions, and chunk counts. All 192 FULL and 185 MASKED development chunks were processed. Five thousand paired family-bootstrap resamples supply descriptive validation intervals, not final-test uncertainty or correction for repeated validation use.

## Reproduce

Run from a **Git clone of this repository**; input verification reads committed blobs. Tested with Python 3.13. Do not run Python with `-O`, which disables assertions. No CourtListener token or paid annotation API is needed. The first checkpoint download needs internet; model runs use the local pinned snapshot.

```powershell
python -m venv .venv
& ./.venv/Scripts/python.exe -m pip install -r experiments/provisional_a/requirements.txt
& ./.venv/Scripts/python.exe -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cpu
& ./.venv/Scripts/python.exe -X utf8 experiments/provisional_a/download_encoder.py
& ./.venv/Scripts/python.exe -X utf8 experiments/mvp_a/execute_notebook.py
& ./.venv/Scripts/python.exe -X utf8 experiments/mvp_a/test_pipeline.py
& ./.venv/Scripts/python.exe -X utf8 experiments/mvp_a/presentation.py
```

Reuse an existing environment if installed. On macOS/Linux, use `.venv/bin/python` without PowerShell's `&` and install the corresponding supported PyTorch wheel. Detailed package versions are recorded in [runtime_provenance.json](outputs/runtime_provenance.json) and the existing [environment lock](../provisional_a/requirements-lock.txt).

The notebook actually refits classifiers and checks reproduced outputs. Cached encoder features are accepted only when IDs, text hashes, model revision and pooling match. Runtime values preserve the first completed run. Exact floating-point comparisons intentionally stop if a different platform changes saved decision scores: preserve this run, investigate, and use a new version rather than overwriting results.

`build_notebook.py` is an authoring utility that clears notebook outputs when rebuilding; it is not necessary for ordinary reproduction. Run `execute_notebook.py` afterwards if you change the notebook source. `presentation.py` regenerates report tables and figures from the saved results. Local checkpoints, embedding caches, joblib models and kernel files are ignored by Git.

## Verification and next steps

The delivered notebook executed all 14 code cells without errors. Verification recomputes all 34 model/C-condition metrics from predictions, checks identical validation IDs, training-only vocabulary, 102×768 finite feature matrices, matched random-removal budgets, and zero test predictions. Additional tests check tampered-input rejection, split/calibration integrity, exact reuse of original texts, controls and the 33 existing masking regressions.

Resolve remaining eligibility/family questions and expand reviewed coverage before stronger conclusions. Any masking change should use training cases and a new data version, followed by all affected conditions. Fix the final protocol before evaluating the reserved test period. Differences from the earlier provisional trial are not a controlled improvement: both selection and preprocessing changed.
