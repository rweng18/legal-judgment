# Partition A: provisional dataset and modeling pipeline

For Becca's dataset preparation, see the [tokenizer and chunking handoff](BECCA_ENCODER_HANDOFF.md) and [portable settings](encoder_settings.json), verified against the trial checkpoint.

This is a complete development trial using **Yinkui's 169 independent A annotations only**. It implements Becca's dataset-preparation steps and Yinkui's model experiments so we can check the workflow before Hayden's adjudication and Becca's final dataset are ready. It does not replace their work or update any person's annotations.

Start with [the results report](outputs/yinkui_A_provisional_v1/REPORT.md) or [the executed notebook](outputs/yinkui_A_provisional_v1/provisional_A_results.ipynb). The notebook displays and verifies real saved experiments; training is performed by `train.py`. [Initial qualitative observations](outputs/yinkui_A_provisional_v1/ERROR_OBSERVATIONS.md) discuss four development cases. All scores are provisional validation results, **not final test results**.

## What went into this run

- Input labels: `annotation/submissions/yinkui/batches/A/annotations.jsonl` (169 records; original records unchanged).
- Opinion text: `annotation/source/cases.jsonl`; A assignment: `annotation/batches/A/manifest.json`.
- Eligibility: 122 include, 36 review, 11 exclude. Review/excluded records remain in the manifest, but do not enter training/evaluation.
- Training, 2010–2020: 89 cases, with 62 affirmed and 27 reversed/vacated.
- Validation, 2021–2022: 16 cases, with 8 per class.
- Reserved test, 2023–2024: 17 cases, with 12 affirmed and 5 reversed/vacated. No model inputs, embeddings, predictions or test metrics are produced for these cases.
- Every label remains an **LLM draft**. Validation is not yet independently human reviewed, so this run cannot satisfy the proposal's final ground-truth requirement.
- The current automatic family screen found the Coreano pair; no eligible case was removed by family/duplicate checks. Similarity checks are incomplete evidence of family independence, not a substitute for Becca/Hayden's review.
- Four included calibration cases fall in training. No calibration-exposed record enters validation/test modeling.

The trial uses 105 development decisions and seals 17 for later. It falls below the proposal's 150-reviewed-case MVP target. Do not report “169 usable labeled cases” or present this as a completed 150-case reviewed MVP.

## Proposal and feedback alignment

| Requirement | Implementation / remaining limit |
|---|---|
| Classify published opinions | Labels refer to the current appeal, not plaintiff success or future litigation outcomes |
| Same cases across text/model comparisons | Fixed manifest and shared validation IDs; assertions verify this |
| Chronological case-family split | 2010–2020 / 2021–2022 / 2023–2024; cross-period families excluded; explicit family hints supported |
| Human evaluation labels | **Pending**; current trial deliberately uses Yinkui drafts and labels every output provisional |
| FULL versus MASKED | Cleaned controlling opinion versus automatic removal of direct current-outcome sentences; no annotation evidence spans enter inputs |
| Masking feedback | Eight-case pre-model audit: two per class in both training and validation; [findings](outputs/yinkui_A_provisional_v1/MASKING_AUDIT_REVIEW.md) document outcome removal, preserved history/reasoning and collateral deletion |
| Random-removal feedback | Main TF-IDF LR experiment, five fixed seeds, exact per-case masked word-loss budget |
| Models | Training-majority baseline; TF-IDF + LR; TF-IDF + linear SVM; frozen LEGAL-BERT + LR |
| Metrics | Accuracy, balanced accuracy, macro F1, raw and row-normalized confusion matrices, class counts, per-class recall |
| Hyperparameters | C = 0.1, 1, 10; validation balanced accuracy, macro F1 tiebreak, smaller C final tiebreak |
| Controlled comparison | Separately report preselected C=1 for every text condition; distinguish this from validation-tuned results |
| Lengths | Word and LEGAL-BERT content-token summaries, >510-token share and chunk totals; no final-test text length inspection |
| Interpretation | Four initial qualitative observations, complete 16-case validation review packet, training coefficients and length-bin counts/scores |
| Final uncertainty estimates | Deferred with final test evaluation; paired family bootstrap intervals belong to the locked final study |

No proposal source was changed. Its 506-case pool and larger study targets remain plans; the smaller A-only engineering trial is explicitly reported here.

## What the preprocessing does

