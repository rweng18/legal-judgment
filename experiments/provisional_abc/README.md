# Combined A-C provisional development workspace

Prepared on November 18, 2026 on `experiments/provisional-abc`. **Majority, TF-IDF logistic regression, linear SVM and frozen LEGAL-BERT + LR are complete.** This workspace preserves the completed A and B experiments and uses the latest locally available prepared C package. The dataset release remains a preparation-only snapshot; model runs are saved separately under `runs/`.

## Complete comparison

Start with the [complete report](runs/abc_complete_provisional_v1/REPORT.md), [reporting tables](runs/abc_complete_provisional_v1/REPORTING.md) or [executed notebook](runs/abc_complete_provisional_v1/A_C_complete_results.ipynb). All eight conditions use the same 42 development cases and the original three family-grouped training folds. C is selected independently for each learned model using MASKED training folds, then held fixed across FULL/MASKED.

| Model | Selected C | FULL balanced accuracy | MASKED balanced accuracy |
|---|---:|---:|---:|
| Majority | — | 50.00% | 50.00% |
| TF-IDF LR | 10 | 82.12% | 53.65% |
| TF-IDF SVM | 10 | 88.12% | 50.71% |
| Frozen LEGAL-BERT + LR | 0.1 | 88.12% | 50.35% |

The SVM uses the same TF-IDF settings as LR. The encoder remains frozen at the proposal's pinned revision, processes every 510-content-token chunk, excludes specials/padding from pooling and weights chunks by content count. StandardScaler and LR fit within training folds only. Both 321×768 embedding matrices and case-ID/text-hash indexes are included in the complete run. The shared vector cache is under `../provisional_b/.cache/vectors`; the pinned checkpoint cache is under `../provisional_b/.cache/huggingface`. Exact B/C token/chunk counts match their upstream reports. All 336 prediction rows, including failures, are retained.

The [SVM stage](runs/abc_svm_provisional_v1/REPORT.md) preserves the lexical checkpoint before encoder execution. Prior majority/LR predictions and selections reproduced exactly; the complete run also reproduced the SVM stage exactly. Source hashes, software versions, effective class weights, checkpoint checksums and cache-reload verification are saved. Ten extension/shared checks cover saved-fold reuse, training-only transforms, MASKED-only selection, chunk boundaries, pooling and protocol guards. The notebook independently checks all metrics, case IDs, confusion matrices and embedding checksums.

With the pinned environment and checkpoint available, reproduce from this directory under fresh output names:

```sh
python run_comparison.py inputs/abc_provisional_v1/release.json runs/abc_logistic_provisional_v1 runs/abc_svm_reproduction --lexical-only
HF_HUB_OFFLINE=1 python run_comparison.py inputs/abc_provisional_v1/release.json runs/abc_svm_reproduction runs/abc_complete_reproduction
python comparison_notebook.py runs/abc_complete_reproduction
```

These remain provisional development results. Masked balanced accuracies are close to the majority baseline on this sample. The FULL/MASKED contrast is descriptive and does not isolate the causal effect of a specific removed phrase. No final-test evaluation, label correction or masking revision was performed.

The [A-C development error analysis](runs/abc_complete_provisional_v1/error_analysis_v1/ERROR_ANALYSIS.md) inspects eight opinions across all three batches, including six disagreement cases, a short shared learned-model failure and a long correct comparison case. It documents direct and indirect residual outcome cues, procedural-history ambiguity, sparse factual narratives and a five-chunk error. One C case has identical FULL/MASKED text and encoder vectors but different fitted-classifier predictions. Exact evidence offsets, copied predictions, the full 42-case diagnostic inventory and a preservation audit accompany the report. All original run and dataset files remain unchanged.

## Completed logistic-regression comparison

See the [results report](runs/abc_logistic_provisional_v1/REPORT.md), [full reporting tables](runs/abc_logistic_provisional_v1/REPORTING.md), and [executed results notebook](runs/abc_logistic_provisional_v1/A_C_logistic_results.ipynb). MASKED training-only selection chose C=10 using three grouped folds. FULL/MASKED use that same C and the same 42 development cases.

| Model | Text | Accuracy | Balanced accuracy | Macro F1 |
|---|---|---:|---:|---:|
| Majority | FULL and MASKED | 59.52% | 50.00% | 0.3731 |
| TF-IDF LR | FULL | 80.95% | 82.12% | 0.8078 |
| TF-IDF LR | MASKED | 57.14% | 53.65% | 0.5333 |

Word unigrams/bigrams, min_df=2, at most 30,000 features, L2-normalized TF-IDF, L2 logistic regression and balanced training-class weights are fitted inside each training pipeline. All 168 prediction rows are retained. No test predictions or encoder computations were performed.

Use the existing pinned environment from `../provisional_b/.venv`, or install the completed run's `requirements-lock.txt` in Python 3.11. From this directory:

```sh
python -m unittest -v test_prepare test_logistic
python run_logistic.py inputs/abc_provisional_v1/release.json runs/abc_logistic_reproduction
python results_notebook.py runs/abc_logistic_reproduction
```

