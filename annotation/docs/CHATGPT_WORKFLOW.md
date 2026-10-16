# Running the annotation with ChatGPT or a local assistant

## Choose your workflow

**Uploaded-file ChatGPT:** download and extract your batch ZIP locally; attach the codebook, schema, and a single input `.md` file to the chat. Paste the start prompt. A ChatGPT project can keep shared instructions and uploaded sources across chats, but it does not automatically read local folders. See [official project documentation](https://learn.chatgpt.com/docs/projects). Avoid a shared chat/project that exposes other people's calibration answers before independent submission.

**Local assistant with file access:** open the extracted `annotation/` folder, or the repository's annotation folder, as the workspace. Tell the assistant your batch and reviewer ID and ask it to read `AGENTS.md` and `README.md`. Specify one chunk at a time initially. The assistant can run Python scripts locally; no API service is needed.

This workflow does not automate the ChatGPT website, use account credentials, or call the model API. Model availability and account usage allowances can vary. Use the team's agreed model when available; record any change. Record an unknown model snapshot as null rather than guessing. If rate-limited, save progress and resume later; smaller output chunks are preferable to rushed annotations.

## Saturday: independent calibration

1. Read `calibration/CAL_001.md`, `CAL_002.md`, and `CAL_003.md` yourself. They contain four cases each, twelve total, all from 2010–2020.
2. Before seeing LLM answers, record your own eligibility and current appellate outcome with one supporting passage per case in `submissions/<you>/independent_calibration_notes.md`. Include uncertainty; do not search the prior audit labels.
3. Open a fresh chat with your own calibration files and shared instructions. Paste START_HERE, replacing the reviewer identifier and stating the exact input filename. Do not provide your human labels or another person's outputs as hints.
4. Ask the assistant to identify the four case IDs and confirm it can access all passages. Confirming access is not completion of annotation.
5. Paste ANNOTATE_CHUNK. Require a JSON array of exactly four annotation objects, plus a brief review table outside that JSON. If the assistant supports downloadable files, request `<chunk_id>.json`; otherwise copy only the JSON array into a UTF-8 file with that name.
6. Validate the output. If it fails, provide the error report and relevant source passages and ask for a corrected complete file. Do not tell the assistant to change values merely to make validation pass. If substantive evidence is missing, use review/null as appropriate.
7. Save the original response before correction as `<chunk_id>.draft-v1.json`. Save the corrected submission as `<chunk_id>.json`; keep original drafts outside the set of files passed to merge.
8. Repeat for all three chunks. Keep each output local and merge your own twelve records with the README command. Do not compare with teammates until all three independent submissions exist.
9. Compare the LLM output with your independent human notes and record differences. Do not silently replace the LLM draft with the human conclusion; keep both for calibration analysis.

## Compare and freeze rules

Coordinator gathers the three **independent** `calibration.jsonl` files and validates them separately. Run from a complete repository copy:

```sh
python scripts/compare_calibration.py submissions/yinkui/calibration.jsonl submissions/becca/calibration.jsonl submissions/hyunsang/calibration.jsonl --output submissions/calibration_comparison.json
```

This reports pairwise agreement and Cohen's kappa for core fields, plus a disagreement queue. It is a consistency diagnostic on twelve examples, not an accuracy estimate. The team must read the evidence and independent human notes before deciding the adjudicated label. Do not let majority voting automatically create ground truth.

Use `docs/DECISIONS.md` to record the actual rule decision, date, people, version, and cases requiring re-annotation. Initial 1.0.0 is a proposed starting version, not falsely described as already team-approved. Once the team agrees, record that freeze. Any later rule change must identify affected records and how they will be reviewed again.

## Sunday pilot and ring review

After the rules freeze, annotate `batches/<your batch>/SUNDAY_PILOT.md` as `<your batch>_pilot`, using the same schema. These five cases are in your assignment and do not overlap calibration or the other pilot sets. Save `pilot.jsonl` and validate it against `SUNDAY_PILOT.expected.json`.

Cross-review: **A reviews B, B reviews C, C reviews A.** Each ZIP includes the other pilot inputs. Reviewers first read the five target opinions and write independent eligibility/outcome notes without viewing the target's output. Then compare the draft and verify supporting quotations, factual fields and discussed legal issues. Save a review note and a corrected copy, never overwrite the original submission. Clearly distinguish confirmed facts, unresolved items, and changes.

Do not mark a record human_reviewed merely because the model checked its own output. Actual human review and the person's name are required. If only the core labels were checked, keep the overall record llm_draft and describe the limited human check in the review notes until the rest is checked.

## Production after the meeting

- Use your assigned `batches/A|B|C/chunks/*.md` files and matching `.expected.json` files. A person may finish earlier training-only chunks after calibration if the team agrees, but keep evaluation labels separate from prompt tuning.
- Start with five cases per response; split further if output is truncated. Preserve original case IDs and the parent chunk ID. If using one-case outputs, merge the selected five files against that chunk's expected manifest.
- Do not upload all 169 opinions and ask the assistant to “do everything.” Require explicit full-text reading, case-by-case output, and a checkpoint after each chunk.
- Reuse prior approved pilot/calibration records for those primary IDs only after checking the codebook version. Mark the actual original input_chunk_id; do not fabricate a new run. Never include duplicate copies of the same case in final batch files.
- If the instructions change, record a new prompt version and re-annotate affected cases; do not silently mix versions.
- Keep a local progress file listing completed chunk IDs, pending IDs, validation failures and unresolved questions. A new chat must resume from saved files, not from a claim that it remembers a previous session.

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

