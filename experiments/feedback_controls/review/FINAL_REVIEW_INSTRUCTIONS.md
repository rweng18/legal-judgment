# Final review handoff: what to do

**Completed November 20:** Yinkui Yu confirmed review dated November 19, with no additional family corrections. The recorded interpretation accepts the supplied review lists with their existing agreed labels. See `../final/inputs/human_review_confirmation.json` and `../final/inputs/reviewed_manifest.jsonl`. The instructions below are preserved as the historical handoff, not another outstanding review request. The final test has since been evaluated.

The experiments can continue while this is completed. Use your existing human review; do not repeat annotation simply because repository status fields are old.

## 1. Point to the actual reviewed decisions

If Hayden already saved the final decisions, send the file or GitHub link and the reviewer name(s) and actual review date. I will map its columns and validate it. This is the easiest route; no need to fill another template.

## 2. Otherwise, confirm the development list

Open `development_acceptance_template.json`. It lists 320 development rows after removing the approved Mann duplicate, with their current labels. Check them against the review already completed. Fill actual reviewer/date and set `accept_all_listed_labels_and_eligibility` to true only if correct. Put changes in `exceptions` with case ID, final decision/label and a short evidence reference. Existing A review need not be repeated. The 54 B/C eligibility disagreements remain excluded.

## 3. Record final test decisions

Open `test_review_template.json`. It contains the 50 current candidates (A 17, B 13, C 20); the count may decrease after review. For each record, fill:

- `decision`: `include`, `exclude`, or `unresolved`.
- `final_label`: 0 = affirmed, 1 = reversed/vacated, for included cases only. Use the current appeal, not the lower-court result or which party won.
- `review_evidence_reference`: a disposition quote or the existing review-file row/entry supporting the decision.
- `duplicate_of` / `family_correction`: only when there is a correction. Same decision means one row; distinct appeals in the same litigation share one family.
- Actual reviewer name(s) and review date at the top.

Do not force mixed/unclear outcomes into a binary label. Keep uncertain cases out under the existing codebook. Do not use model predictions to choose labels or exclusions.

## 4. Confirm family decisions and masking audit

The five B/C duplicate-pair recommendations and four flagged-mask recommendations were approved in chat. `family_candidates.json` lists the broader existing family candidates, including additional A/C pairs not yet resolved by that five-pair review. Supply any existing decisions for those pairs; otherwise they remain grouped and flagged, and the dataset cannot be described as fully deduplicated.

Mask corrections are being evaluated as a versioned sensitivity experiment. I will show their audit and residual issues before fixing final preprocessing. You do not need to choose classifier settings.

## 5. Return the record

Send the edited files, their paths/links, or a message identifying the exact accepted manifest, actual reviewer/date and case-specific exceptions. Merely saying everyone reviewed the data does not identify which labels and exclusions the review finalized.

Then I will validate coverage, labels, evidence references and family separation; freeze the version and hashes; fix the protocol from development results; and evaluate the reserved test once with all requested metrics and paired family-bootstrap intervals. No final test predictions have been run.
