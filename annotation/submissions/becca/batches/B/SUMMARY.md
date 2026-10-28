# Becca — batch B progress

Updated October 28, 2026. Branch: `annotations/becca-batch-b`. Started from latest main revision `ecca2a4` at the user’s direction to begin batch B in small chunks.

## Status

Completed: **B_001, 5 of 169 cases**. B_002–B_034 remain pending (164 cases). This is a partial checkpoint, not a complete or frozen round submission.

All 5 records are `llm_draft`; no human review or adjudication is claimed. Initial codebook/schema/prompt version 1.0.0 remains in use. The central DECISIONS.md contains no substantive replacement rule version or team freeze. The user explicitly authorized B work; A comparison/MVP documentation was not treated as a new B labeling rule.

## Results

| Case ID | Case | Eligibility | Current disposition | Binary label | Attention |
|---|---|---|---|---|---|
| NY-2766601 | Hernandez v. BP America, Inc. | Include | Affirmed | 0 | Owned premises; successful noncreation/notice showing. Painted line during rain, no inferred puddle or business subtype. |
| NY-4791129 | Colini v. Stino, Inc. | Include | Affirmed | 0 | Foot caught in carpet, but negligent cause speculative. Law-of-case issue is ancillary to merits. |
| NY-4546815 | Elassad v. Nastasi | Review | Affirmed | null | Home ownership does not settle front-path boundary. Black ice and above-freezing weather are distinct evidence statements. |
| NY-4613124 | Parchment v. TJX Cos., Inc. | Exclude | Affirmed | null | Procedural-only charge and cross-examination rulings; no appellate negligence-merits analysis. |
| NY-2800741 | Mogan v. Dame Russell Physical Therapy, PLLC | Review | Affirmed | null | Institutional ownership and supervision/premises scope unresolved. Physical trip and substantive supervision ruling are clear. |

Draft totals: 2 included, 1 excluded, 2 unresolved. Included class counts: two 0 and zero 1. These are annotation counts, not model performance or human-gold counts.

## Files and validation

- `drafts/B_001.draft-v1.json`: preserved first complete draft.
- `chunks/B_001.json`: selected output, identical to the original draft.
- `chunks/B_001.validation.json`: five records, exact chunk coverage and zero errors; expected warnings for five LLM drafts and two unresolved review records.
- `checkpoint.jsonl`: five-record partial merge against the batch B manifest, including review and excluded records.
- `checkpoint.jsonl.validation.json`: passed partial validation with zero errors; 164 missing IDs are expected until the remaining 33 chunks are finished.
- `checkpoint.summary.json`: descriptive counts and provisional audit candidates. No human audit has been performed and no complete round is frozen.
- `progress.json`: exact completed/pending IDs, next chunk, selected-output hash and shared-calibration overlap IDs.
- `prompts_used/`: resolved prompts and actual scope/provenance.
- `human_review_log.md`: pending human review and case-specific assistant priorities.

Validation checks source hashes, exact quotations and offsets, evidence references, all 19 issue topics per case, all 19 source passages and basic consistency. It does not establish semantic correctness.

## Independence and next step

No peer B labels, previous automated labels for these cases, independent human notes or outside case facts were consulted. No B_001 case overlaps the shared calibration manifest. Four later B cases do overlap (NY-2993705, NY-3206955, NY-4310325 and NY-5960096); handle provenance/exposure explicitly when reached and do not silently count reused work as fresh independence. Prior human exposure is unknown. All five B_001 decisions date to the preliminary training period; this does not make the drafts human-gold training labels.

Next input is `batches/B/chunks/B_002.md`. Continue full reading, original-draft preservation, exact evidence, validation and local checkpoint commits. Push when requested. At completion, merge exactly the 169 expected records, preserve and hash the complete draft before peer comparison, then compare/review B. All labels, exclusions and unresolved questions require the specified human review.
