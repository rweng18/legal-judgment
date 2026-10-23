# Becca MVP

## Notebooks

1. `isolate_unanimous_include.ipynb` isolates the 114 cases marked include by all three reviewers and retains the full 169-case audit.
2. `build_metadata_table.ipynb` builds the original 114-case source/label metadata (`metadata_v1`).
3. `review_case_families.ipynb` screens all 506 source opinions, reproduces saved family review decisions, and builds the family manifests and updated metadata.

Run all cells using Python 3 from this folder or the repository root. Only the standard library is required. Keep `family_review/` with the family notebook.

## Current artifacts

- `FAMILY_REVIEW_REPORT.md`: findings, uncertainty, calibration inheritance, and validation.
- `data/unanimous_include_v1/`: fixed 114-case IDs/source records, 169-case audit, and selection provenance.
- `data/metadata_v1/`: original metadata table, HTML view, and checksums; preserved as a prior version.
- `data/family_v1/`: 495 observed families across 506 sources, case/passage/packet mappings, reviewed candidates, uncertainty, and provenance.
- `data/metadata_v2_family_review/metadata.jsonl`: current 114-case metadata with draft family IDs and inherited calibration flags. Supersedes metadata_v1 for family/exposure fields only.
- `family_review/`: reusable screening code and saved assistant review evidence.

## Current status

The 114 MVP cases remain unchanged, in 114 observed families. Five have a related source record outside the MVP. Sodhi's missing companion remains unresolved. Germain inherits calibration exposure, bringing the recorded training-only MVP count to four. No known linked family spans chronological periods in this snapshot.

Family decisions are assistant drafts awaiting human review. Target labels are unchanged and still await Hayden's review. Family assignments do not establish human-gold outcomes or prove that no further family relationships exist. Versioned split assignments are now frozen with Sodhi pending; FULL text has now been produced; MASKED processing, encoder chunks, and training have not begun.

All notebook code cells have been checked by sequential execution, including repeat runs. Original annotations and synced project references were not modified. This work was prepared from repository revision e5f2ea9.

## Proposed chronological counts

`proposed_chronological_split.ipynb` reports period, family, provisional-class, exclusion, and pending counts from the existing metadata. It preserves the date boundaries, excludes cross-period families, enforces calibration restrictions, and holds unresolved companions. All three code cells passed checks. These are proposed counts only; no split is frozen or training performed.

## Frozen chronological split — mvp_split_v1

`freeze_case_id_splits.ipynb` freezes `data/mvp_split_v1/split_manifest.json`
with seed 20261016 and a companion SHA-256 file. It supersedes the earlier proposed
counts for assignment status: 81 training, 16 development, 16 testing, and one
pending case (Sodhi). Four MVP cases are training-only through recorded calibration
exposure and family inheritance. The manifest preserves all 114 selected IDs.

Targets remain provisional; human target and family review is not complete.
Development and testing are flagged as small. Existing versioned files cannot be
overwritten by the notebook; changed data/decisions require a new version and reruns
of affected experiments. All three code cells, count/group checks, and the frozen
output overwrite guard passed. No training was run.

## FULL text — full_v1

`produce_full_text.ipynb` generates and verifies the shared cleaned-text base using
`preprocessing/full_text.py` and frozen `full_rules_v1.json`. Outputs are in
`data/full_v1/`: 114 individual text files, label-free `full.jsonl`, source-offset
`removal_audit.jsonl`, summary, and checksum manifest. All later conditions must
start from these exact FULL texts; MASKED will add removal, not different cleaning.

The training-developed rules remove metadata and page markers while preserving
controlling opinion text, dispositions, citations, and substantive footnotes.
No separate dissent section was detected in the supplied source texts. Two majority
references to dissent were preserved and reviewed in `full_review_v1.json`.
All three notebook code cells and structural/export checks passed. No empty or
near-empty text was produced. Source OCR quirks are retained rather than silently
rewritten. Frozen IDs, targets, splits, and Sodhi's pending status are unchanged.
No MASKED text, encoder chunks, or training have been produced.
