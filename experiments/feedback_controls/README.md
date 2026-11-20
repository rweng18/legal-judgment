# Team 11: feedback experiments and reviewed final evaluation

Finalized November 20, 2026. Start with **[the executed notebook](Team_11_Feedback_Experiments.ipynb)**. The report is maintained locally and is intentionally excluded from this GitHub push. All notebook figures are included under `results/figures/`.

## What is complete

All planned experiments are executed: expanded FULL/MASKED replication, fixed-C=1 sensitivity, five-seed matched random removal for **both LR and LEGAL-BERT**, the 2×2 masking-component ablation, first-chunk versus all-chunk features, separate deduplication/masking sensitivities, nested family learning curves, and prediction changes linked to the eight-case passage audit. A separate diagnostic holds the fitted FULL classifier fixed.

After Yinkui Yu's review confirmation (review date **November 19, 2026**), the final release and protocol were frozen and the reserved test was evaluated once. The final fit uses **278 training cases**, with **42 development-validation cases** kept out of fitting and **50 test cases** (34 affirmed, 16 reversed/vacated). No additional duplicate/related-appeal corrections were supplied. The approved Mann duplicate NY-6112018 is removed, retaining NY-4306359. The 54 disputed B/C eligibility cases remain excluded.

Review confirmation is recorded in `final/inputs/human_review_confirmation.json`, with the user's exact statement, the scope interpretation stated in chat, and the source revisions supporting the accepted labels. It is user-confirmed review, not a new blinded inter-human annotation experiment. The original draft annotations and provisional releases remain historical artifacts. Older templates under `review/` are not outstanding requests: the confirmation and frozen manifest supersede them for this release.

## Main findings

| Balanced accuracy | LR | LEGAL-BERT |
|---|---:|---:|
| Validation FULL | 82.12% | 88.12% |
| Validation MASKED | 53.65% | 50.35% |
| Validation random-removal mean | 74.28% | 75.62% |
| Test FULL | 81.80% | 89.52% |
| Test MASKED | 66.36% | 74.63% |
| Test random-removal mean | 76.88% | 80.37% |

The targeted mask hurts more than quantity-matched random removal in development. On test, LEGAL-BERT's random-minus-mask difference is much smaller: **5.74 points, paired 95% interval −7.06 to 19.31**. LR's corresponding test difference is **10.51 points, interval 2.76 to 20.24**. This supports a cautious account of information loss, not a pure measurement of outcome leakage or a definitive model ranking.

All three masked models have **70% test accuracy**, versus a 68% majority baseline, but different class recalls. Report accuracy, balanced accuracy, macro F1, confusion matrices and class counts together. The notebook includes every requested metric.

## Evidence map

- `inputs/protocol.json`: original frozen development protocol, 279/42 cases. Its provisional status is historical and intentionally preserved.
- `inputs/quality_v1/`: approved, uniform rule corrections and matched controls, frozen separately.
- `results/metrics.json`, `predictions.jsonl`: **126 development conditions, 5,292 predictions**. Some conditions intentionally reuse a fitted model to isolate one factor; this is not 126 independent studies.
- `results/seed_summaries.json`, `paired_intervals.json`: all seeds and 5,000 paired validation-family resamples. Development intervals are descriptive because validation was repeatedly used.
- `results/audit_prediction_links.json`: 22 verified evidence quotations across eight preselected cases, five random seeds, and both fitting modes.
- `results/two_class_mask_audit.json`: two examples per class in training and validation; includes remaining masking failures.
- `results/chunk_length_groups.json`, `length_statistics.json`: length/chunk groups with class counts and performance.
- `final/inputs/protocol.json`: decisions frozen before test predictions; previously selected C values, seeds and primary/secondary comparisons.
- `final/inputs/reviewed_manifest.jsonl`: accepted 370 train/validation/test records and review provenance.
- `final/results/`: **21 final conditions, 1,050 predictions**, per-model intervals and paired family-bootstrap differences.
- `results/complete_verification.json`: metric recomputation, exact word budgets, reviewed manifest, no known family/period overlap, no cross-period exact FULL duplicates, embedding hashes/shapes, and frozen final-output checks.

## How the experiments were run

Use Python with the recorded versions in the run/embedding metadata. Run commands from the repository root; `-X utf8` is important on Windows. No API token is needed. The encoder requires the locally cached pinned checkpoint `nlpaueb/legal-bert-base-uncased`, revision `15b570cbf88259610b082a167dacc190124f60f6`. Its three file checksums are verified before extraction. It is never fine-tuned.

Preparation scripts refuse to overwrite frozen protocols. The final evaluator refuses to replace existing final metrics. The normal audience workflow is to open the executed notebook or run the read-only verification:

```powershell
python -X utf8 experiments/feedback_controls/verify_all.py
python -X utf8 experiments/feedback_controls/execute_notebook.py
```

The notebook refits one development LR example as a demonstration and checks saved outputs. It **never reruns the final test**. Its execution counts and outputs are real.

The completed execution sequence was:

```text
prepare_controls.py          # canonical Git-blob inputs; freeze original controls
quality.py                   # freeze revised rules and word-matched controls
extract.py --snapshot PATH   # resumable frozen development embeddings
run_experiments.py --stage lexical
run_experiments.py --stage bert
analyze.py                   # metrics, bootstrap, case/passage linkage
audit_masks.py               # two-class training/validation checks
final_test.py freeze         # user review, consensus-label checks, fixed protocol
extract_final.py --snapshot PATH
final_test.py evaluate       # one reserved-test evaluation; overwrite guard
verify_all.py
build_notebook.py            # unexecuted notebook source using included results/figures
execute_notebook.py          # execute generated notebook, verify all cells
```

`build_notebook.py` replaces the notebook with its source, so always execute it afterward before publishing. The notebook does not require the separate local report directory.

## Interpretation and next steps

Keep the original matched comparison separate from the 278-row deduplicated fit. Primary MASKED uses inherited policies by batch; secondary REVISED is a uniform policy. The boundary-only change improves retention without changing LR validation predictions. The matcher-only change yields identical text on this corpus. Refined masking is not uniformly more accurate, and residual direct cues remain. The final mask was not changed after seeing test performance.

Known family grouping prevents the identified relatives from crossing splits. It does not establish complete deduplication or independence of every record. Removing the one approved Mann duplicate is a sensitivity check, not proof that all publication aliases are gone. Human review and bootstrap intervals also do not eliminate selection bias, label uncertainty or possible encoder pretraining overlap.

The reserved test is now consumed. Next work should explain the differing validation/test findings and finalize the project presentation. New model selection or mask revisions need new held-out evaluation data; do not optimize against the saved test results.
