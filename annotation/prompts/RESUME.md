# Resume prompt

Resume Team 11 annotation from the attached/local files, not from assumed chat memory. Read README.md, CODEBOOK.md, AGENTS.md if local, the current schema, and the latest actual team decision log.

Reviewer: [REVIEWER_ID]. Batch: [A/B/C]. Current input: [CHUNK_ID]. Saved progress and outputs: [FILES]. First compare saved output IDs with the expected manifest and report completed, invalid, and missing IDs. Do not overwrite valid outputs or another person's work. Do not count validation-report JSON files as annotations.

Continue only the explicitly assigned missing/invalid cases. Read their complete source texts. Preserve original drafts, record supersedes on revisions, and use the currently agreed codebook/prompt version. Validate each completed chunk when tools permit and save a new checkpoint. Do not invent work completed in a prior session.

