# Becca — batch B progress

Updated October 28, 2026. Branch: `annotations/becca-batch-b`. Started from latest main revision `ecca2a4` at the user’s direction to begin batch B in small chunks.

## Status

Completed: **B_001–B_004, 20 of 169 cases**. B_005–B_034 remain pending (149 cases). This is a partial checkpoint, not a complete or frozen round submission.

All 20 records are `llm_draft`; no human review or adjudication is claimed. Initial codebook/schema/prompt version 1.0.0 remains in use. The central DECISIONS.md contains no substantive replacement rule version or team freeze. The user explicitly authorized B work; A comparison/MVP documentation was not treated as a new B labeling rule.

## Results

| Case ID | Case | Eligibility | Current disposition | Binary label | Attention |
|---|---|---|---|---|---|
| NY-2766601 | Hernandez v. BP America, Inc. | Include | Affirmed | 0 | Owned premises; successful noncreation/notice showing. Painted line during rain, no inferred puddle or business subtype. |
| NY-4791129 | Colini v. Stino, Inc. | Include | Affirmed | 0 | Foot caught in carpet, but negligent cause speculative. Law-of-case issue is ancillary to merits. |
| NY-4546815 | Elassad v. Nastasi | Review | Affirmed | null | Home ownership does not settle front-path boundary. Black ice and above-freezing weather are distinct evidence statements. |
| NY-4613124 | Parchment v. TJX Cos., Inc. | Exclude | Affirmed | null | Procedural-only charge and cross-examination rulings; no appellate negligence-merits analysis. |
| NY-2800741 | Mogan v. Dame Russell Physical Therapy, PLLC | Review | Affirmed | null | Institutional ownership and supervision/premises scope unresolved. Physical trip and substantive supervision ruling are clear. |
| NY-5947900 | Patrick v. Costco Wholesale Corp. | Include | Reversed | 1 | Cause unidentified; ice cream observed nearby 20 minutes afterward does not establish causation. |
| NY-4619740 | Yarosh v. Oceana Holding Corp. | Include | Reversed | 1 | Noncreation and lack of notice established for vestibule snow; no duty to continuously mop or mat every floor. |
| NY-6119453 | Boyle v. Pottery Barn Outlet | Include | Affirmed | 0 | Box condition both open and obvious and not inherently dangerous; engineer affidavit insufficient. |
| NY-5312913 | Monaco v. Russillo | Include | Affirmed | 0 | Common-law noncreation/notice and separate GML § 205-e lack-of-culpability grounds; private home despite police response. |
| NY-4337765 | Stevens v. Benjamin | Include | Affirmed | 0 | Defendants failed to address specific code allegations; applicability and violation not conclusively established. |
| NY-4402418 | Andersen v. El Triunfo Laundromat Corp. | Include | Affirmed | 0 | Noncreation and lack of actual notice established prima facie; lack of constructive notice and speculative causation not established. |
| NY-4617802 | Colon v. New York Mercantile Exch., Inc. | Include | Affirmed | 0 | C&W’s submission of plaintiff’s deposition failed to establish noncreation; hallway fall, not expressly on loading dock. |
| NY-5950295 | Willstein v. Waldbaum, Inc. | Include | Affirmed | 0 | Neither defendant met its constructive-notice burden; two appeals concern one order. |
| NY-9355448 | Francisco v. Pulla | Include | Affirmed | 0 | Photos/testimony failed to establish absence of danger or triviality; notice not pursued on appeal. |
| NY-4725572 | Glosek v. Bella Pizza | Include | Reversed | 1 | Rug placement shown not dangerous; no triable issue, and complaint dismissed. |
| NY-5948742 | Hayes v. Norstar Apartments, LLC | Include | Affirmed | 0 | Storm established, but preexisting ice and fall surface remain triable; favors plaintiff. |
| NY-4387362 | Depczynski v. Mermigas | Include | Affirmed | 0 | Noncreation/constructive-notice burden unmet; inspection-duty error does not change result. |
| NY-9422144 | Cashwell v. Stop & Shop Supermarket Co., LLC | Include | Affirmed | 0 | Plaintiffs’ frozen-food leak theory speculative; their liability motion denied. |
| NY-3202838 | Micek v. Greek Orthodox Church of Our Savior | Include | Affirmed | 0 | Private church premises; caterers established lack of premises relationship and noncreation. |
| NY-8511901 | Fuentes v. Fisher | Include | Affirmed | 0 | Out-of-possession owner established no maintenance duty; actual stair hazard unstated. |