1. Validate annotation schema, IDs and exact supporting-quote offsets with the existing annotation validator. This checks structure/evidence alignment, not semantic correctness.
2. Group same normalized case names, docket strings and source hashes across the saved pool; apply explicit family hints. Compare A texts with word 5-gram Jaccard: >=0.65 enters a review queue; >=0.85 conservatively groups. These unsupervised checks do not become model features. Docket strings can be ambiguous across counties, and less similar companion cases can be missed.
3. Record every A candidate in a split manifest. Retain only `eligibility.binary_task == include` with label 0/1. Remove cross-period families and exact duplicate versions. Keep calibration exposure in the training period only. No class balancing by sampling or swapping cases across periods.
4. Build FULL by removing markup, recognized header/footer metadata and explicitly marked separate dissent text. These rules are provisional, not a guarantee that every unusual opinion format is parsed perfectly.
5. Build MASKED with label-independent sentence rules for operative orders and express statements of the current appellate result. Historical trial rulings and parenthetical precedents are generally retained. No label, supporting quote, confidence, rationale or case feature annotation is passed into the text transform.
6. Save exact removed spans, reason codes, hashes and word counts. Save all random-removal indices and how many automatically identified outcome words each control happened to delete.
7. Produce the seeded audit packet. An assistant/human must read the relevant opinions and record findings before training. **Existence of the audit file is an execution gate, not evidence of human approval.**

Known masking limitations: removing an entire sentence can discard reasoning and citations. “Inc.” can join a historical ruling to the next disposition; “Supreme Court properly considered” can remove an evidentiary ruling unrelated to the appeal's overall outcome. Some ancillary procedural results remain. One short training opinion loses 57% of its words. These findings are preserved for revision, not hidden by dropping cases after seeing results. The validation audit did not change the rules in this run.

## Models and controls

TF-IDF: word unigrams/bigrams, `min_df=2`, at most 30,000 features, default L2 vector normalization. Vocabulary and IDF are fitted only on training opinions for each condition. LR uses L2 regularization, `liblinear`, balanced class weights and at most 10,000 iterations. LinearSVC uses balanced class weights, `dual=auto`, at most 20,000 iterations. Seeds and settings are in `config.json` and each saved `run_config.json`.

