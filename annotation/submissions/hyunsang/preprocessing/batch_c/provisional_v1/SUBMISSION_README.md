# Batch C provisional preprocessing — engineering handoff

**PRE-HUMAN-REVIEW / NOT GOLD / NOT FROZEN.** No adjudicated outcome labels or final evaluation data are claimed here.

## Scope

- 168 Batch C candidates; three reviewers' eligibility audit: 127 unanimous include, 8 unanimous exclude, 9 unanimous review and 24 disagreements.
- Provisional development subset: 107 cases (train 96, validation 11). Reserved test-period opinions are omitted from development texts.
- FULL opinion cleaning and label-independent MASKED text rules plus sentence-removal logs, and pinned LEGAL-BERT token/chunk statistics.
- Source data and reviewer audit files are for provenance and QC, not predictive input features.

## Main files

- `C_development_v2_PROVISIONAL.jsonl`: provisional training/validation FULL and MASKED texts.
- `C_three_reviewer_audit_168.csv`: three-reviewer comparison.
- `case_family_manifest_C_168_PROVISIONAL.csv`, `case_family_review_C_candidates.csv`: screening and review queue.
- `C_masking_qc_v2.csv`, `C_masking_review_queue_v2.csv`, `masking_removal_logs_v2.jsonl`, `full_clean_removal_audit.jsonl`: cleaning/masking QA logs.
- `C_v2_exact_token_lengths/case_lengths.csv`, `length_summary.json`: exact tokenizer length statistics using settings from `experiments/provisional_b/encoder.py` (pinned LEGAL-BERT, 510 content tokens per chunk, no overlap).
- `run_batch_c_preprocessing.py`, `b_mask_v2.py`, `README.md`: reproducibility code and run instructions; `RUN_SUMMARY.json`, `file_checksums_sha256.json` record run metadata.

## Items needing team review before freezing

1. Two strong *candidate* family pairs: `NY-4304286` / `NY-6207931` and `NY-4387315` / `NY-6235219`. Both are train/train; **not confirmed duplicates**.
2. Two automatic masking QA flags: `NY-4427636` and `NY-5980564` (each has a removed sentence >80 words). Both are **not yet manually cleared**.
3. Final labels/adjudication for 24 reviewer eligibility disagreements and any other pending decisions, plus final split-family and masking revalidation.

This is a draft engineering handoff, not a request to merge or release a frozen gold dataset without team review.
