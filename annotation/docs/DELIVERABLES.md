# Deliverables: three independent passes per round

Every teammate completes A, compares A together, then repeats B and C. Keep the existing calibration files where they are; they need not be renamed. Record actual prompt/model metadata, completed/pending IDs, validation status, prior exposure to shared answers, and real human review. Use model notes rather than invented human notes when no independent human pass occurred.

## Each person's round submission

```text
submissions/<reviewer_id>/
  batches/A/
    prompts_used/             exact prompt text/version
    chunks/                   selected final A_001.json through A_034.json
    drafts/                   original responses and earlier versions
    annotations.jsonl         exactly 169 unique records, including exclude/review
    annotations.validation.json
    human_review_log.md        actual review only; state pending if none
    SUMMARY.md                version, counts, uncertainties, exposure and progress
  batches/B/                  same structure; 169 cases
  batches/C/                  same structure; 168 cases
```

Reviewer IDs are `yinkui`, `becca`, `hyunsang`. Every person has all three round folders by the end. Original drafts must survive corrections; revised records identify their predecessors with `supersedes` and explain changes. Exact IDs and hashes stay unchanged.

## Build and validate a round output

Run from `annotation/`, with Python 3.10+ and the standard library. Replace the reviewer and round as needed. A partial example:

```sh
python scripts/merge_annotations.py submissions/yinkui/batches/A/chunks/A_001.json submissions/yinkui/batches/A/chunks/A_002.json --expected batches/A/manifest.json --partial --output submissions/yinkui/batches/A/checkpoint.jsonl
```

For a complete round, pass all selected chunk files, omit `--partial`, and write `annotations.jsonl`. The following cross-platform Python snippet selects exactly the 34 expected chunk files, without matching validation reports or old drafts:

```python
from pathlib import Path
import subprocess, sys
reviewer = "yinkui"
batch = "A"
folder = Path("submissions") / reviewer / "batches" / batch
files = [folder / "chunks" / f"{batch}_{i:03d}.json" for i in range(1, 35)]
assert all(p.is_file() for p in files), "Finish all chunks before a complete merge"
subprocess.run([sys.executable, "scripts/merge_annotations.py",
               *map(str, files), "--expected", f"batches/{batch}/manifest.json",
               "--output", str(folder / "annotations.jsonl")], check=True)
```

Carry any reusable own calibration records into the correct chunk/round with their original run provenance; do not add a second copy of the same case. Track known exposure to peer labels separately. The merge refuses duplicate IDs.

```sh
python scripts/validate_annotations.py submissions/yinkui/batches/A/annotations.jsonl --expected batches/A/manifest.json --report submissions/yinkui/batches/A/annotations.validation.json
```

## Cross-compare A, then B and C

Freeze all three independent files first. Run on the repository or a package containing that round's complete source subset:

```sh
python scripts/compare_calibration.py submissions/yinkui/batches/A/annotations.jsonl submissions/becca/batches/A/annotations.jsonl submissions/hyunsang/batches/A/annotations.jsonl --expected batches/A/manifest.json --output submissions/comparison/A/comparison.json
```

`--expected` selects the round; omitting it retains the original 12-case calibration behavior. The script validates all three complete inputs, reports pairwise core-field agreement/kappa and queues disagreements. It does not check every extra feature, adjudicate, or invent a missing third submission. Review facts, issue tags, exact evidence and provenance separately. Report previously discussed calibration cases separately when interpreting fresh independent agreement.

Save comparison notes, actual human decisions, an audit of unanimous inclusions/exclusions, and unresolved IDs under `submissions/comparison/A/`; repeat B and C. See [QUALITY_CONTROL.md](QUALITY_CONTROL.md). Pairwise agreement is not classifier accuracy.

## Consolidation

After review, assemble one selected/resolved record per expected ID into:

```text
submissions/consolidated/
  A.jsonl                     169 records, including excluded/unresolved cases
  A.validation.json
  A.summary.json
  A_decisions.md              record sources, changes, reviewers and open items
  B.jsonl                     169, when ready
  C.jsonl                     168, when ready
  all_cases.jsonl             506 only after all three rounds are ready
```

Never directly merge Yinkui + Becca + Hyun Sang as a case dataset: each person covers the same IDs. Consolidation requires explicit reviewed selection/resolution. Keep unresolved cases marked review with null binary labels; keep excluded records and their reasons for the audit trail. Do not label model consensus human-reviewed.

```sh
python scripts/validate_annotations.py submissions/consolidated/A.jsonl --expected batches/A/manifest.json --report submissions/consolidated/A.validation.json
python scripts/summarize_annotations.py submissions/consolidated/A.jsonl --output submissions/consolidated/A.summary.json
```

Once all three disjoint rounds are consolidated, use the full repository source:

```sh
python scripts/merge_annotations.py submissions/consolidated/A.jsonl submissions/consolidated/B.jsonl submissions/consolidated/C.jsonl --expected source/all_expected.json --output submissions/consolidated/all_cases.jsonl
python scripts/summarize_annotations.py submissions/consolidated/all_cases.jsonl --output submissions/consolidated/all_cases.summary.json
```

A smaller MVP can start from reviewed eligible records in A alone (169 candidates, roughly 170 before filtering). Report actual eligible/class/split counts and exclusions; do not require exactly 170 or describe three annotations as three independent cases. The README covers accuracy, balanced accuracy, macro F1, confusion matrix, class counts and small-sample evaluation limitations.

## Acceptance checks and GitHub submission

- Every expected case appears once per reviewer output and once in the consolidated round, including exclusions/reviews.
- Schema, IDs, hashes, evidence references, quotation offsets and passage coverage pass validation.
- All 19 legal-issue topics and factual fields are present; unknowns remain explicit.
- Private-premises scope and binary disposition have source evidence; unresolved and nonbinary outcomes have null labels.
- Original drafts, prior exposure, corrections, human review and adjudication are distinguishable.
- Actual human review is required for human-gold evaluation labels; check case-family overlap before data splitting.
- Annotation outputs, selected evidence and outcome-derived fields must not be concatenated into ordinary model input.

Use your own branch and reviewer folder. A coordinator can publish comparison/consolidated outputs once reviewed. Do not overwrite peer submissions, change case texts, or automatically promote majority labels. No script uploads automatically; do not store credentials in files.
