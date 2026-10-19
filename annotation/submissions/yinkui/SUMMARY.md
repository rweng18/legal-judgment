# Yinkui calibration submission

Prepared October 18, 2026 for batch A. Scope: the 12 shared calibration cases only; no five-case pilot or production batch annotation was performed.

## Deliverables

- [Combined 12-case annotation JSONL](calibration.jsonl) and [validation report](calibration.jsonl.validation.json).
- [Three chunk outputs and validation reports](calibration/) with preserved original drafts in `calibration/drafts/`.
- [Independent assistant notes](independent_model_notes.md), [input/output hash freeze](independent_freeze.json), and [resolved prompts](prompts_used/).
- [Comparison with Becca and discussion points](comparison/REPORT.md), [case-by-case table](comparison/case_table.md), [agreement data](comparison/calibration_comparison.json), and [proposed corrections, not applied](comparison/proposed_corrections.json).

All three chunks (`CAL_001`, `CAL_002`, `CAL_003`) are complete and structurally valid. Every record includes exact evidence quotations, all 19 issue topics, every source passage's classification, and the remaining schema fields.

## Status and counts

| Item | Result |
|---|---|
| Completed / pending calibration records | 12 / 0 |
| Include / exclude / review | 7 / 1 / 4 |
| Included binary classes: 0 / 1 | 4 / 3 |
| Whole dispositions across all 12: affirmed / reversed | 9 / 3 |
| Actual model identity exposed in this session | GPT-6 / Codex; exact variant/snapshot unavailable |
| Schema / prompt version used | 1.0.0 / 1.0.0 |
| Human-reviewed records | 0 |
| Independently authored human notes | Not supplied; model notes are explicitly labeled |
| Time per case | Not measured reliably; no estimate claimed |

The four review cases are Rodriguez (NY-5992200), Maldonado (NY-3193933), Verges (NY-4795834), and Gartenberg (NY-4840329), all involving the sufficiency of private-premises evidence. Richardson (NY-2993705) is excluded from the narrow slip/trip scope as a described step-off/trench fall. These judgments remain LLM drafts for human review.

## Independence and cross-comparison

The complete independent draft was frozen in commit `b94ae3c` before fetching teammates' results. The later Git pull brought in Becca's three chunk files and her notes from `main` (`20fee87`). The codebook, schema and input packets match the frozen inputs. Original drafts were not changed after comparison.

Both LLM drafts agree on all 12 appellate dispositions, but agree on include/exclude/review for only 7/12 cases. Six cases are included by both; their binary labels agree in all six. Becca's Verges record has a review/null-label inconsistency; the proposed correction is documented without changing her files. No Hyun Sang submission was found in the fetched branches or open PRs at the time of inspection, so the report is explicitly a two-submission comparison.

The main rule questions are private-property evidence, slip/trip versus step-off falls, and counting appealed orders rather than individual motions. Details, source passages and extra-feature disagreements are in the comparison report. No rule was declared team-approved; no draft was promoted to human-reviewed or gold. Agreement statistics are not model accuracy, balanced accuracy or macro F1.

For independent human calibration, read the original opinions before this submission's answers. Record actual human judgments separately; do not relabel the assistant's notes as human work.