Draft totals: 17 included, 1 excluded, 2 unresolved. Included class counts: fourteen 0 and three 1. These are annotation counts, not model performance or human-gold counts.

## Files and validation

- `drafts/B_001.draft-v1.json`: preserved first complete draft.
- `chunks/B_001.json`: selected output, identical to the original draft.
- `chunks/B_001.validation.json`: five records, exact chunk coverage and zero errors; expected warnings for five LLM drafts and two unresolved review records.
- `drafts/B_002.draft-v1.json`: preserved first complete B_002 draft.
- `chunks/B_002.json`: selected B_002 output, identical to its original draft.
- `chunks/B_002.validation.json`: five records, exact chunk coverage and zero errors; expected warnings for five LLM drafts.
- `drafts/B_003.draft-v1.json`: preserved first complete B_003 draft.
- `chunks/B_003.json`: selected B_003 output, identical to its original draft.
- `chunks/B_003.validation.json`: five records, exact chunk coverage and zero errors; expected warnings for five LLM drafts.
- `drafts/B_004.draft-v1.json`: preserved first complete B_004 draft.
- `chunks/B_004.json`: selected B_004 output, identical to its original draft.
- `chunks/B_004.validation.json`: five records, exact coverage and zero errors; expected LLM-draft warnings.
- `checkpoint.jsonl`: 20-record partial merge against the batch B manifest, including review and excluded records. Supersedes the 15-record checkpoint preserved in commit `b0d8c22`; B_001–B_003 records are unchanged.
- `checkpoint.jsonl.validation.json`: passed partial validation with zero errors; 149 missing IDs are expected until the remaining 30 chunks are finished.
- `checkpoint.summary.json`: descriptive counts and provisional audit candidates. No human audit has been performed and no complete round is frozen.
- `progress.json`: exact completed/pending IDs, next chunk, selected-output hash and shared-calibration overlap IDs.
- `prompts_used/`: resolved prompts and actual scope/provenance.
- `human_review_log.md`: pending human review and case-specific assistant priorities.

Validation checks source hashes, exact quotations and offsets, evidence references, all 19 issue topics per case, all 69 source passages across four chunks and basic consistency. It does not establish semantic correctness.

## Independence and next step

No peer B labels, previous automated labels for these cases, independent human notes or outside case facts were consulted. No B_001–B_004 case overlaps the shared calibration manifest. Four later B cases do overlap (NY-2993705, NY-3206955, NY-4310325 and NY-5960096); handle provenance/exposure explicitly when reached and do not silently count reused work as fresh independence. Prior human exposure is unknown. Sixteen completed decisions date to the preliminary training period. Monaco (NY-5312913), Francisco (NY-9355448) and Fuentes (NY-8511901) are preliminary validation-period cases; Cashwell (NY-9422144) is preliminary test-period. All require independent human eligibility/outcome review before human-gold evaluation use. No rules were tuned from held-out cases.

Next input is `batches/B/chunks/B_005.md`. Continue full reading, original-draft preservation, exact evidence, validation and local checkpoint commits. Push when requested. At completion, merge exactly the 169 expected records, preserve and hash the complete draft before peer comparison, then compare/review B. All labels, exclusions and unresolved questions require the specified human review.
