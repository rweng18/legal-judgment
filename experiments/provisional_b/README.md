# Partition B+C development experiments

Becca owns the notebook, model selection and reporting. Open `provisional_b.ipynb` after Hayden freezes the reviewed development release. The notebook ships with empty outputs. The combined B+C study preserves batch IDs. It trains on 2010–2020, evaluates on 2021–2022 and reserves 2023–2024. Confirm the release matches those choices before running it.

## Hayden’s handoff

For Hayden’s tokenizer settings, length-report command and return checklist, use the [B+C encoder handoff](HAYDEN_ENCODER_HANDOFF.md).

Use one release directory, for example `inputs/bc_v1/`. The three files below form the interface. A different upstream format can be mapped to these fields while preserving the original values, IDs and provenance.

1. **manifest.jsonl** contains one metadata row per B/C candidate across all periods, including exclusions and reserved cases. Fields are `case_id`, `batch` (B or C), `date_filed` (YYYY-MM-DD), `period` (train, validation or test) and `eligibility` (include, review or exclude). Included rows need a reviewed `family_id`. Included development rows also need integer `label` (0 affirmed, 1 reversed/vacated) and `review_status` = `reviewed`. Supply `calibration_exposure` as a boolean if available. Resolve family conflicts in the split manifest before freezing. The runner rejects included families spanning periods and known calibration exposures outside training. Test labels may be omitted.
2. **development.jsonl** contains exactly the included training and validation IDs, each once. Each row has `case_id`, `batch`, `date_filed`, `period` and `texts` with nonempty `FULL` and `MASKED` strings. Supply the final cleaned texts. Keep the source opinions, removal logs, family decisions and the review trail with the dataset version. The experiments use only these two strings as text features.
3. **release.json** records the freeze and SHA-256 hashes of the two files as delivered. Example shape:

```json
{
  "status": "frozen",
  "reviewed_by": "<reviewer>",
  "dataset_version": "<dataset version>",
  "split_version": "<split version>",
  "mask_version": "<mask version>",
  "sha256": {
    "manifest.jsonl": "<64 lowercase hex digits>",
    "development.jsonl": "<64 lowercase hex digits>"
  }
}
```

Generate the digests after the files are final, for example with `shasum -a 256 manifest.jsonl development.jsonl`. Hashes identify exact file bytes. The loader checks both files, joins the IDs and uses chronological metadata to keep reserved test text out of modeling.

## Setup and length summaries

Run the commands below from `experiments/provisional_b` in a Python 3.11 or 3.12 virtual environment.

```sh
python -m pip install -r requirements.txt
python -m ipykernel install --user --name legal-bc --display-name "Legal B+C"
```

Select the **Legal B+C** kernel in the notebook. The first tokenizer or encoder load needs access to the pinned Hugging Face files or an existing local snapshot in the Hugging Face cache. For an offline run with that snapshot already installed, set `HF_HUB_OFFLINE=1`.

Hayden can run this utility as soon as the cleaned development texts are available, then rerun it on the freeze under a fresh output name. It needs only NumPy and Transformers plus the tokenizer files. It does not load model weights.

```sh
python lengths.py inputs/bc_v1/development.jsonl runs/bc_v1_lengths
```

`encoder_settings.json` and the shared `encoder.py` pin `nlpaueb/legal-bert-base-uncased` at revision `15b570cbf88259610b082a167dacc190124f60f6`. Use the slow checkpoint tokenizer on each complete text independently. Count content tokens before specials or padding. Keep contiguous windows of 510 tokens, including the final short window. Add CLS and SEP per chunk for model inference. One opinion with 1,100 content tokens produces chunks of 510, 510 and 80. A 510-token opinion fits one input.

`case_lengths.csv` records whitespace word counts, content tokens, chunks, final-chunk content length, the over-one-input flag and paired reductions for every case. A reduction is FULL minus MASKED. Its percentage uses that case’s FULL count as denominator. `length_summary.json` reports minimum, median, mean, 90th percentile and maximum by split and variant, total chunks, fraction over 510 content tokens, and distributions of paired changes. The source checksum and tokenizer revision identify the inputs.

## Running the experiments

The [completed frozen LEGAL-BERT comparison](runs/b_bert_assumed_reviewed_v1/REPORT.md) includes all model results, an executed notebook, reusable embedding matrices, and full reproduction details for the available Batch B cases.

The [reporting tables](runs/b_bert_assumed_reviewed_v1/REPORTING.md) and [updated executed notebook](runs/b_bert_assumed_reviewed_v1/Batch_B_reporting_results.ipynb) include split and fold class counts, all metrics alongside the majority baseline, and raw and row-normalized confusion matrices in label order 0, 1.

The [development error analysis](runs/b_bert_assumed_reviewed_v1/error_analysis_v1/ERROR_ANALYSIS.md) reviews eight cases, including every FULL/MASKED disagreement, a shared failure, a short-opinion error, and the longest opinion as a correct comparison case. It documents residual outcome reasoning, procedural-history ambiguity, and length-related hypotheses with exact evidence offsets and an unchanged-source audit. Labels, predictions, masking rules, and model settings remain as originally reported.

