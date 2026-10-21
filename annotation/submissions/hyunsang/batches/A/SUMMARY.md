# hyunsang — complete independent A submission

169/169 source IDs, A_001–A_034. No pending chunks. Selected output: annotations.jsonl.

| Decision | Count |
|---|---:|
| Include | 132 |
| Exclude | 13 |
| Review | 24 |
| Total | 169 |

Included binary labels: affirmed 0 = 86; reversed/vacated 1 = 46. These are annotation counts, not classifier results.

Every supplied opinion passage was read in full before its chunk was labeled. Each original draft-v1 was saved before validation; revisions preserve earlier drafts and supersedes links. Every selected chunk passes, and the complete merged output passes without partial mode: 169 unique expected IDs; zero missing/extra IDs and validation errors; source hashes, evidence offsets, schema, topics, passage coverage and contradictions checked.

All 169 records are llm_draft. No human review or adjudication is claimed. The 24 review decisions retain null binary labels; all exclusions also retain null labels. Every record, including 132 inclusions, still requires the appropriate human checks before it can be called gold. The summary script's seeded audit IDs and proposed period counts are unperformed review candidates, not completed audits or approved evaluation splits.

Source snapshot: 239379ca278b285f846dfa7d2371570e40ac900a. Schema/prompt: initial 1.0.0; DECISIONS.md records no substantive team freeze. Actual session model name: GPT-6; unobservable snapshot version null. No API annotation calls, extra agents, training or external case research.

No peer submission, peer summary or comparison file was read. No peer comparison/consolidation was performed. The calibration phase was not rerun. Historical calibration discussions were visible in conversation context; they are not fresh blinded examples. NY-5992200 is specifically marked for that prior context exposure. Original exact user instructions and applied shared templates are in prompts_used/.

Evidence precision: exact narrow controlling-disposition quotations are separate from retained broad passage-level evidence. Broad passages may mix allegations, testimony, history and findings; their statement_status is therefore unclear rather than falsely calling the entire passage a court finding. Human review must check which exact words support each substantive field; genuine quotation matching alone does not prove the interpretation. Explicitly selected indirect-reasoning cues and literal repeated rulings are retained for diagnostic masking audit, not automatic model inputs.

Three assistant-evidence-refinement attempts encountered validation failures while narrowing quotations; failed intermediate drafts were preserved. The selected final files all pass. No eligibility/outcome label was changed by quotation or cue refinement. Earlier source-based corrections are documented in corrections.md. Broad evidence and the conservative private-boundary / mechanism decisions deserve human attention.

The family note for Coreano identifies related but distinct appellate decisions. Two-order decisions and ancillary appellate motions are described in their records; do not treat family membership as independent cases for future splits.

Output SHA-256: 842f85a6374c6f854521e4a25fa0eabf7da7d2d9288b982930efe5d80144f2a2.

GitHub has not been updated by this run. This is the reviewer's independent draft submission for later authorized upload and team review.
