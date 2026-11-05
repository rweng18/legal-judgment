# Hayden’s handoff from Becca · Batch B+C tokenizer and length report

Hayden, you can measure opinion lengths as soon as you have paired FULL and MASKED texts. The length report uses only the tokenizer, so you can run it while label review is underway. Once you freeze the release, run it on the exact texts you send to Becca. Becca will use the same tokenizer and chunk settings to extract embeddings, select models and report the experiments.

## Prepare one row per opinion

Combine B and C and retain each case’s batch ID. Include the 2010–2020 training cases (`train`) and 2021–2022 validation cases (`validation`) in `development.jsonl`. The 2023–2024 reserved cases appear only as metadata in the release manifest.

Save one UTF-8 JSON object per line. This fictional row shows the required fields and spelling.

```json
{"case_id":"example-001","batch":"B","date_filed":"2019-05-10","period":"train","texts":{"FULL":"We affirm. The witness described the entrance.","MASKED":"The witness described the entrance."}}
```

Use the same stable case ID for both variants. FULL is the cleaned opinion. MASKED is the cleaned opinion after the selected passages have been removed. Finish cleanup and masking before tokenizing. Keep labels, reviewer notes and removed passages in the accompanying records. If either text is empty, flag the case for review before measuring it.

## Use Becca’s tokenizer and chunk settings

| Setting | Value |
|---|---|
| Encoder and tokenizer | `nlpaueb/legal-bert-base-uncased`, revision `15b570cbf88259610b082a167dacc190124f60f6` |
| Tokenizer | `BertTokenizer` via `AutoTokenizer` with `use_fast=False`. Use the checkpoint’s vocabulary and uncased behavior. |
| Content tokens | Encode the complete FULL and MASKED strings separately with `add_special_tokens=False` and `truncation=False`. |
| Chunks | Take contiguous windows of up to **510 content tokens**, starting at offsets 0, 510, 1020 and so on. Use zero overlap and keep the final window. |
| Model input | Becca adds CLS and SEP to each chunk, giving at most **512 tokens** before padding. Inference batches contain up to four chunks, right-padded to the longest input. |
| Opinion vector | Becca averages final-layer content-token vectors across all chunks, excluding specials and padding. Each chunk contributes in proportion to its content length, yielding one 768-dimensional vector per opinion per variant. |

**Boundary check:** 510 content tokens fit one input. A 511-token opinion needs two chunks of 510 and 1. A 1,100-token opinion needs three chunks of 510, 510 and 80. Apply the rule independently after masking, since deleting a passage can move every subsequent chunk boundary. Both the length utility and Becca’s experiment import the [shared implementation](encoder.py) and read the [settings file](encoder_settings.json).

## Generate and report the lengths

From the repository root, run the following in a Python 3.11 or 3.12 environment. The first run downloads the pinned tokenizer files unless they are already cached. Substitute your development file path and choose a fresh output directory for each run.

```sh
cd experiments/provisional_b
python -m pip install "numpy==2.3.4" "transformers==4.57.1"
python lengths.py inputs/bc_v1/development.jsonl runs/bc_v1_lengths
```

| Output | What to report |
|---|---|
| `case_lengths.csv` | One row per case with FULL and MASKED word counts, content-token counts, chunk counts, final-chunk lengths and flags for exceeding one input. Words are counted by splitting on whitespace. |
| `length_summary.json` | For each split and variant, report the case count, minimum, median, mean, 90th percentile and maximum of words, tokens and chunks per case. Report total chunks and the fraction of opinions with **more than 510 content tokens**. The denominator is the number of cases in that split. |
| `paired_change` within the summary | Report how many words, tokens and chunks masking removed. Each case’s change is FULL minus MASKED. Its percentage is 100 × change / FULL. The summary describes these paired case-level changes. |

Use four rows for the main table: training FULL, training MASKED, validation FULL and validation MASKED. Report paired masking changes once per split. Use `fraction_over_one_input` as a fraction or multiply by 100 for a percentage. The `*_removed_pct` fields are already percentages.

## Return the frozen release to Becca

1. Supply **`manifest.jsonl`, `development.jsonl` and `release.json`** together. The manifest covers all B/C candidates and records eligibility, dates, periods and reviewed family assignments. Included development cases must have reviewed outcome labels (0 = affirmed, 1 = reversed/vacated). Resolve included families that span periods before freezing. The [release specification](README.md#haydens-handoff) lists the exact fields and checksum format.
2. Include the **`case_lengths.csv` and `length_summary.json` generated from the frozen texts**. Check that `development_sha256` in the summary matches the hash for `development.jsonl` in `release.json`. The CSV should contain one row for each included development ID.
3. Identify the versioned source opinions, removal logs, masking review and unresolved eligibility or family decisions. If review changes the texts or case membership, assign a new release version and regenerate the length outputs.
