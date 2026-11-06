# Batch B — PRE-REVIEW PREPROCESSING PACKAGE (engineering draft)

Five tasks: (1) case-family screen: 7 candidate pairs, 5 strong from matching caption/date/high text overlap; (2) revised label-blind sentence masking; (3) FULL/MASKED quality flags and removal logs; (4) exact LEGAL-BERT tokenizer runner prepared, **NOT executed** in this runtime; (5) reproducible machine-readable data, Python generator, QC notebook and checksum support.

## Sources
- 506 source opinions and source metadata from the project, no external case lookup
- 169 case Batch B 3-reviewer comparison table
- 112 B unanimous-include *development-only* (97 train, 15 validation) source-derived FULL texts
- pre-review FULL cleaning inherited from the A prototype; MASKED rules revised in the local QC generator

## NOT completed / blockers
- No human annotation adjudication, family confirmation, or final label release. The 30 B disagreements remain outside the exploratory modeling subset.
- No exact LEGAL-BERT tokenizer result (network access to pinned checkpoint unavailable).
- No proof of leakage-free masking: new text flags need a separate legal-content audit. Only training examples should inform further rule changes.
- This package covers provisional B development only; final release requires reviewed B+C and 2023–24 metadata-only test cases.

## Generate exact tokenizer lengths on Mac
1. `cd ~/Developer/legal-judgment/experiments/provisional_b` (or actual clone path).
2. `python3 -m venv .venv && source .venv/bin/activate`
3. `python -m pip install "numpy==2.3.4" "transformers==4.57.1"`
4. `python /absolute/path/to/Batch_B_PRE_REVIEW_READY/run_exact_legalbert_lengths.py /absolute/path/to/Batch_B_PRE_REVIEW_READY`
The output will be `B_v2_exact_token_lengths/case_lengths.csv` and `length_summary.json`. On later frozen B+C release, regenerate with **that** frozen development.jsonl.

## Reproduce QC
The `inputs/` folder contains all source-derived input files for the B-only engineering run, including the 506-opinion pool and three-reviewer comparison table. From the extracted `Batch_B_PRE_REVIEW_READY/` directory run `python3 make_batch_b_pre_review.py`. The script regenerates all provisional outputs. Open `Batch_B_QC_stats.ipynb` from that same directory and run its cells. No team annotations have been labeled `reviewed`.
