# Becca: tokenizer and chunk settings

Prepared October 24, 2026. These are the settings used in our completed Partition A trial, verified against the cached tokenizer and encoder configuration. Please keep them fixed for the reviewed rerun so changes in data preparation are not mixed with changes in representation.

Your part is to provide the reviewed dataset, cleaned FULL/MASKED texts, and length/chunk checks. Yinkui will extract embeddings and train/evaluate the classifiers. You do not need to train a model or recompute the trial's embeddings.

## Exact settings

| Component | Setting |
|---|---|
| Encoder and tokenizer | `nlpaueb/legal-bert-base-uncased` |
| Pinned revision | `15b570cbf88259610b082a167dacc190124f60f6` — use this for both |
| Tokenizer | `BertTokenizer`, loaded with `AutoTokenizer(..., use_fast=False)` |
| Case handling | Checkpoint's uncased behavior (`do_lower_case=True`); do not add a separate lowercasing/normalization step |
| Vocabulary | 30,522 tokens; use the checkpoint vocabulary unchanged |
| Initial tokenization | `add_special_tokens=False`, `truncation=False` |
| Content chunk size | **510 tokens**, fixed contiguous token windows |
| Overlap | **0 tokens**; window step 510 |
| Model input | `[CLS] + content chunk + [SEP]`, at most **512 tokens** |
| Final chunk | Keep it, even if short; do not discard or repeat it |
| Padding | Right-pad to the longest sequence in each inference batch; use the attention mask |
| Token IDs | CLS 101, SEP 102, PAD 0, UNK 100 |
| Inference batch size | 4 **chunks**, not four opinions |
| Frozen representation | Last hidden layer, 768 features; evaluation mode, gradients disabled |
| Within-chunk pooling | Mean of content-token vectors only; exclude CLS, SEP and padding |
| Across-chunk pooling | Mean weighted by each chunk's content-token count |
| Saved case embedding | One 768-dimensional `float32` vector per opinion per text variant |
| Trial software | Transformers 4.57.1, PyTorch 2.9.1+cpu; see requirements lock for the full environment |
| Execution settings | Seed 20261023; four CPU threads in the trial |

The authoritative model revision is in [model_lock.json](model_lock.json). Although the trial's general config has `encoder_revision: null`, the runner resolves and pins the revision through this lock file; it does not load a changing `main` revision. [encoder_settings.json](encoder_settings.json) is a portable handoff specification, not a new configuration automatically consumed by the existing runner.

## Text and chunk preparation

1. Keep stable `case_id`, `family_id`, chronological split, eligibility/review status and final label in metadata. Labels, evidence quotations, reviewer notes and predictions must not be appended to model text.
2. Finish source cleanup and outcome masking **before tokenization**. Tokenize FULL and MASKED separately. Do not remove stopwords, citations or punctuation as an extra encoder-specific step. MASKED means removing the selected passages, not replacing them with the tokenizer's `[MASK]` token.
3. Tokenize the entire remaining opinion without truncation. Split the resulting token-ID list at offsets 0, 510, 1020, and so on. These are token windows, not sentence windows. Do not realign MASKED chunks to FULL chunks: their boundaries can differ after deletion.
4. Add CLS/SEP separately to each chunk. Keep original order and all chunks. For example, 1,100 content tokens become 510 + 510 + 80, with input lengths 512, 512 and 82 before batch padding.
5. All chunks inherit the opinion's split. Never split or evaluate chunks as independent cases. The classifier receives one pooled vector per opinion.
6. Flag empty texts for resolution; do not silently drop cases from one condition. Freeze the same included IDs across FULL/MASKED and all compared models.

Tokenization pattern, matching the trial:

```python
tokenizer = AutoTokenizer.from_pretrained(
    local_pinned_snapshot, local_files_only=True, use_fast=False
)
ids = tokenizer.encode(
    cleaned_text, add_special_tokens=False, truncation=False, verbose=False
)
assert ids  # Otherwise flag the opinion for review.
chunks = [ids[start:start + 510] for start in range(0, len(ids), 510)]
inputs = [tokenizer.prepare_for_model(
    chunk, add_special_tokens=True, return_special_tokens_mask=True
) for chunk in chunks]
```

See `encoder_features()` in [train.py](train.py) for the implemented batching and pooling. Chunk means are weighted by content length: with chunks of 510, 510 and 80 tokens, use weights 510/1100, 510/1100 and 80/1100. An unweighted mean would give the short final chunk too much influence. Context is computed within each chunk; this is not equivalent to encoding the entire opinion in one long transformer pass.

## What to hand back

- A versioned dataset with stable IDs, reviewed labels/status, family/split metadata, and the exact cleaned FULL/MASKED strings. Preserve original opinions and a log of removed passages separately.
- Per opinion and variant: UTF-8 text SHA-256, word count, content-token count, number of chunks, and final-chunk content length. Chunk token IDs are optional because Yinkui can regenerate them from the frozen texts and tokenizer.
- Per development split and variant: min, median, mean, P90 and max token counts; proportion with more than 510 content tokens; total chunks. Count tokens before CLS/SEP and padding. Keep word counts as a separate measurement.
- The masking review, unresolved cases, and versioned family hints. Do not treat the provisional trial's masks or labels as approved ground truth.

Check that each case's chunk content lengths sum to its complete token count, each content chunk has 1–510 tokens, and each unpadded model input has at most 512 tokens. No tokens should be lost or duplicated.

Keep the 2023–2024 test period out of development tokenization, embedding extraction and model analysis for now, consistent with the trial. Test-label review follows the separate agreed process; it should not use model predictions. Fit vocabulary/IDF, embedding scaling and classifiers on training cases only.

If source text, masking, case order, tokenizer/revision, chunking or pooling changes, use a new run/version and regenerate affected embeddings. Reuse embeddings only when these settings and case/text hashes match. The existing cache records model revision, ordered case IDs, text hashes and pooling description; any future tokenizer implementation change also requires a fresh cache. Do not reuse FULL embeddings as MASKED embeddings.

Current trial sanity check (not targets for revised data): 105 development opinions produced **199 FULL chunks** and **196 MASKED chunks**. Once Hayden's review or your cleanup changes the data, the counts can legitimately change.
