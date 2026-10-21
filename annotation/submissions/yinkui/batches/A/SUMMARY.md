# Yinkui — partition A independent annotation submission

Completed October 21, 2026: **169/169 unique cases**, all 34 chunks, no missing IDs. All records are **LLM drafts**, pending human review and team adjudication.

| Provisional eligibility | Cases |
|---|---:|
| Include in binary task | 122 |
| Review unresolved eligibility | 36 |
| Exclude from binary task | 11 |

Among currently included cases: **82 affirmed (0)** and **40 reversed/vacated (1)**. These are annotation counts, not final sample counts or model metrics.

## Files

- [annotations.jsonl](annotations.jsonl): one record per case, including excluded and unresolved cases.
- [annotations.validation.json](annotations.validation.json): full-manifest validation; passed with no missing/extra IDs or validation errors. LLM-draft and unresolved-review warnings are expected.
- [case_table.md](case_table.md): every case, provisional decision, outcome and uncertainty notes.
- [annotations.summary.json](annotations.summary.json), [progress.json](progress.json): machine-readable counts and completion status.
- `chunks/` and `drafts/`: 34 selected chunks and preserved original drafts; no draft overwrites.
- `authoring/`: semantic selections made after reading each full opinion, plus serialization/validation helpers.
- [provenance.json](provenance.json), `prompts_used/`, [independent_freeze.json](independent_freeze.json): instructions, source/output hashes and exposure record.
- [human_review_log.md](human_review_log.md): explicitly pending, not a fabricated review.

## Independence and remaining review

No peer batch-A annotations were read or cross-compared. Repository directory listings were inspected to match the reviewer-folder layout. The source, codebook and schema were preserved. Initial version 1.0.0 is used; the shared decision log still says substantive team freeze is pending.

Previously annotated/compared calibration cases in this submission: NY-2757329, NY-4546774, NY-4551400, NY-4840329, NY-5992200. Their records disclose this exposure. Keep them training-only and separate them when reporting fresh independent agreement.

Resolve property-boundary, institution-ownership, unclear fall mechanism and procedural-versus-merits cases before claiming a final eligible sample. The original 506-candidate prescreen is not proof of eligibility. Some decisions use only the phrase “defendant’s building”; these remain review cases where private ownership or context is insufficient. Jury-instruction and product/service-liability boundaries also require a team decision.

Check companion opinions before splitting: Coreano expressly cites a decision issued together, and Sodhi discusses companion appeals. Preserve both records in the audit but group related litigation for evaluation; do not count multiple opinions as independent evidence without checking.

Next: freeze the other reviewers’ A submissions, compare the independent files, and record human adjudication. Use one resolved record per case for an A-only MVP. Do not concatenate reviewer outputs into a larger case dataset or use outcome/issue/evidence annotations as ordinary predictive inputs.

## Revalidate

From the repository root:

```sh
python annotation/scripts/validate_annotations.py annotation/submissions/yinkui/batches/A/annotations.jsonl --expected annotation/batches/A/manifest.json --report annotation/submissions/yinkui/batches/A/annotations.validation.json
```

`authoring/finalize_submission.py` packages existing selected chunks and validates them; it does not infer labels. Original per-chunk authoring scripts refuse to overwrite existing drafts.