The complete Batch B comparison is available through `run_bert.py`. It loads the saved SVM run's training folds, reproduces the lexical models, then selects the frozen-encoder classifier's C on MASKED training folds. Use the pinned environment for this stage. From this folder, run:

```sh
python download_encoder.py
HF_HUB_OFFLINE=1 python run_bert.py ../../annotation/submissions/hyunsang/preprocessing/batch_b/provisional_v1 runs/b_svm_assumed_reviewed_v1 runs/b_bert_assumed_reviewed_v1 --assume-labels-reviewed
python results_notebook.py runs/b_bert_assumed_reviewed_v1
```

Choose a fresh destination when reproducing a completed run. The combined package includes the environment lock, per-case predictions, fold assignments, model-selection scores, confusion matrices, length summaries, checkpoint hashes, and both embedding matrices with a case-ID index. Frozen vectors are also cached in `.cache/vectors`. Checkpoints and tokenizer files are cached in `.cache/huggingface`.

The [Batch B linear SVM and combined comparison](runs/b_svm_assumed_reviewed_v1/REPORT.md) reuse the logistic-regression run's saved folds and verify the earlier baseline predictions. Use `run_svm.py` with the package, saved logistic-regression run, fresh output directory and `--assume-labels-reviewed`.

The [Batch B TF-IDF logistic-regression results](runs/b_logistic_assumed_reviewed_v1/REPORT.md) use the same cases and review assumption as the majority run. Reproduce them with `run_logistic.py`, which checks the supplied inputs against the saved majority run before fitting.

The available Batch B majority baseline has been run under the user's assumption that the supplied labels have been reviewed. Its [results and reproduction command](runs/b_majority_assumed_reviewed_v1/REPORT.md) preserve that assumption and the exact evaluation case list. The `run_majority.py` entry point supports this Batch B package with the explicit `--assume-labels-reviewed` option.

In the notebook, choose the release path and a fresh output directory, select the kernel and run all cells. Save an executed copy with the run so the template remains reusable. The commands below call the same functions. The first is an optional lexical check. The second runs the reported suite, starting with the majority classifier and lexical models before loading the encoder.

```sh
python experiment.py inputs/bc_v1/release.json runs/bc_v1_lexical --lexical-only
python experiment.py inputs/bc_v1/release.json runs/bc_v1
```

The training majority breaks a label-count tie in favor of class 0. Each learned model uses the same grouped folds. The deterministic splitter assigns each family to one holdout fold, ensures both classes occur in every fold, and balances each fold’s share of each class where feasible. It uses three folds when each class occurs in at least three families, two if the smaller count is two, and stops below two. Fold construction uses training labels and family IDs only.

Choose C from 0.1, 1 and 10 using MASKED text. Average the holdout balanced accuracies across folds, break ties by mean macro F1, then by smaller C. Refit the full pipeline on all training cases separately for each variant at that same model-specific C. TF-IDF uses word unigrams/bigrams, min_df=2, at most 30,000 features and L2 vector normalization. The linear classifiers use balanced weights. Frozen LEGAL-BERT runs in evaluation mode and pools the final hidden layer over all content tokens across all chunks. Each encoder classifier fits its own training-only scaler. The vector cache is keyed by exact text, encoder settings, implementation and software versions.

## Reading and reproducing a run

- `results.csv` contains development sample size, C, accuracy, balanced accuracy, macro F1 and per-class recall for every model and variant.
- `predictions.csv` pairs each case’s reviewed label with its prediction and, for the learned models, its decision score.
- `confusion_matrices.json` and `confusion_matrices.png` use true rows, predicted columns and class order [0, 1]. The figure also includes within-class percentages.
- `class_counts.csv` records label counts for each included split and each CV fold's training and held-out portions. Reserved test cases are not included in these development runs.
- `reporting_summary.json` adds exact row-normalized matrices and verified metrics; `REPORTING.md` presents the full reporting tables. Accuracy is the overall correct fraction, balanced accuracy is mean recall across labels 0 and 1, and macro F1 is mean F1 across both labels. Balanced accuracy selects settings, with macro F1 as the tie-breaker.
- `selection.json` records all MASKED fold scores, means and the selected C. `splits.csv` records development split and training holdout fold by ID.
- `run.json` records input hashes and versions, model parameters, class order, seed, encoder settings, software versions and source hashes. Rerun using the same frozen inputs and a new output directory.

Reporting supplements can be regenerated without retraining using `python reporting.py runs/RUN_NAME`. They verify the saved predictions against the results, record source checksums, and preserve the original run metadata. New runs generate these supplements automatically. The historical Batch B packages retain the source hashes from their original model execution; the supplement records the reporting code separately.

For the synthetic protocol checks, run `python -m unittest -v test_protocol`. The checks create temporary files. The pooling check uses deterministic token vectors, including special and padding tokens.
