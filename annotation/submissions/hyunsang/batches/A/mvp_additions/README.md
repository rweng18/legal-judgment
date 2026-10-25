# Partition A: six additional MVP candidates

For Becca: this folder contains ONLY six approved additions to the existing 114 unanimously included cases. It does not replace, edit or merge the original 114-case pool. On the frozen comparison snapshot, all six IDs are outside that unanimous pool. Combining by unique case ID would produce 120 candidates (5 additional affirmed / label 0; 1 additional reversed / label 1).

## Files
- additional_6.csv: convenient ID/label/decision-reason handoff table.
- additional_6.jsonl: six complete schema-compatible original LLM records selected from the three frozen submissions.
- additional_6.expected.json and additional_6.validation.json: exact-six coverage and validator report.
- decisions.json: actual user decisions, exact original evidence and record-selection provenance.
- remaining_35_review.csv: no additions from these cases; retain review/null.
- review_decisions_41.json: full limited user-decision log for the review queue.
- input_freeze.json: snapshot and input SHA256 values.
- DECISIONS_KO.md: Korean handoff explanation.

## Provenance and review status
Records are unchanged copies selected explicitly: Egan, Rosado, Morreale and Cammarata from hyunsang; Barretta and Knapp from becca. They were already include records with the selected label. Selection is not a new independent annotation. The other reviewers' conflicting opinions remain preserved in the original submissions and comparison log.

Hayden/hyunsang accepted eligibility after AI full-source reading and discussion of quoted evidence; no fresh blinded human full-opinion pass is claimed. Full optional annotations were NOT all re-reviewed. The JSONL records therefore remain llm_draft with their original provenance. decisions.json records the limited human decisions separately. Validator warnings about LLM drafts are expected; schema-valid does not mean human-gold.

## Use
Append the six candidates to the existing pool by case ID, check for duplicates and confirm data version. Do not concatenate all three reviewer submissions. These annotation JSONs, explanations and selected quotes are target/audit material, NOT ordinary model text inputs. Build FULL/MASKED from frozen source opinions using the team's preprocessing rules. Preserve existing calibration-exposure and case-family checks; this package does not establish independent final-test gold or approve a split.

The meeting discussion supersedes the earlier written plan for this MVP scope. The 14 cases with any original exclude remain withheld under the meeting selection rule, not newly legally adjudicated. This package contains no new data for those 14. No model training, public upload, PR, merge or teammate message has been performed.

## Validation from repository root
python annotation/scripts/validate_annotations.py annotation/submissions/hyunsang/batches/A/mvp_additions/additional_6.jsonl --expected annotation/submissions/hyunsang/batches/A/mvp_additions/additional_6.expected.json --report annotation/submissions/hyunsang/batches/A/mvp_additions/additional_6.validation.json
