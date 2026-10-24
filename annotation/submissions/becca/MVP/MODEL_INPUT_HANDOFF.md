# Model-input handoff to Yinkui

This defines the approved input boundary. It is not a declaration that the full
dataset review or descriptive-statistics work is complete.

## Fixed inputs

Paths below are relative to this MVP folder.

| Purpose | File |
|---|---|
| FULL model text | `data/full_v1/full.jsonl` |
| MASKED model text (current) | `data/masked_v2/masked.jsonl` |
| Shared IDs, split assignments and target labels | `data/mvp_split_v1/split_manifest.json` |
| Guarded loader and validation | `preprocessing/model_inputs.py` |
| Reproducible validation notebook | `validate_model_inputs.ipynb` |
| Validation results and input hashes | `data/model_input_contract_v1/validation.json` |

Both text exports contain exactly `case_id` and `text`, with 114 unique matching
IDs. Use only `text` as the feature input. The ID is for joining, grouping chunks,
and associating predictions with cases; it is not a predictive feature.

The manifest supplies `cases[].target` separately for supervision and scoring.
Join by case ID, never by row position. Use exactly the same case order and targets
for both text variants and all models. The guarded loader returns only assigned
cases: 81 training, 16 development, 16 test. Sodhi (`NY-4655053`) remains pending
and must not enter the experimental subset. Split seed: 20261016.

Targets are **provisional**, pending Hayden's review. Do not describe evaluation
with these labels as human-gold evaluation. Family and residual masking review
also remain incomplete. `descriptive_length_statistics.ipynb` now reports word/token/chunk statistics for
the 97 training/development cases using Yinkui's pinned encoder settings. Test
and pending cases remain excluded from those statistics.

## Use the guarded loader

From a notebook in MVP, after adding `preprocessing/` to the Python import path:

```python
from pathlib import Path
from model_inputs import load_model_batch

batch = load_model_batch(Path.cwd(), "MASKED", "train")
texts = list(batch.texts)       # only these strings go to tokenizer/vectorizer
y = list(batch.targets)        # separate training loss/scoring targets
case_ids = list(batch.case_ids) # bookkeeping, never concatenate with text
# encoded = tokenizer(texts, ...)  # use Yinkui's agreed encoder settings
```

Choose `FULL` or `MASKED` and `train`, `development`, or `test`. The loader checks
export hashes, the shared split/label snapshot, exact fields, unique/matching IDs,
valid targets, assigned-case text, family separation, and calibration restrictions.
It fails rather than silently dropping cases or selecting an alternate label.
All chunks from a case inherit its assignment and target; do not split chunks
independently. Fit learned vocabulary/feature transforms on training data only.

## Diagnostic artifacts are not model features

Do not feed annotation JSON, annotation-rich metadata tables, family/split records,
review notes, removal audits, or descriptive-statistics rows to a tokenizer or
vectorizer. In particular, do not append labels, favors, legal findings, factual
summaries, or selected supporting quotations. These are available for descriptive
analysis and error review only. Keep diagnostic annotation joins outside the
feature-building path.

Legal reasoning and quotations naturally occurring in the opinion remain in the
approved text under the frozen cleaning/masking rules. This boundary excludes
separately generated annotations; it does not remove all legally predictive
content or claim that FULL is free of outcome statements.

## Checks, limitations and changes

`validate_model_inputs.ipynb` validates the exports and exercises rejection of
annotation fields, duplicate/mismatched IDs, invalid/missing targets, empty assigned
text, nested annotations in the text field, and cross-split family overlap.
It verifies identical targets across variants even when input rows are reordered.

Empty assigned text is rejected. Text under 50 words is reported for review and
is not silently dropped; current FULL/MASKED v2 exports have neither empty nor
near-empty outputs. Pending/excluded cases are never returned by the loader.

Schema and checksum checks protect this saved input path; they cannot prevent a
different training script from concatenating annotations afterward. Use this
loader and pass only its `texts` to feature construction.

Keep existing versions intact. A change to IDs, labels, splits or preprocessing
requires a new dataset/contract version, fresh validation and rerunning affected
experiments. MASKED v2 supersedes MASKED v1 for future comparisons. Record exact
input hashes and versions with every experiment. No experiments are run by the validator.
