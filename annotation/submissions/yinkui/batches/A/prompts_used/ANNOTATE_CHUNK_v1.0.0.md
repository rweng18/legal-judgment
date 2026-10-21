# Annotation prompt (version 1.0.0)

Annotate every case in the current input, reading all its passages. Return one JSON object per expected ID using annotation.schema.json, preferably as a downloadable JSON array named [CHUNK_ID].json. If downloadable files are unavailable, return the complete JSON array in one code block with no commentary inside it.

For each case:
1. Determine scope and binary-task inclusion separately. Include only evidence-supported private-premises slip/trip negligence merits appeals with a clear whole current disposition. Exclude definite mismatches; use review for uncertainty.
2. Record the full disposition category and per-order results. Set binary_label only for eligible affirmed (0), reversed/vacated (1); otherwise null.
3. Extract factual fields and every one of the 19 legal-issue topics, keeping allegations, arguments, testimony, court findings and dispositions distinct. Unknown is not false. A triable issue is not a final liability finding.
4. Identify evidence types actually discussed; classify every passage; collect direct and indirect outcome cues separately.
5. Attach exact, continuous evidence quotes with passage IDs and local evidence IDs. Do not alter source punctuation or OCR. Reuse evidence IDs where appropriate. Do not invent character offsets; the validator computes them.
6. Copy the exact case ID/hash, current chunk ID, schema/prompt version and actual run metadata. Always start with llm_draft. Give a short evidence-based finding, not private chain-of-thought reasoning.

Check that no case is omitted, all fields are present, all topics/passages are covered, and included labels have sufficient support. If output limits prevent finishing, identify the unfinished IDs and request a smaller subchunk; never claim partial work is complete.

After the JSON, give a compact table of case ID, include/exclude/review, outcome, and issues requiring human attention. This table does not replace the JSON deliverable. If local code is available, run the supplied validator and report its real result; otherwise state validation pending.