Frozen encoder: [`nlpaueb/legal-bert-base-uncased`](https://huggingface.co/nlpaueb/legal-bert-base-uncased), pinned to the commit in `model_lock.json`. Each opinion is split into non-overlapping chunks of at most 510 content tokens plus CLS/SEP. The encoder runs in evaluation/inference mode with gradients disabled. Mean pooling excludes special/padding tokens; chunk vectors are averaged weighted by their content lengths. Every chunk is used. StandardScaler and balanced LR are fitted on training vectors only. No fine-tuning or LLM prediction calls are made.

Random-removal control: seeds 11, 23, 37, 51, 71, separately deterministic for each case. Shuffle all FULL sentence indices uniformly, removing sentences until the masked word budget is reached. Remove a random contiguous portion of the last selected sentence if needed. Preserve retained tokens' original order. Outcome sentences are eligible too. Report all five results and their mean/sample standard deviation; never pick the best seed. Equal word counts do not imply equal BERT-token counts or equal semantic information. This control is run for LR, as requested, not for every model.

The fixed-C table is the primary controlled ablation. The C-grid-selected table follows the proposal's tuning plan, but compares conditions whose C may differ. Because this validation set is used for selection, its selected scores are optimistic development estimates. Neither table proves real-world legal prediction ability. Unknown overlap with the encoder's pretraining data and citation/writing-style differences remain possible confounds.

## Reproduce this completed trial

Commands below run from the repository root. Tested with Python 3.13. Full installed versions are saved in `requirements-lock.txt`; key dependencies are in `requirements.txt`. The cached source dataset needs no CourtListener token or API requests.

```powershell
python -m venv .venv
& ./.venv/Scripts/python.exe -m pip install -r experiments/provisional_a/requirements.txt
& ./.venv/Scripts/python.exe -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cpu
& ./.venv/Scripts/python.exe experiments/provisional_a/download_encoder.py
& ./.venv/Scripts/python.exe experiments/provisional_a/train.py --reproduce
& ./.venv/Scripts/python.exe experiments/provisional_a/report.py
& ./.venv/Scripts/python.exe experiments/provisional_a/execute_notebook.py
& ./.venv/Scripts/python.exe experiments/provisional_a/test_pipeline.py
```

On macOS/Linux use `.venv/bin/python` and omit PowerShell's `&`; install the corresponding supported PyTorch wheel. The completed prepared dataset is provided, so do not rerun `prepare.py` with the existing run name. `--reproduce` checks that the full metrics object matches the saved result before replacing the metric file. Without that flag, training refuses to overwrite results. Small cross-platform floating-point differences can affect edge cases; preserve the old run and investigate under a new name if the equality check fails.

The model checkpoint, local joblib models, embedding caches, environment and temporary kernel files are ignored by Git. Texts, provenance, metrics, logs, review packets, plots and notebook are portable outputs. Loading joblib files is only needed for trusted models created locally by this script. Feature caches are keyed by encoder revision, case IDs, text hashes and pooling protocol. Changing preprocessing requires a new prepared run.

## Rerun after team review

1. Hayden saves an agreed annotation file separately, retaining original independent annotations and documenting disagreement decisions. Validation/test labels must be reviewed without model predictions or initial LLM suggestions, consistent with the proposal. Do **not** send the error packet as the first input to blind label adjudication.
2. Becca freezes prepared source records, family hints and masking rules. Use the same source schema and stable case IDs. If family relations are newly discovered, add them to a versioned file in the existing `family_hints.json` format. Changes to the source/manifest path go into a new config file, not the old run directory. Review unusual formats, procedural-plus-merits decisions, private-property evidence and short opinions.
3. Prepare a new run. For the same source/manifest schema, this example is sufficient (replace the annotation path with the real reviewed file):

```powershell
& ./.venv/Scripts/python.exe experiments/provisional_a/prepare.py --annotations annotation/adjudicated/A/annotations.jsonl --run-name reviewed_A_v1
```

For new source/family paths, copy `config.json` to a new config, update `source`, `family_hints`, `annotations`, `expected` and `run_name`, and pass `--config PATH`. Do not invent a reviewed file or change review-status fields without actual human review. The existing annotation validator requires all assigned IDs, including exclusions and unresolved cases.

4. Read the newly generated `MASKING_AUDIT_PACKET.md` before model fitting. Record case-specific findings in that new run's `MASKING_AUDIT_REVIEW.md`, identify who reviewed it, and keep human approval separate from assistant checks. Do not copy the old review as if it covered changed cases/texts. If changing masks, use training examples and a new mask version/run name; record validation audit concerns without tuning against final test data.
5. Run `train.py --run-name reviewed_A_v1`, then `report.py --run-name reviewed_A_v1`, then `execute_notebook.py --run-name reviewed_A_v1`. The scripts read the saved run config. **Review the narrative before sharing a new report:** the prototype's qualitative findings concern this original run; new labels or masks require fresh interpretation and audit notes. Keep all result conditions on identical decisions.
6. Compare inclusion/exclusion counts, label changes, length loss, split membership, control results and model errors against the provisional run. Do not infer improved model quality solely from a change in dataset composition. Keep the final test evaluation locked until the team fixes the pipeline; this development runner intentionally has no test-evaluation switch.

## Files to inspect

- `split_manifest.jsonl`: all 169 candidates, statuses, labels, families and split assignments; metadata only for the test period.
- `dataset_development.jsonl`: 105 train/validation decisions with FULL, MASKED and five RANDOM texts, counts and hashes.
- `data_provenance.json`, `execution.json`, `run_config.json`: input hashes, masks, package versions, settings and timings.
- `masking_log.jsonl`: removed spans and random-control indices; `MASKING_AUDIT_PACKET.md` / `MASKING_AUDIT_REVIEW.md`: pre-model audit.
- `metrics.json`: every C-grid result, fixed-C and selected-C tables, confusion matrices, counts and random-seed summary.
- `validation_predictions.jsonl`: case-level predictions and linear decision scores (scores are not calibrated probabilities).
- `token_length_statistics.json`, `dataset_summary.json`, `subgroup_metrics.json`: lengths, classes and coarse length-group analysis. Subgroup estimates are especially unstable at this sample size.
- `tfidf_features.json`: training-only coefficient summaries; `ERROR_REVIEW_PACKET.md`: all validation examples; `ERROR_OBSERVATIONS.md`: four initial assistant interpretations.
- `REPORT.md`, `plots/`, `provisional_A_results.ipynb`: shareable results, labeled as provisional.

Automated checks cover current-outcome removal versus historical citations, both classes, dissent/metadata boundaries, deterministic exact random-removal budgets, metric orientation, test/family/calibration exclusion, explicit family hints, same-case prediction coverage, metric recomputation and training-only vocabulary. They do not certify legal eligibility, annotation correctness or complete masking.

References for implementation: [scikit-learn TF-IDF](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html), [LinearSVC](https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVC.html), and the pinned LEGAL-BERT configuration. No extra hardware purchase is needed for this small frozen-feature trial; the completed run demonstrates feasibility on the current environment.
