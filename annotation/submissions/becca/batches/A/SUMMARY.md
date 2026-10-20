# Becca — batch A progress

Updated October 20, 2026. Branch: `annotations/becca-batch-a`.

## Status

First chunk completed: **A_001, 5 of 169 cases**. A_002–A_034 remain pending (164 cases). This is a partial checkpoint, not a complete or frozen round submission.

All five records are `llm_draft`; no human review or adjudication is claimed. Initial codebook/schema/prompt version 1.0.0 is used at the user's direction to start step 2. The team decision log still does not record a substantive rule freeze. Recheck affected drafts if the team changes the rules.

## Results

| Case ID | Case | Eligibility | Current disposition | Binary label | Attention |
|---|---|---|---|---|---|
| NY-4600405 | Patricola v. General Motors Corp. | Include | Affirmed | 0 | Storm abatement and creation/notice remain triable issues, not established negligence. |
| NY-4253165 | Keum Ok Han v. Kemp, Pin & Ski, LLC | Include | Reversed | 1 | Out-of-possession landlord established no snow-removal duty; reversal favors defendant. |
| NY-4849014 | Coreano v. 983 Tenants Corp. | Include | Affirmed | 0 | Entire appealed branch affirmed; “insofar as appealed from” does not make the disposition mixed. |
| NY-4259140 | Grossman v. TCR | Review | Affirmed | null | Club maintenance/control and fee-paying members are described, but private ownership/lease is not explicit. Resolve the private-premises boundary from supplied evidence under frozen rules. Majority affirms; dissent would reverse. |
| NY-4347986 | Slattery v. Tops Markets, LLC | Include | Reversed | 1 | Defendant's store and placement of its entrance rug support control. Alleged rug hazard was not found dangerous; expert affidavit rejected. Preserve source OCR. |

Draft totals: 4 included, 0 excluded, 1 unresolved. Included class counts: two 0 and two 1. These are annotation counts, not model performance or human-gold counts.

## Files and validation

- `drafts/A_001.draft-v1.json`: preserved first complete draft.
- `chunks/A_001.json`: selected chunk output, initially identical to the original draft.
- `chunks/A_001.validation.json`: passed with five records, no missing/extra chunk IDs and zero errors. Warnings correctly identify five LLM drafts and one unresolved review record.
- `checkpoint.jsonl`: five-record partial merge against the batch-A manifest.
- `checkpoint.jsonl.validation.json`: partial-coverage validation; missing IDs are expected until the other 33 chunks are finished.
- `checkpoint.summary.json`: descriptive counts from the supplied summary script. Its suggested audit ID is not a completed audit or a final sample drawn from a frozen full round. Preliminary periods are not approved evaluation splits.
- `progress.json`: exact completed and pending IDs for resumption.
- `prompts_used/`: resolved template prompts and actual session scope/provenance.
- `human_review_log.md`: pending human review.

The validator checks structure, exact source hashes/quotes, evidence references, all 19 issue topics, all 26 passages and basic consistency. Passing it does not establish semantic correctness.

## Independence and next step

No peer outputs, prior model labels, human calibration notes or comparison reports were consulted. Existing calibration records were not reused. The user's prior exposure to shared answers is unknown; record it before interpreting independent agreement.

Next input is `batches/A/chunks/A_002.md`. Continue with the same full-reading, draft-preservation and per-chunk validation procedure. Do not compare peer answers until the independent round is complete and frozen. All draft labels, especially the unresolved property question and proposed evaluation cases, require the specified human review.
