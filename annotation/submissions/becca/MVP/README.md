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

Family decisions are assistant drafts awaiting human review. Target labels are unchanged and still await Hayden's review. Family assignments do not establish human-gold outcomes or prove that no further family relationships exist. Versioned split assignments are now frozen with Sodhi pending; FULL and MASKED text have now been produced; encoder chunks and training have not begun.

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

## MASKED text — masked_v1

`produce_masked_text.ipynb` generates 114 texts from the immutable FULL exports.
Rules were developed on 81 training cases, with complete reading of 10 purposive
training samples, then frozen before processing development/test/pending cases.
The same rules apply without receiving labels or selected annotation evidence.

- `preprocessing/masked_text.py`: reusable sentence masking and immutable export.
- `preprocessing/masked_rules_v1.json`: frozen policy, code/input hashes and training IDs.
- `preprocessing/masked_training_review_v1.json`: training sample notes and training audit.
- `preprocessing/verify_masked.py`: boundary/leakage regressions and export checks.
- `data/masked_v1/masked.jsonl` and `texts/`: model inputs containing only ID/text.
- `data/masked_v1/removal_audit.jsonl`: exact removed sentences, FULL-relative Unicode
  offsets, reasons, word counts/fractions, hashes and retained-cue candidates.
- `data/masked_v1/manifest.json` and `summary.json`: provenance and totals.

The run removed 223 sentences / 5,178 words (8.14%), leaving 58,441 words.
No empty or under-50-word outputs occurred. Retained-cue candidates occur in 42
cases; these include indirect reasoning and cited outcomes, not just possible
missed direct cues. Four cases have inherited bracket-balance warnings. One
short training case loses over half its words and retains 64 words. Flags remain
explicit review candidates; no evaluation-specific editing or tuning occurred.

All three notebook code cells executed sequentially using Python's standard
library; this was not a Jupyter-kernel execution. Twenty synthetic regression
checks and 114-case reconstruction/hash/word-count/export checks passed.
IDs, labels, families and splits are unchanged; pending Sodhi remains pending.
This is automated preprocessing with assistant training-sample review, not
human-adjudicated text or a guarantee of exhaustive cue removal. Later changes
require a new version and rerunning affected experiments.

## Training residual review and current MASKED version — masked_v2

`review_masking_audit.ipynb` is the current masking-review/rebuild notebook.
It uses `preprocessing/masked_text_v2.py`, `masked_rules_v2.json`,
`masked_training_review_v2.json`, and `verify_masked_v2.py`.
**Use `data/masked_v2/` for subsequent MASKED experiments.** The earlier v1
notebook, rules, code, text and audits remain preserved for reproducibility.
FULL, the selected IDs, provisional labels and split manifest are unchanged.

Seed 20261016 selected five additional complete training opinions from the 26
flagged training cases not fully read previously. Four missed outcome sentences
were confirmed in three samples; two were not flagged by the original scanner.
General rules now handle explicit agreement about operative relief, nominal
ruling descriptions, and required denial/grant of relief. Rules were frozen
before v2 evaluation processing. No evaluation labels, selected annotation
quotations or case-specific overrides were used. Fifteen training opinions have
now been fully read across both reviews; this is not exhaustive semantic review.
Twenty-one cases in the follow-up sampling pool remain without full review.

V2 saves 228 removed sentences and per-case exact FULL offsets, removal reasons,
word counts/fractions, hashes and residual candidates. It removes 5,365 words
(8.43%) from FULL, leaving 58,254 words. There are no empty or under-50-word
outputs. One case retains 64 words after losing over half its words. Four
inherited bracket warnings remain. Forty-three cases have broad residual-cue
flags; the scanner was broadened, so this count is not directly comparable to
v1's 42 flags and does not count confirmed leaks.

All three notebook cells executed sequentially in Python (not a Jupyter kernel).
Thirty-three regression checks and all 114 reconstruction/hash/word-accounting
checks passed. Evaluation flags remain review candidates and do not support a
claim of exhaustive cue removal. Any experiment run with masked_v1 must be rerun
for a masked_v2 comparison. No model experiments were run in this task.

## Model-input boundary and handoff

`MODEL_INPUT_HANDOFF.md` identifies the approved FULL v1 / MASKED v2 text exports
and shared mvp_split_v1 targets. `preprocessing/model_inputs.py` validates the
exact `{case_id, text}` export fields and returns texts, case IDs and targets in
separate tuples. Only texts enter tokenization/vectorization. Annotation-rich
metadata, favors, findings, summaries and selected quotations remain diagnostic
artifacts. Legal reasoning/quotations in the original opinion remain text.

`validate_model_inputs.ipynb` checks hashes, ID coverage, label availability,
family separation and the feature/target boundary. It confirms identical IDs and
targets across variants, with 81 train / 16 development / 16 test cases and Sodhi
excluded as pending. Seventeen checks passed, including rejection of prohibited
fields and incorrect joins. All three notebook code cells executed sequentially
in Python; no Jupyter kernel or model training was run. Results and code/input
hashes are saved in `data/model_input_contract_v1/validation.json`.

No text, targets, IDs or splits changed. Labels remain provisional. These checks
protect the supplied loader; downstream code must also pass only its text strings
to feature construction. Later dataset changes require a new version and reruns.

## Descriptive word/token lengths — length_statistics_v1

`descriptive_length_statistics.ipynb` contains executed tables for FULL v1 and
MASKED v2: minimum, median, mean, P90 and maximum words/content tokens; fractions
exceeding one LEGAL-BERT input; chunk distributions and per-case chunk counts;
and paired masking reductions in words, tokens and chunks. Training (81),
development (16) and their combined 97-case set are reported separately.
Test cases and pending Sodhi are excluded under Yinkui's current restriction.

The notebook uses the supplied slow LEGAL-BERT tokenizer at revision
`15b570cbf88259610b082a167dacc190124f60f6`, with Transformers 4.57.1. Content
chunks have 510 tokens, no overlap, and two special tokens per input. Counts
exclude special tokens and padding; words use whitespace splitting; P90 uses
linear interpolation. No extra lowercasing, truncation, model weights, embedding
extraction or model training is performed.

All five code cells executed in a real local Jupyter kernel. Chunk accounting,
text/input hashes, matched IDs, scope exclusion and audit word reductions passed.
No empty or under-50-word outputs occurred. Combined totals: 183 FULL chunks and
176 MASKED chunks; 70.10% versus 64.95% exceed a single input; masking removes
8.25% of words and 8.00% of content tokens across these 97 cases.

`data/length_statistics_v1/` holds `per_case.jsonl` (194 rows),
`paired_changes.jsonl` (97 rows), `summary.json` and `manifest.json`.
`preprocessing/length_statistics.py` reproduces the calculation; the requirements
lock and tokenizer download helper are in the same directory. The ignored local
`.venv/` and `.cache/` contain the execution environment and tokenizer files.
The provenance manifest pins tokenizer file hashes and input/code hashes.
On another machine, install `preprocessing/length_requirements-lock.txt`, run
`preprocessing/download_length_tokenizer.py`, and select that Python environment
as the notebook kernel. Later data/tokenizer/chunk changes require a new version.
