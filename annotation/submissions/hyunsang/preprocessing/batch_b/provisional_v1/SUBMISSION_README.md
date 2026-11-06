# Batch B provisional preprocessing — engineering handoff

**Status: PRE-REVIEW / NOT HUMAN GOLD / NOT FROZEN.** This is an engineering QC run, not the final B+C modeling release. Do not use `llm_draft` records as approved evaluation labels.

## Scope and inputs

- Batch B has 169 candidates; all three independent reviewers' submissions were compared. 125 cases were unanimous `include`, 9 unanimous `exclude`, 5 unanimous `review`, and 30 had different eligibility decisions.
- The provisional development subset has 112 unanimous-include cases (97 train from 2010–2020, 15 validation from 2021–2022). Reserved 2023–2024 test texts are not in the development input.
- Source opinion data and review comparison input snapshots are in `inputs/` for audit/reproduction, not predictive features. No reviewer annotation labels are used by the MASKED text rules.

## Files

- `B_development_v2_PROVISIONAL.jsonl`: cleaned FULL and preliminary MASKED texts for 112 development candidates.
- `masking_removal_logs_v2.jsonl`, `B_masking_qc_112_v2.csv`, `B_masking_review_queue_v2.csv`: removed spans, automatic quality flags, and unresolved text checks.
- `case_family_review_7pairs.csv`, `case_family_manifest_B_169_PROVISIONAL.csv`, `named_family_warnings.json`: duplicate/family candidate screening. Five strong candidate pairs are **not legally confirmed**.
- `B_v2_exact_token_lengths/case_lengths.csv` and `length_summary.json`: tokenizer-based word/token/chunk report. Uses the pinned `nlpaueb/legal-bert-base-uncased` tokenizer at revision `15b570cbf88259610b082a167dacc190124f60f6`, with 510 content tokens per chunk, no overlap.
- `make_batch_b_pre_review.py`, `run_exact_legalbert_lengths.py`, `Batch_B_QC_stats.ipynb`: regeneration, length calculation and descriptive QC notebook.
- `RUN_SUMMARY.json` and `file_checksums_sha256.json`: original pre-tokenization QC snapshot metadata; do not mistake their old `exact_legalbert_tokenization` field for the final state. The actual tokenization outputs are in `B_v2_exact_token_lengths/`.

## Reproduction

From this folder run `python make_batch_b_pre_review.py` to regenerate pre-review QC. **This overwrites provisional outputs**, so reproduce in a clean copy if you want to preserve this run's bytes. Then from `experiments/provisional_b` in an environment with `numpy==2.3.4` and `transformers==4.57.1` run:

```bash
PYTHONPATH="$PWD" python /absolute/path/to/run_exact_legalbert_lengths.py /absolute/path/to/this/folder
```

The exact length script refuses an existing output directory. Choose a clean copy for regeneration. The tokenizer-only step does not require PyTorch.

## Unresolved before final release

1. Human-reviewed/adjudicated labels and outcome targets; 30 eligibility disagreements in B remain unresolved.
2. Human/legal case-family confirmation of candidate pairs and related boundary checks.
3. Human quality review of possible residual outcome cues and over-masking, including 2 flagged cases.
4. Final reviewed B+C release with version, hashes and split/family checks, followed by a fresh length report on exact frozen texts.
