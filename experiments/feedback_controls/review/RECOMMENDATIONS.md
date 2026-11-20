# B/C review decisions and recommendations — November 19, 2026

**Subsequent decision:** The user approved these recommendations, then confirmed review by Yinkui Yu dated November 19 with no additional family corrections. The executed sensitivities and final reviewed release are documented in `../README.md`. This file preserves the evidence and recommendation state before that approval.

Evidence snapshot: repository commit `0837ed2bf4c1d3abc7fd3b0ea652f5a5461894db`.
The recommendations below are assistant review of the frozen sources, not newly supplied human adjudication. No original annotations, labels, masks, splits, or published results have been overwritten.

## Decision supplied by the user

“For disagreed cases, recover none.” Exclude all 30 B and 24 C eligibility disagreements from modeling. The exact 54 IDs and their audit sources are recorded in `user_exclusion_decisions_2026-11-19.json`. None is in the existing 321-case development release (279 training, 42 validation), so this decision alone changes no development counts. This conservative exclusion does not establish that all 54 are legally outside the project scope. Keep unanimous `review` cases outside the binary dataset as well.

The user reported that human review is complete. We still need the resulting case-level decisions or an explicit adoption of a precisely identified manifest to replace pending-review fields honestly. This document does not attribute its recommendations to Hayden or another human.

## Duplicate records and related appeals

Directly compared the complete frozen source text of both records in each of the following five pairs. They reproduce the same underlying decision, including facts, procedural order and substantive discussion, with publication, citation, header or OCR differences. These are not five pairs of separate appeals.

| Decision | Records | Recommended treatment |
|---|---|---|
| Wintermute | NY-4304286 / NY-6207931 | Both already outside development; retain neither as a model row. Preserve the alias link. |
| Alvarado | NY-4304440 / NY-6207337 | Keep the already-included NY-6207337. Do not recover NY-4304440. |
| Seferagic | NY-4306330 / NY-6111859 | Keep the already-included NY-4306330. Do not recover NY-6111859. |
| Mann | NY-4306359 / NY-6112018 | Both currently included. Recommend retaining NY-4306359 and recording NY-6112018 as its duplicate alias. Both express the same reversal; retain label 1. |
| Lingenfelter | NY-4387315 / NY-6235219 | Keep the already-included NY-4387315. Do not recover NY-6235219. |

For Mann, the suggested retained record has the docket and a complete, readable opinion; the alternate adds reporter formatting and citation years, rather than another observation. Removing that duplicate alone would give 320 development rows, but this is **not a final unique-case count**: other A/C family candidates remain to be checked. The combined family audit contains additional pairs beyond this B/C review queue.

Do not group Arbit/Patrick or Clark/Loper merely because the defendant names resemble each other. The candidate metadata show different plaintiffs, dates and, where available, dockets. Keep them separate unless there is positive evidence of the same underlying litigation.

For genuinely separate appeals from one lawsuit, retain eligible decisions but assign one family ID and keep the entire family in the same evaluation split and cross-validation fold. For duplicate publications of one decision, use one model row and preserve both source IDs in an alias table. Family grouping alone avoids split leakage but does not remove duplicate weighting within training.

Hartnett (NY-4665270) discusses two appeals; Gould (NY-4855957) is captioned Appeal No. 2. Their complete frozen opinions were read. A caption search of all 506 source records finds no second Hartnett or Gould record. Recommend retaining the present rows, recording their companion-appeal warning and checking any later additions against their family IDs. Absence of a second caption match is not proof that every possible related record has been found.

## Four flagged masking cases

Read the full cleaned opinions, their MASKED versions and the exact deleted spans. All four are training cases: two label 0 and two label 1. They provide the requested two-class training audit, but do not replace the separate two-class validation audit.

| Case | Finding | Recommendation |
|---|---|---|
| B: NY-4509516 | The long deletion quotes Harvey's storm-in-progress burden rule and its citations. The matcher treats “Supreme Court properly shifted” inside the quotation as a current-appeal disposition. | Restore that quoted rule and citations. Continue removing the present appeal's explicit disposition. Preserve factual and evidentiary reasoning. |
| B: NY-5950295 | A sentence-boundary error joins “The Supreme Court denied the motions, and we affirm.” to the following quoted general notice rule, deleting both. | Separate the spans; remove the current “we affirm” language while retaining prior procedural history and the quoted rule with its citations. |
| C: NY-4427636 | The opening procedural-history sentence ending in “LLC.” is joined to “Ordered that the order is reversed…”. Both disappear together. | Restore the opening history and remove the operative appellate order separately. The closing explicit statement that the lower court should have denied the motion remains a disposition cue to mask. |
| C: NY-5980564 | The long deletion is the closing statement that the lower court should have granted summary judgment followed by a long string of authorities. The preceding factual and evidentiary reasoning remains. | Accept deletion of the explicit current-appeal conclusion. Prefer preserving the cited-authority span under a consistent citation-preservation policy; the existing deletion is defensible but loses precedent information. |

Keep all four cases; the problem is mask precision, not grounds to discard the opinions. These are recommendations for a versioned masking revision, not changes already applied to the frozen experiment.

Implement any revision as a general boundary/quotation/span rule rather than case-ID exceptions. Audit remaining current-appeal cues as well as over-deletions; fixing the four flags alone cannot establish that MASKED is outcome-free. Preserve the current baseline for reproduction, compare the revised mask on the same development cases, and recompute each matched-random-removal budget from the corresponding mask. Do not revise rules in response to test predictions.

## Final-test readiness

The reserved metadata contain 69 records in 2023–2024. The current upstream selection identifies 17 A assigned records, 13 B included records and 20 C included records: **50 candidate test records**, not 50 certified unique, reviewed test cases. Other reserved records remain excluded, disputed or unresolved. Test labels and texts were not opened for this recommendations audit, and no test predictions were run.

Recommend freezing a case-level manifest before final evaluation with:

- Case ID and source-text hash; eligibility decision and final binary label (0 affirmed, 1 reversed/vacated) under the agreed codebook.
- Actual reviewer and review date or existing review-log reference; unresolved or mixed outcomes excluded under the codebook.
- Canonical record/duplicate alias, family ID and split assignment, with no train/test family overlap.
- The preprocessing version and a record of any prior modeling exposure.

An already-completed review does not need to be repeated. Supply its decisions, or explicitly adopt the exact existing eligible IDs and their labels after checking that they match the completed review. Freeze preprocessing and classifier choices using development data, then run the agreed final comparisons once on the same test cases. Report accuracy, balanced accuracy, macro F1, confusion matrices and class counts with uncertainty appropriate to the small test set. Do not call unanimous LLM agreement human-reviewed ground truth by itself.

## Experiment continuity

Use the unchanged 321-case development release for the instructor-requested matched-control experiment so that its comparison with the earlier results is interpretable. Treat approved deduplication and mask corrections as a separate, versioned data-quality sensitivity run; report changed case counts explicitly. The final dataset should use the resolved duplicate and masking policy, with no recovery of the 54 disputed records.
