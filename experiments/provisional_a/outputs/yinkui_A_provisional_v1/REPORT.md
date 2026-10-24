# PROVISIONAL — Partition A trial results

> **NOT FINAL PROJECT RESULTS.** Development run only; label and dataset review are not certified by this report. For the original Yinkui trial, Hayden’s adjudication and Becca’s final preparation are pending. Do not interpret these scores as final test performance or a reliable model ranking.

Run: yinkui_A_provisional_v1. Input annotations: annotation/submissions/yinkui/batches/A/annotations.jsonl. Uses only Yinkui’s frozen independent LLM-draft annotations, not adjudicated human ground truth. All scores below are DEVELOPMENT validation scores. No test text is passed to preprocessing/feature extraction/model evaluation; only test metadata/counts and unsupervised family screening are used.

## Dataset and split

169 candidate decisions: 122 marked include, 36 pending review, 11 excluded. Modeling status counts: {'sealed_test': 17, 'included': 105, 'review': 36, 'exclude': 11}. The family screen does not certify complete family resolution.

| Period | Use | Affirmed (0) | Reversed/vacated (1) | Total |
|---|---|---:|---:|---:|
| 2010–2020 | Training | 62 | 27 | 89 |
| 2021–2022 | Validation | 8 | 8 | 16 |
| 2023–2024 | Sealed test | 12 | 5 | 17 |

One validation error changes accuracy by 6.25 percentage points. Accuracy and balanced accuracy coincide only if the validation classes are balanced. This set is also used for C selection, so tuned scores are not independent performance estimates. Check the reviewed case count against the proposal’s 150-reviewed-case MVP target and 300-eligible-case threshold for stronger final conclusions.

## Main controlled experiment

Fix C=1 in advance for all learned conditions to isolate text changes. Class weights, vocabulary/IDF and BERT feature scaling are fitted using training data only. Confusion matrices use true rows and predicted columns in order [0, 1]. Full per-class recall and row-normalized matrices are in metrics.json and the notebook.

| Model | Text | C | Accuracy | Balanced accuracy | Macro F1 | Confusion matrix |
|---|---|---:|---:|---:|---:|---|
| Majority | FULL | None | 0.500 | 0.500 | 0.333 | [[8, 0], [8, 0]] |
| TFIDF_LR | FULL | 1.0 | 0.688 | 0.688 | 0.676 | [[7, 1], [4, 4]] |
| TFIDF_LR | MASKED | 1.0 | 0.625 | 0.625 | 0.600 | [[7, 1], [5, 3]] |
| TFIDF_SVM | FULL | 1.0 | 0.750 | 0.750 | 0.733 | [[8, 0], [4, 4]] |
| TFIDF_SVM | MASKED | 1.0 | 0.500 | 0.500 | 0.418 | [[7, 1], [7, 1]] |
| LEGAL_BERT_LR | FULL | 1.0 | 0.938 | 0.938 | 0.937 | [[7, 1], [0, 8]] |
| LEGAL_BERT_LR | MASKED | 1.0 | 0.562 | 0.562 | 0.561 | [[5, 3], [4, 4]] |

## Matched-length random-removal control (main LR experiment)

Five fixed seeds, uniform sentence removal order, with a random contiguous portion of the final sentence when needed to exactly match each opinion’s masked word-loss budget. Outcome sentences remain eligible for random removal. This is a word-budget control, not a matched BERT-token or matched semantic-content control. No seed is selected as the winner.

| Model | Text | C | Accuracy | Balanced accuracy | Macro F1 | Confusion matrix |
|---|---|---:|---:|---:|---:|---|
| TFIDF_LR | RANDOM_11 | 1.0 | 0.625 | 0.625 | 0.600 | [[7, 1], [5, 3]] |
| TFIDF_LR | RANDOM_23 | 1.0 | 0.688 | 0.688 | 0.676 | [[7, 1], [4, 4]] |
| TFIDF_LR | RANDOM_37 | 1.0 | 0.625 | 0.625 | 0.600 | [[7, 1], [5, 3]] |
| TFIDF_LR | RANDOM_51 | 1.0 | 0.750 | 0.750 | 0.746 | [[7, 1], [3, 5]] |
| TFIDF_LR | RANDOM_71 | 1.0 | 0.688 | 0.688 | 0.676 | [[7, 1], [4, 4]] |

- accuracy: 0.675 ± 0.052 (sample standard deviation across five seeds, not a confidence interval).

- balanced_accuracy: 0.675 ± 0.052 (sample standard deviation across five seeds, not a confidence interval).

- macro_f1: 0.660 ± 0.061 (sample standard deviation across five seeds, not a confidence interval).

At fixed C, LR balanced accuracy changes from 0.688 (FULL) to 0.625 (MASKED); the random-removal mean is 0.675. The differences describe this tiny provisional validation sample. They do not identify a causal effect of outcome language: masking also removes some useful reasoning, and random removal can itself remove outcome cues.

## Proposal-specified hyperparameter search (secondary)

C ∈ {0.1, 1, 10}; maximize validation balanced accuracy, then macro F1, then smaller C. These are scores on the same validation set used for selection, not final test scores. Compare the fixed-C results above when isolating the masking effect.

