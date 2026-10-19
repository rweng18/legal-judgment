# Running the annotation with ChatGPT or a local assistant

## Choose your workflow

**Uploaded-file ChatGPT:** download and extract your batch ZIP locally; attach the codebook, schema, and a single input `.md` file to the chat. Paste the start prompt. A ChatGPT project can keep shared instructions and uploaded sources across chats, but it does not automatically read local folders. See [official project documentation](https://learn.chatgpt.com/docs/projects). Avoid a shared chat/project that exposes other people's calibration answers before independent submission.

**Local assistant with file access:** open the extracted `annotation/` folder, or the repository's annotation folder, as the workspace. Tell the assistant your batch and reviewer ID and ask it to read `AGENTS.md` and `README.md`. Specify one chunk at a time initially. The assistant can run Python scripts locally; no API service is needed.

This workflow does not automate the ChatGPT website, use account credentials, or call the model API. Model availability and account usage allowances can vary. Use the team's agreed model when available; record any change. Record an unknown model snapshot as null rather than guessing. If rate-limited, save progress and resume later; smaller output chunks are preferable to rushed annotations.

## Initial calibration

1. Read `calibration/CAL_001.md`, `CAL_002.md`, and `CAL_003.md` yourself. They contain four cases each, twelve total, all from 2010–2020.
2. Before seeing LLM answers, record your own eligibility and current appellate outcome with one supporting passage per case in `submissions/<you>/independent_calibration_notes.md`. Include uncertainty; do not search the prior audit labels.
3. Open a fresh chat with your own calibration files and shared instructions. Paste START_HERE, replacing the reviewer identifier and stating the exact input filename. Do not provide your human labels or another person's outputs as hints.
4. Ask the assistant to identify the four case IDs and confirm it can access all passages. Confirming access is not completion of annotation.
5. Paste ANNOTATE_CHUNK. Require a JSON array of exactly four annotation objects, plus a brief review table outside that JSON. If the assistant supports downloadable files, request `<chunk_id>.json`; otherwise copy only the JSON array into a UTF-8 file with that name.
6. Validate the output. If it fails, provide the error report and relevant source passages and ask for a corrected complete file. Do not tell the assistant to change values merely to make validation pass. If substantive evidence is missing, use review/null as appropriate.
7. Save the original response before correction as `<chunk_id>.draft-v1.json`. Save the corrected submission as `<chunk_id>.json`; keep original drafts outside the set of files passed to merge.
8. Repeat for all three chunks. Keep each output local and merge your own twelve records with the README command. Do not compare with teammates until all three independent submissions exist.
9. Compare the LLM output with your independent human notes and record differences. Do not silently replace the LLM draft with the human conclusion; keep both for calibration analysis.

## Compare calibration and agree on starting rules

Coordinator gathers the three **independent** `calibration.jsonl` files and validates them separately. Run from a complete repository copy:

```sh
python scripts/compare_calibration.py submissions/yinkui/calibration.jsonl submissions/becca/calibration.jsonl submissions/hyunsang/calibration.jsonl --output submissions/calibration_comparison.json
```

This reports pairwise agreement and Cohen's kappa for core fields, plus a disagreement queue. It is a consistency diagnostic on twelve examples, not an accuracy estimate. The team must read the evidence and independent human notes before deciding the adjudicated label. Do not let majority voting automatically create ground truth.

Use `docs/DECISIONS.md` to record the actual rule decision, date, people, version, and cases requiring re-annotation. Initial 1.0.0 is a proposed starting version, not falsely described as already team-approved. Once the team agrees, record that freeze. Any later rule change must identify affected records and how they will be reviewed again.

## Shared rounds: A, compare A, then B and C

All three people annotate the same full round independently. Start with A (169), compare and review A, then repeat for B (169) and C (168). Use the same codebook version and exact batch manifest, but separate conversations and reviewer folders. No partition rotation or exclusive owner is used.

- Work in `batches/A/chunks/`, at most five cases per input. Save selected outputs in `submissions/<reviewer_id>/batches/A/chunks/` and original responses in that round's `drafts/` folder.
- Validate each chunk and merge selected outputs using `batches/A/manifest.json`. Do not mix historical drafts or validation reports into the merge.
- Freeze each person's `annotations.jsonl` before opening peer answers. Preserve the source/codebook version and a file hash or Git commit.
- Once all three A submissions are complete and valid, use the comparison command in [DELIVERABLES.md](DELIVERABLES.md), review disagreements and sample unanimous inclusion/exclusion decisions. Record actual human decisions and unresolved items.
- Write one consolidated A record per case; do not merge three overlapping reviewers' records into a case dataset. Then continue to B and C.
- If a rule changes, document its version, the training evidence supporting the change and affected prior cases. Do not tune the prompt using held-out evaluation cases.
- Existing calibration/optional pilot records can count within their manifest round. Keep each ID once, reuse only your own work under compatible rules, and record prior exposure to shared answers. Shared calibration is development data and should be reported separately from fresh independent agreement.

`SUNDAY_PILOT.md` is optional practice material retained for convenience, not a required five-case/ring-review stage. A smaller MVP may use the reviewed eligible subset of A if time is tight; see the README for evaluation limitations. No human review is implied by three LLM runs.

## Resuming / troubleshooting

| Problem | Action |
|---|---|
| Assistant says it cannot see the file | Reattach the actual file or paste the current case text. Do not accept summaries from memory. |
| JSON stops halfway through | Keep it as an incomplete draft; request fewer cases. Invalid partial JSON is not a submitted annotation. |
| Quote mismatch | Copy exact source punctuation and OCR. Use two quotes if evidence spans passage boundaries. |
| Missing field or issue | Return schema errors; ask for a complete corrected object with all required topics. |
| Conflicting outcomes | Re-read all current order paragraphs; preserve per-order outcomes and use mixed/review where appropriate. |
| Ownership unclear | Use review; do not search the web or infer from a corporate defendant. |
| Assistant labels everything with certainty | Ask it to reassess only evidence-supported judgments and explicit unknowns. Confidence is not a substitute for support. |
| No file-generation tool | Copy JSON arrays to local `.json` files and validate later. |
| No local Python | Submit outputs and indicate validation pending; coordinator can run the scripts. |
| Model usage limit | Save outputs/progress; resume when available. Log a model change if the team switches models. |
| No GitHub write access | Send your submission folder ZIP to the coordinator. Do not change repository visibility. |

