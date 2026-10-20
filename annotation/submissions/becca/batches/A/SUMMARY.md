# Becca — batch A progress

Updated October 20, 2026. Branch: `annotations/becca-batch-a`.

## Status

Completed: **A_001–A_004, 20 of 169 cases**. A_005–A_034 remain pending (149 cases). This is a partial checkpoint, not a complete or frozen round submission.

All twenty records are `llm_draft`; no human review or adjudication is claimed. Initial codebook/schema/prompt version 1.0.0 is used at the user's direction to start step 2 and continue chunk by chunk through A_004. The team decision log still does not record a substantive rule freeze. Recheck affected drafts if the team changes the rules.

## Results

| Case ID | Case | Eligibility | Current disposition | Binary label | Attention |
|---|---|---|---|---|---|
| NY-4600405 | Patricola v. General Motors Corp. | Include | Affirmed | 0 | Storm abatement and creation/notice remain triable issues, not established negligence. |
| NY-4253165 | Keum Ok Han v. Kemp, Pin & Ski, LLC | Include | Reversed | 1 | Out-of-possession landlord established no snow-removal duty; reversal favors defendant. |
| NY-4849014 | Coreano v. 983 Tenants Corp. | Include | Affirmed | 0 | Entire appealed branch affirmed; “insofar as appealed from” does not make the disposition mixed. |
| NY-4259140 | Grossman v. TCR | Review | Affirmed | null | Club maintenance/control and fee-paying members are described, but private ownership/lease is not explicit. Resolve the private-premises boundary from supplied evidence under frozen rules. Majority affirms; dissent would reverse. |
| NY-4347986 | Slattery v. Tops Markets, LLC | Include | Reversed | 1 | Defendant's store and placement of its entrance rug support control. Alleged rug hazard was not found dangerous; expert affidavit rejected. Preserve source OCR. |
| NY-5950199 | Checo v. 452-53rd St. Realty Corp. | Include | Affirmed | 0 | Defendant failed the initial creation/notice showing; no specific evidence types or conclusive notice finding are identified. |
| NY-7853716 | Kmitis v. Macy's, Inc. | Include | Affirmed | 0 | Affirms dismissal in defendants' favor; no triable issue on creation/notice. Accident date is explicit. |
| NY-3169329 | Monopoli v. Food Emporium, Inc. | Include | Affirmed | 0 | Fall was on a shopping-center ramp, not the parking lot. Lease allocation of control remains disputed between private owner and tenant. |
| NY-4803674 | Mister v. Mister | Include | Affirmed | 0 | Competing potential causes and notice remain factual issues; only month/year is given. Private home/control supported without assuming title ownership. |
| NY-4807631 | Leavy v. Key Food Stores Co-Operative, Inc. | Include | Affirmed | 0 | Jury could find employees created the display hazard. Obviousness does not eliminate the safe-maintenance duty. |
| NY-9430103 | Tafolla v. Aldrich Mgt. Co., LLC | Include | Affirmed | 0 | Negligence without proximate cause could be reconciled under a fair view of conflicting testimony. Substantive verdict review, not procedural-only. |
| NY-9422110 | Villanueva v. DJ's Intl. Buffet, Inc. | Review | Affirmed | null | Actual-case text states a stairway fall without establishing slip/trip mechanism. Review is not based merely on inability to prove a negligent cause. One order resolved two motions. |
| NY-2787559 | Mahai-Sharpe v. Riverbay Corp. | Review | Affirmed | null | Building attribution and janitorial work are described; private ownership/lease/use is not explicit. Retain property evidence for human interpretation. |
| NY-5934014 | Troutman v. 957 Nassau Road, LLC | Exclude | Reversed | null | Appellate analysis solely resolves improper juror replacement and leaves remaining contentions unaddressed. Reversal with a new trial is preserved; procedural-only scope excludes the binary label. |
| NY-5938121 | Tonkin v. Widewaters Lakewood Village Center Co. | Include | Affirmed | 0 | Pre-storm versus storm-time ice and lack of constructive notice were not established as a matter of law. |
| NY-2759462 | Nelson v. Bogopa Service Corp. | Exclude | Reversed | null | Appellate analysis addresses excluded evidence and prejudicial summation, without deciding negligence merits. Full reversal with new trial preserved. |
| NY-9389937 | Reid v. 645 LLC | Review | Affirmed | null | Private ownership/control of the exterior grocery-store platform is not established. Code compliance and fall-site causation findings remain recorded. |
| NY-2686408 | Mathis v. D.D. Dylan, LLC | Include | Affirmed | 0 | Box/shovel found both obvious and not inherently dangerous; expert report insufficient. Do not infer an unmade notice finding from nine-month duration. |
| NY-4388750 | Barron v. Eastern Athletic, Inc. | Include | Affirmed | 0 | Gym ownership explicit. Ordinary shower water, later soap allegation and insufficient engineer affidavit are distinguished. |
| NY-2825305 | Kyte v. Mid-Hudson Wendico, Inc. | Include | Affirmed | 0 | Reasonable door inspections supported lack of constructive notice. Failure of exclusive-control proof for res ipsa loquitur does not negate ordinary premises control. |

