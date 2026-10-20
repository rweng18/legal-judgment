# Becca — batch A progress

Updated October 20, 2026. Branch: `annotations/becca-batch-a`.

## Status

Completed: **A_001–A_002, 10 of 169 cases**. A_003–A_034 remain pending (159 cases). This is a partial checkpoint, not a complete or frozen round submission.

All ten records are `llm_draft`; no human review or adjudication is claimed. Initial codebook/schema/prompt version 1.0.0 is used at the user's direction to start step 2 and continue with A_002. The team decision log still does not record a substantive rule freeze. Recheck affected drafts if the team changes the rules.

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

Draft totals: 9 included, 0 excluded, 1 unresolved. Included class counts: seven 0 and two 1. These are annotation counts, not model performance or human-gold counts.

## Files and validation

- `drafts/A_001.draft-v1.json`: preserved first complete draft.
- `chunks/A_001.json`: selected chunk output, initially identical to the original draft.
- `chunks/A_001.validation.json`: passed with five records, no missing/extra chunk IDs and zero errors. Warnings correctly identify five LLM drafts and one unresolved review record.
- `drafts/A_002.draft-v1.json`: preserved first complete A_002 draft.
- `chunks/A_002.json`: selected A_002 output, initially identical to its original draft.
- `chunks/A_002.validation.json`: passed with five records, no missing/extra chunk IDs and zero errors. Warnings identify the five LLM drafts.
- `checkpoint.jsonl`: ten-record partial merge against the batch-A manifest. Supersedes the five-record checkpoint preserved in commit `31d1d69`; existing A_001 annotations are unchanged.
- `checkpoint.jsonl.validation.json`: passed partial-coverage validation; 159 missing IDs are expected until the other 32 chunks are finished.
- `checkpoint.summary.json`: descriptive counts from the supplied summary script. Its suggested audit ID is not a completed audit or a final sample drawn from a frozen full round. Preliminary periods are not approved evaluation splits.
- `progress.json`: exact completed and pending IDs for resumption.
- `prompts_used/`: resolved template prompts and actual session scope/provenance.
- `human_review_log.md`: pending human review.

The validator checks structure, exact source hashes/quotes, evidence references, all 19 issue topics per case, all 46 passages across the two chunks and basic consistency. Passing it does not establish semantic correctness.

## Independence and next step

No peer outputs, prior model labels, human calibration notes or comparison reports were consulted. Existing calibration records were not reused. The user's prior exposure to shared answers is unknown; record it before interpreting independent agreement.

Next input is `batches/A/chunks/A_003.md`. Continue with the same full-reading, draft-preservation and per-chunk validation procedure. Do not compare peer answers until the independent round is complete and frozen. All draft labels, especially the unresolved property question and proposed evaluation cases, require the specified human review.
