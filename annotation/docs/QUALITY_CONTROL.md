# Quality control and review protocol

## What the scripts prove

The validator checks schema structure, allowed values, exact ID coverage, source hashes, genuine quotation matches, references to evidence, whole-passage coverage, and basic contradictions. The package audit verifies assignments, source integrity and blinded exports. Neither proves that an interpretation is legally or factually correct.

A quote can exist and still refer to a cited case, a losing party's argument, or the wrong stage of litigation. Reviewers must inspect the context. Read the complete controlling opinion before accepting the label.

## Independent calibration

Each teammate reads the same 12 training-period opinions and records their own eligibility and current outcome before seeing model output. Then each runs the LLM independently without others' answers. Keep raw model drafts separate from human decisions. Compare only after all three submissions are saved. Do not treat agreement between three uses of the same model as three independent human votes.

Discuss disagreement about private control, nonfall accidents, procedural-only decisions, multiple orders and current outcome. Resolve with exact passages and codebook rules. If the text cannot resolve the issue, retain review status. Do not expand eligibility simply to increase the sample size.

Record pairwise agreement/kappa as a small-sample diagnostic. A null kappa can occur when expected chance agreement is one; it is not zero agreement. Twelve mostly easy provisional cases cannot establish corpus-wide accuracy or exclusion recall. The calibration set is development data and must never be described as a held-out evaluation of annotation quality.

## Sunday pilot review

A reviews B; B reviews C; C reviews A. The second person first reads the source without the primary output and records eligibility/outcome. Then check the primary's full annotations and quotes. Explain changes in an adjudication note. Five pilot cases per batch is a workflow check, not enough to certify the entire batch.

If a material rule changes after the pilot, increment the prompt/codebook version and review affected training records before production. Do not use validation/test case inspection to tune the annotation prompt. Individual evaluation-label adjudication may happen under frozen rules, but prompt changes belong to training examples.

## Production review

1. Review every flagged or inconsistent record. Missing/ambiguous source evidence is a valid unresolved result.
2. Draw the seeded random 10% audit of accepted training records from a fixed merged version. Review those source opinions and annotations. Preserve the audit denominator and disagreements. Add targeted checks separately; do not mix their rates into the random-sample error estimate.
3. All proposed validation/test candidates need independent human eligibility/outcome decisions without initial LLM labels or model predictions. A second human resolves disagreement/ambiguity. If not fully reviewed, they cannot be used as human-gold evaluation cases.
4. Check potential duplicate/related litigation using names, dockets, decision dates and text. The provided family hints are incomplete and may contain false matches. Do not assume two different cluster IDs are independent disputes.

## Recording human review

Maintain independent notes with case ID, human eligibility, human outcome, quote/passage, uncertainty, reviewer and date. Keep the original LLM JSON untouched. For a revised annotation, set supersedes to the original filename and explain changes. Set human_reviewed only after a person checks eligibility/outcome and the record's substantive annotation fields; otherwise keep llm_draft and describe which limited checks were done separately. Adjudicated status requires an actual human resolution and note.

## Leakage and future use

- The full text contains the answer; using it to label is appropriate, but labels and evidence selections must not enter classifier features.
- Court findings, favors, current-outcome passages, and reasoning summaries are post-outcome information. Extra features are useful for descriptive analysis, not automatically safe for prediction.
- Annotated outcome spans on evaluation cases are for auditing, not manual gold-guided masking of test inputs.
- Training/validation/test periods are preliminary. Case families spanning boundaries require a documented handling decision before model fitting.
- No model accuracy, balanced accuracy, macro F1, or classifier confusion matrix exists yet. This phase produces counts and annotation agreement, which are different quantities.