| Model | Text | C | Accuracy | Balanced accuracy | Macro F1 | Confusion matrix |
|---|---|---:|---:|---:|---:|---|
| LEGAL_BERT_LR | FULL | 1.0 | 0.938 | 0.938 | 0.937 | [[7, 1], [0, 8]] |
| LEGAL_BERT_LR | MASKED | 1.0 | 0.562 | 0.562 | 0.561 | [[5, 3], [4, 4]] |
| Majority | FULL | None | 0.500 | 0.500 | 0.333 | [[8, 0], [8, 0]] |
| TFIDF_LR | FULL | 10.0 | 0.750 | 0.750 | 0.733 | [[8, 0], [4, 4]] |
| TFIDF_LR | MASKED | 1.0 | 0.625 | 0.625 | 0.600 | [[7, 1], [5, 3]] |
| TFIDF_LR | RANDOM_11 | 10.0 | 0.688 | 0.688 | 0.654 | [[8, 0], [5, 3]] |
| TFIDF_LR | RANDOM_23 | 10.0 | 0.750 | 0.750 | 0.733 | [[8, 0], [4, 4]] |
| TFIDF_LR | RANDOM_37 | 1.0 | 0.625 | 0.625 | 0.600 | [[7, 1], [5, 3]] |
| TFIDF_LR | RANDOM_51 | 1.0 | 0.750 | 0.750 | 0.746 | [[7, 1], [3, 5]] |
| TFIDF_LR | RANDOM_71 | 10.0 | 0.750 | 0.750 | 0.733 | [[8, 0], [4, 4]] |
| TFIDF_SVM | FULL | 1.0 | 0.750 | 0.750 | 0.733 | [[8, 0], [4, 4]] |
| TFIDF_SVM | MASKED | 0.1 | 0.625 | 0.625 | 0.600 | [[7, 1], [5, 3]] |

## Masking audit and professor feedback

See the run-specific MASKING_AUDIT_REVIEW.md and MASKING_AUDIT_PACKET.md. The sampling design includes both classes in training and validation. Review outcome removal, retained reasoning and historical decisions before fitting; record the actual reviewer and findings. An assistant check is not human approval.

For the original yinkui_A_provisional_v1 run, all eight sampled whole-appeal dispositions were removed, but two validation opinions showed collateral deletion and a training outlier lost 57% of its words. One sampled opinion retained ancillary procedural results. Those validation findings were recorded without changing rules. New runs require a fresh audit rather than inheriting these observations. The audit and five-seed random-removal control implement both feedback requests.

## Text lengths

| Split | Text | Minimum words | Median | Mean | P90 | Maximum |
|---|---|---:|---:|---:|---:|---:|
| train | FULL | 86 | 468.0 | 516.7 | 843.0 | 1495 |
| train | MASKED | 64 | 428.0 | 476.0 | 805.2 | 1434 |
| validation | FULL | 276 | 534.0 | 650.9 | 925.5 | 1796 |
| validation | MASKED | 250 | 466.0 | 588.7 | 872.0 | 1671 |

Masking removes a mean 9.6% of words per opinion (median 8.3%, maximum 57.0%). The historical dataset_summary.json key `removed_fraction` contains percentage statistics; individual dataset rows contain true fractions.


| Split | Text | Min tokens | Median | Mean | P90 | Max | >510 content tokens | Total chunks |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| train | FULL | 113 | 642.0 | 710.4 | 1189.2 | 1900 | 66.3% | 163 |
| validation | FULL | 375 | 714.0 | 868.2 | 1252.0 | 2320 | 87.5% | 36 |
| train | MASKED | 82 | 593.0 | 656.8 | 1128.0 | 1810 | 64.0% | 161 |
| validation | MASKED | 331 | 634.5 | 785.7 | 1208.0 | 2147 | 81.2% | 35 |

LEGAL-BERT uses every non-overlapping chunk of up to 510 content tokens plus CLS/SEP. Padding and special tokens are excluded from mean pooling. Chunk vectors are averaged with content-token-count weights; no first-512 truncation and no fine-tuning.

## Error analysis and next review

ERROR_REVIEW_PACKET.md includes all 16 validation opinions, their original source links, FULL/MASKED LR and cross-model predictions, removed passages, and masked text. This is a review queue, not a claim that every error has been legally adjudicated. The original run also has ERROR_OBSERVATIONS.md with four assistant-reviewed examples. Automatic length-group summaries are in subgroup_metrics.json; each bin’s class counts must accompany its scores.

tfidf_features.json lists training-derived positive/negative coefficients at C=1. Coefficients are diagnostic associations, not explanations of legal causation. Because validation is small, no claim that LEGAL-BERT is superior is justified by one run.

Hayden: confirm eligibility and labels independently of these predictions, especially procedural-plus-merits and ambiguous property cases; preserve disagreements. Becca: finalize case families, source cleanup and masks, inspect collateral removal and residual cues, and freeze the reviewed dataset. Yinkui: rerun all conditions under a new run name on that dataset. Keep the test period sealed until the final pipeline and evaluation labels are fixed.

For the final study, compute paired 95% bootstrap intervals using case families for test metrics and FULL-minus-MASKED differences. This prototype deliberately provides no test intervals or test metrics. Expand beyond A if stronger comparative conclusions are needed.