Draft totals: 14 included, 2 excluded, 4 unresolved. Included class counts: twelve 0 and two 1. These are annotation counts, not model performance or human-gold counts.

## Files and validation

- `drafts/A_001.draft-v1.json`: preserved first complete draft.
- `chunks/A_001.json`: selected chunk output, initially identical to the original draft.
- `chunks/A_001.validation.json`: passed with five records, no missing/extra chunk IDs and zero errors. Warnings correctly identify five LLM drafts and one unresolved review record.
- `drafts/A_002.draft-v1.json`: preserved first complete A_002 draft.
- `chunks/A_002.json`: selected A_002 output, initially identical to its original draft.
- `chunks/A_002.validation.json`: passed with five records, no missing/extra chunk IDs and zero errors. Warnings identify the five LLM drafts.
- `drafts/A_003.draft-v1.json`: preserved first complete A_003 draft.
- `chunks/A_003.json`: selected A_003 output. Tonkin's factual summary was corrected to attribute submissions specifically to defendants; its `supersedes` identifies the original record. No label/evidence changes; the other four draft records are identical.
- `chunks/A_003.validation.json`: passed with five records, no missing/extra chunk IDs and zero errors. Warnings identify five LLM drafts and two unresolved review records.
- `drafts/A_004.draft-v1.json`: preserved first complete A_004 draft.
- `chunks/A_004.json`: selected A_004 output, identical to the original draft.
- `chunks/A_004.validation.json`: passed with five records, no missing/extra chunk IDs and zero errors. Warnings identify five LLM drafts and one unresolved review record.
- `checkpoint.jsonl`: twenty-record partial merge against the batch-A manifest. Supersedes the fifteen-record checkpoint preserved in commit `5607224`; existing A_001–A_003 records are unchanged.
- `checkpoint.jsonl.validation.json`: passed partial-coverage validation; 149 missing IDs are expected until the other 30 chunks are finished.
- `checkpoint.summary.json`: descriptive counts from the supplied summary script. Its suggested audit ID is not a completed audit or a final sample drawn from a frozen full round. Preliminary periods are not approved evaluation splits.
- `progress.json`: exact completed and pending IDs for resumption.
- `prompts_used/`: resolved template prompts and actual session scope/provenance.
- `human_review_log.md`: pending human review.

The validator checks structure, exact source hashes/quotes, evidence references, all 19 issue topics per case, all 84 passages across the four chunks and basic consistency. Passing it does not establish semantic correctness.

## Independence and next step

No peer outputs, prior model labels, human calibration notes or comparison reports were consulted. Existing calibration records were not reused. The user's prior exposure to shared answers is unknown; record it before interpreting independent agreement.

Next input is `batches/A/chunks/A_005.md`. Continue with the same full-reading, draft-preservation and per-chunk validation procedure. Do not compare peer answers until the independent round is complete and frozen. All draft labels, including exclusions, unresolved questions and proposed evaluation cases, require the specified human review.
