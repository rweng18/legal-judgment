# Deliverables and acceptance criteria

## Calibration and pilot materials

Save these materials as you complete each step. Bring available results and open questions to Monday’s discussion, and note any pending work in `SUMMARY.md`. The structure below describes the completed calibration/pilot package, rather than a weekend deadline.

```text
submissions/<reviewer_id>/
  prompts_used/                 exact prompt text/version used
  independent_calibration_notes.md
  calibration/                 CAL_001.json, CAL_002.json, CAL_003.json
    drafts/                    original unmodified responses
  calibration.jsonl            exactly 12 independently annotated records
  calibration.jsonl.validation.json
  pilot.jsonl                  exactly 5 assigned pilot records
  pilot.validation.json
  cross_review/                independent notes + review of teammate's pilot
  SUMMARY.md                   counts, unresolved cases, time spent, model used
```

`SUMMARY.md` should state batch/owner, actual model name, prompt/codebook version, completed IDs or chunks, validation status, how many human checks occurred, unresolved case IDs/reasons, estimated minutes per case, and proposed rule clarifications. No scores should be invented. Do not include private chat/account information or credentials.

## Full batch submission after production

```text
submissions/<reviewer_id>/
  production_chunks/           selected final chunk files
  drafts/                      earlier LLM versions, not input to final merge
  annotations.jsonl            exactly 169 (A/B) or 168 (C) primary records
  annotations.validation.json
  human_review_log.md
  adjudication_log.md
  SUMMARY.md
```

For a small demonstration, merging two explicitly named files works as follows; for full production list the selected final files only. Do not pass a folder wildcard containing validation reports or historical versions.

```sh
python scripts/merge_annotations.py submissions/yinkui/production_chunks/A_001.json submissions/yinkui/production_chunks/A_002.json --expected batches/A/manifest.json --partial --output submissions/yinkui/checkpoint.jsonl
```

`--partial` permits missing IDs and reports them; this is a checkpoint, not a finished batch. For the final batch, omit `--partial` and provide all selected final records. The merge refuses duplicate IDs rather than choosing the latest file silently. If a chunk contains already completed calibration/pilot cases, assemble one final record per expected ID explicitly.

Validate the completed batch:

```sh
python scripts/validate_annotations.py submissions/yinkui/annotations.jsonl --expected batches/A/manifest.json --report submissions/yinkui/annotations.validation.json
```

## Coordinator merge

Run on the full repository copy, whose `source/cases.jsonl` contains all 506 cases:

```sh
python scripts/merge_annotations.py submissions/yinkui/annotations.jsonl submissions/becca/annotations.jsonl submissions/hyunsang/annotations.jsonl --expected source/all_expected.json --output submissions/merged_annotations.jsonl
python scripts/summarize_annotations.py submissions/merged_annotations.jsonl --output submissions/annotation_summary.json
```

Do not combine independent calibration runs into this primary merge: those contain intentionally duplicated IDs. Carry only the owner-approved final version into the primary batch. Preserve independent versions separately for agreement analysis.

The summary reports annotated count, include/exclude/review counts, full outcome distribution, eligible binary class counts, planned-period class counts, unresolved items, missing factual fields, word lengths, and review status. It also generates a seeded random sample of 10% of included training cases for audit. Freeze and retain the input dataset hash/version when drawing that sample; rerunning after changes can alter the sample.

## Acceptance checklist

- Every expected primary ID occurs exactly once, including excluded or unresolved cases.
- Source hashes match; all source text remains unchanged.
- Every required schema field and all 19 legal-issue topics are present.
- All supporting quotes match the canonical passages; no invented ellipses, offsets, facts, or model versions.
- Included cases have private-property, incident, merits, and current-disposition evidence.
- Modified/mixed/dismissed/unclear outcomes are preserved with null binary label.
- All passages are classified in text_sections, including metadata or separate-opinion material.
- Original LLM drafts, corrections, human reviews and adjudications are distinguishable.
- Unresolved cases stay out of the included binary pool until resolved.
- Validation/test labels receive independent human review before model evaluation.
- Related-case hints are checked before final train/validation/test splitting.
- No classifier uses annotation JSON, evidence selections, or derived outcomes as ordinary input features.

## Uploading to GitHub

Use a personal branch such as `annotations/yinkui` and a PR containing only your submission folder and explicitly agreed documentation changes. Alternatively, upload your folder through GitHub's web interface if the team uses that workflow. Do not overwrite source packages or another person's work. Ask the coordinator to resolve conflicting record versions with a logged decision.

No scripts upload automatically. A GitHub account with collaborator write access, plus any required connected-app repository access, is needed. Do not put access tokens into files, notebooks, prompts, screenshots, or commit messages.

