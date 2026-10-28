# Becca — batch B progress

Completed **B_001–B_006: 30/169 cases**; 139 pending. Next: **B_007**. Branch `annotations/becca-batch-b`, started from `ecca2a4`. Partial checkpoint; no complete round freeze.

All records remain llm_draft. Initial codebook/schema/prompt 1.0.0; no human review, adjudication or substantive team rule freeze is claimed.

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
| NY-5937355 | Miskanic v. Roller Jam USA, Inc. | Include | Affirmed | 0 | Ramp defect/notice burden unmet; concealed or increased risk remains triable. |
| NY-5994504 | Kalthoff v. Arrowood Indemnity Co. | Exclude | Reversed | null | Current action resolves insurance coverage, not negligence merits. |
| NY-4306359 | Mann v. Wegmans Food Markets, Inc. | Include | Reversed | 1 | Storm defense established; lull and preexisting-ice theories did not raise an issue. |
| NY-6475974 | DiScalo v. Mannix Family Mkt. | Include | Reversed | 1 | Flattened box both open and obvious and not inherently dangerous. |
| NY-6473777 | Everett v. CMI Servs. Corp. | Include | Affirmed | 0 | Job-hazard, obviousness and workers’ compensation defenses not established. |
| NY-4304286 | Wintermute | Exclude | Reversed | null | Procedural-only witness exclusion; reversed/null, new trial does not decide negligence. |
| NY-5934656 | Mauge | Include | Affirmed | 0 | Restaurant control; noncreation/notice established, general grease awareness not recurrent-condition notice. |
| NY-4654580 | Padilla | Review | Reversed | null | Review walkway boundary; causation showing failed, both motions in one order reversed. |
| NY-4387315 | Lingenfelter | Include | Reversed | 1 | All Espinal exceptions rejected; direct negligence plus ancillary cross claim, full reversal. |
| NY-6454036 | Padel | Review | Reversed | null | Review private status/exterior-step control; granted reargument reaches substantive constructive notice. |

Totals: 23 included, 3 excluded, 4 unresolved. Included labels: 17 zero, 6 one. These are draft counts, not model performance.

`drafts/` preserves original outputs; `chunks/` contains selected outputs and validation reports; `prompts_used/` records prompts and provenance. `checkpoint.jsonl` merges only selected chunks. It supersedes the checkpoint in `72813b3`; all earlier chunk artifacts are unchanged. `progress.json` tracks exact IDs and hashes; `checkpoint.summary.json` provides descriptive counts and provisional audit candidates, not a completed audit.

Validation passed: 30 unique records, 119 passages, all 19 issues per case, source hashes, exact quotations/offsets and references. 139 missing IDs are expected in this partial batch. Validation does not establish semantic correctness; see `human_review_log.md` for pending review.

No peer labels or outside case facts consulted. Completed IDs do not overlap calibration. Later overlap IDs remain in progress.json and require explicit exposure handling. Prior human exposure is unknown. Validation/test-period cases use unchanged rules and require independent human review before evaluation use; no held-out rule tuning occurred.

Continue with `batches/B/chunks/B_007.md`. Local commits; push when requested. At completion merge all 169 records, preserve/hash the complete draft before peer comparison, then review B.