Choose fresh run directories. Eight checks cover data integrity, family leakage, held-out vocabulary/IDF, balanced weights and MASKED-only selection. The executed notebook independently recomputes saved prediction metrics. No source annotations, masks or earlier experiment results are changed.

## Authorization and review status

[assumptions.json](assumptions.json) records the user's explicit instruction to use Batch C provisionally and the earlier Batch B review assumption. A retains its existing `team_reviewed` status. B and C retain `pending_human_review`; C's underlying reviewer submissions remain drafts. The combined release is `provisional_user_authorized`, not a frozen human-gold release.

A comes from the current **reviewed A MVP**, not the older provisional A experiment. B uses the supplied draft-label field for its 112 prepared cases. C's eligibility audit contains no outcome-label column, so preparation checks the three saved reviewer submissions and exports their per-case label votes. All three agree on a binary label for each of the 107 prepared C cases. Missing labels, disagreements or mismatched source hashes stop preparation; none were silently resolved.

## Combined dataset

The release is in [inputs/abc_provisional_v1](inputs/abc_provisional_v1). Every upstream development case and its exact FULL/MASKED strings is retained. No case is relabeled, dropped or added to improve model scores. Upstream selection exclusions and A's unresolved Sodhi hold remain outside development.

| Batch | Training 0 | Training 1 | Training total | Development 0 | Development 1 | Development total |
|---|---:|---:|---:|---:|---:|---:|
| A | 59 | 27 | 86 | 8 | 8 | 16 |
| B | 64 | 33 | 97 | 12 | 3 | 15 |
| C | 58 | 38 | 96 | 5 | 6 | 11 |
| **Total** | **181** | **98** | **279** | **25** | **17** | **42** |

Labels: 0 affirmed, 1 reversed/vacated. Training covers 2010–2020; development evaluation covers 2021–2022. The 2023–2024 period remains reserved. Candidate metadata for all 506 source cases is recorded, but test texts and test labels are not exported. Here “development total” in the table means the validation split; `development.jsonl` contains both training and validation, 321 cases in total.

## Families and known limitations

Preparation combines the existing global family manifest, per-batch family memberships, source hints and exact-text duplicate links. It assigns a common `ABC-FAM-…` ID without prefixing by batch, so related cases in different batches stay together in future cross-validation. The combined manifest retains each upstream family identifier separately.

- Eight linked family groups span batches; five have multiple included development cases. All eight are within training. No included family crosses chronological periods, and no known calibration family enters validation.
- Existing unresolved companion warnings remain for **NY-4665270** and **NY-4855957**. Their upstream inclusion is preserved and flagged; neither gains a new family-review approval.
- Existing candidate family links remain provisional. This union is not a new legal adjudication or exhaustive family search. Identical texts are grouped rather than silently removed; counts remain per decision.
- A uses its existing `masker_v2`; B/C use `mask_v2_abbreviation_boundary_pre_review`. Exact strings are reused rather than claiming a single harmonized masking implementation. Batch-specific preprocessing is a potential confound.
- A and B development cases have already been used in model evaluation and error inspection. Combined validation is another development comparison, not an untouched final test.

## Files and reproducibility

- `development.jsonl`: exactly 321 FULL/MASKED text pairs, with IDs, batches, dates and periods; no annotations are appended to features.
- `manifest.jsonl`: all 506 candidate IDs, original source statuses, development labels, combined family IDs, calibration/companion flags and per-text hashes. Non-development labels are null.
- `C_label_provenance.jsonl`: the three saved reviewer votes and source statuses for the 107 included C cases.
- `release.json`: version, authorization status, exact source/output checksums, preparation code hash and the cached Yinkui C Git revision. It intentionally does not claim a human-reviewed freeze.
- `assumptions.json`: a release-local copy of the user-authorized assumptions.
- `family_audit.json`, `class_counts.csv`, `summary.json`: retained family links, cross-batch grouping, outstanding warnings and counts.
- `provisional_abc.ipynb`: unexecuted dataset inspection notebook; no training cells.

From this directory, validate the delivered release with `python -m unittest -v test_prepare`. Rebuild into a **fresh** directory with `python prepare.py --out inputs/abc_provisional_reproduction`. Existing destinations are rejected. The script needs only Python's standard library and Git. It makes no network calls, modifies no upstream annotation files, and fits no models.

Rebuilding requires the source files at their saved versions and Yinkui's C annotation object at commit `87f7771b01cb8fcd75860e240c0b075a09bb3f61`. That object is already available locally; a fresh clone may need the `annotations/yinkui-batch-c` branch fetched. The saved release can be loaded and verified without that Git object because it includes the derived C vote provenance. `load_release` in `prepare.py` verifies output hashes and joins texts to metadata for later experiment code.

The completed runners reuse the B experiment's model and reporting functions with this workspace's A-C loader. The old B+C loader intentionally remains unchanged and does not accept the A-C provisional schema. The SVM and encoder stages reuse the saved combined family folds and evaluation cases rather than constructing new splits.
