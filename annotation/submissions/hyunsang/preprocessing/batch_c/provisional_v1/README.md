# Batch C pre-review preprocessing runner

This package is based on the Batch B revised masking QC script and the team A/B source-cleaning/LEGAL-BERT code. It requires your existing Mac clone at `~/Downloads/legal-judgment`, the working Python 3.12 virtualenv with `numpy==2.3.4` and `transformers==4.57.1`, and access to the Yinkui Batch C Git branch if not already cached. It changes **no Git branch or working files**; generated output stays inside this folder.

Unzip as `~/Downloads/Batch_C_PRE_REVIEW_READY/` and run from your active `(venv)` Python:

```bash
python ~/Downloads/Batch_C_PRE_REVIEW_READY/run_batch_c_preprocessing.py
```

It will produce the 3-reviewer C audit, conservative case-family candidates and split manifest, FULL/MASKED development text, removal logs, QC queue, and **exact** LEGAL-BERT token length files. If a source mismatch or missing file appears, it fails instead of guessing. Run it only once in a fresh package copy: exact lengths refuse overwriting an existing output folder.

Important: no human-reviewed gold labels, no final data freeze, and no external cases searched.
