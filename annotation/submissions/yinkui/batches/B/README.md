# Yinkui — Batch B annotation submission

Completed November 3, 2026: **169/169 cases across all 34 chunks**. Full validation passed with no missing/extra IDs or structural/evidence errors. All records are **LLM drafts pending human review**, not gold labels.

| Provisional decision | Cases |
|---|---:|
| Include in binary task | 143 |
| Review eligibility | 15 |
| Exclude from binary task | 11 |

The included cases contain **98 affirmed (0)** and **45 reversed/vacated (1)**. Excluded/review cases have null binary labels. These are draft annotation counts, not the final study sample or model performance.

## Files for teammates

- [annotations.jsonl](annotations.jsonl): complete submission, one record per case including exclusions/reviews.
- [case_table.md](case_table.md): readable table of all 169 decisions and notes.
- [review_queue.md](review_queue.md) / [review_queue.json](review_queue.json): prioritized scope/exclusion/family review; all records still need human review.
- [annotations.validation.json](annotations.validation.json): schema, exact quotation offsets, source hashes, references, all-passages coverage and expected IDs.
- [annotations.summary.json](annotations.summary.json): machine-readable counts.
- [case_family_notes.json](case_family_notes.json): known duplicate/companion warnings.
- [revisions.json](revisions.json): eight LLM self-audit corrections; original v1 drafts retained, v2 records explicitly identify predecessors. No eligibility or binary label changed in this audit.
- `drafts/`, `chunks/`, `authoring/`: original drafts, selected records, per-chunk checks and actual manual semantic selections.
- [run_manifest.json](run_manifest.json), [provenance.json](provenance.json), [independent_freeze.json](independent_freeze.json), `prompts_used/`: completion, versions, input/output hashes and exposure record.
- [human_review_log.md](human_review_log.md): pending; no fabricated human sign-off.

## Procedure and interpretation

Same full-reading, codebook 1.0.0 and schema procedure as Yinkui's A pass. Every supplied passage was read, with exact quotes for scope, disposition, issues and factual features. No peer B annotations or external case facts were consulted, and no annotation API or subagents were used. The repository decision log still contains no substantive codebook freeze; disputed boundaries remain explicitly unresolved.

Prior calibration exposure in B: NY-2993705, NY-3206955, NY-4310325, NY-5960096. Affected records disclose this exposure. Keep them training-only and report them separately from fresh independent agreement.

Labels describe the **current appellate disposition**, not plaintiff success or prediction of an unseen lawsuit. A whole appealed order may be affirmed even when different parties obtained different relief below. Outcome beneficiaries and trial actions are recorded separately.

The 15 unresolved cases primarily concern private/public boundaries, unspecified fall mechanisms, and procedural-versus-merits scope. The 11 exclusions include public sites, nonqualifying incidents, procedural/insurance decisions and one duplicate-source observation. These remain in the audit file. Langgood has a complete majority disposition/reasoning but an announced dissent absent from the supplied snapshot; its inclusion carries a text-completeness flag.

One known duplicate pair is Alvarado: NY-6207337 retained provisionally and NY-4304440 excluded as duplicate. Check the family notes and all rounds before splitting. This is not an exhaustive cross-round family audit.

## Next steps

1. Freeze the other two independent B submissions before cross-comparison. Do not overwrite anyone's original draft.
2. Compare the three B files; review disagreements against original opinions, plus a sample of unanimous inclusions and exclusions. Hayden can lead actual human adjudication.
3. Resolve scope and labels, verify useful features and evidence, and record reviewer/date/reason in the consolidated B decision log. Do not automatically treat majority agreement as human gold.
4. Only after review, add eligible B cases to the study with one record per unique case and related cases grouped across splits. Reuse A's evaluation/masking procedure and maintain calibration cases in training only.

Do not concatenate three reviewer files as if they contained different cases. Annotation summaries, legal findings, selected outcome evidence and outcome cues may reveal labels; they are **not automatically approved predictive features or test masking spans**. The published opinion's reasoning may itself reveal the disposition. Preserve the full/masked/random-removal controls when modeling resumes.

## Revalidate (from repository root)

```sh
python annotation/scripts/validate_annotations.py annotation/submissions/yinkui/batches/B/annotations.jsonl --expected annotation/batches/B/manifest.json --report annotation/submissions/yinkui/batches/B/annotations.validation.json
```

Expected warnings are `LLM draft: not human gold` for all 169 and unresolved-review warnings for 15. The validator does not assess legal correctness. `authoring/finalize_submission.py` packages selected records without inferring labels. Per-chunk authoring and audit-revision scripts intentionally refuse draft overwrites; do not rerun them to replace existing annotations.
