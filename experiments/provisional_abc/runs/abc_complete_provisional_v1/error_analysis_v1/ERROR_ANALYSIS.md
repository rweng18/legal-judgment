# A-C development error analysis

This review concerns `abc_complete_provisional_v1`, not the earlier B-only run. Eight development opinions were selected for qualitative inspection: two from A, two from B and four from C. Both complete FULL/MASKED texts and their upstream removal logs were read. The sample contains six cases with a variant disagreement, a short shared learned-model failure, and a long correct comparison case. Selection is diagnostic and deliberately nonrandom; it does not estimate the prevalence of semantic error categories. The other 34 evaluation cases were inventoried from predictions and lengths only.

The saved target is the **current appellate disposition**: 0 affirmed; 1 reversed/vacated. It is not the winning party or the earlier trial-court ruling. A retains its team-reviewed status; B/C retain their explicit provisional assumptions and pending source review statuses. No labels, eligibility decisions, masks, model settings or predictions were changed.

## Preserved case-level results

Each prediction pair is **FULL / MASKED**. Majority predicts **0 / 0** for every case. Token counts exclude special tokens; chunk counts refer to the frozen encoder, not TF-IDF.

| Case | Batch | Saved label | TF-IDF LR | SVM | LEGAL-BERT LR | Content tokens F/M | Chunks F/M |
|---|---|---:|---|---|---|---|---|
| NY-4929051 | A | 1 | 0 / 0 | 0 / 0 | 1 / 0 | 2320 / 2147 | 5 / 5 |
| NY-5304378 | A | 1 | 1 / 0 | 1 / 0 | 1 / 0 | 1187 / 965 | 3 / 2 |
| NY-8511862 | B | 0 | 1 / 1 | 1 / 1 | 1 / 1 | 486 / 457 | 1 / 1 |
| NY-6459053 | B | 0 | 1 / 1 | 0 / 1 | 0 / 1 | 580 / 528 | 2 / 2 |
| NY-5957906 | C | 1 | 1 / 0 | 1 / 0 | 1 / 0 | 585 / 475 | 2 / 1 |
| NY-9301972 | C | 0 | 0 / 0 | 0 / 0 | 0 / 1 | 367 / 367 | 1 / 1 |
| NY-4894160 | C | 0 | 0 / 1 | 0 / 1 | 0 / 0 | 708 / 637 | 2 / 2 |
| NY-6476214 | C | 1 | 1 / 1 | 1 / 1 | 1 / 1 | 2499 / 2461 | 5 / 5 |

Across all 42 evaluation cases, LR changes predictions on 10 cases, SVM on 14, and LEGAL-BERT on 21. That is 45 model-case disagreements across 27 distinct cases. Relative to FULL, MASKED fixes 0 / 0 / 2 errors and introduces 10 / 14 / 19 for LR / SVM / LEGAL-BERT respectively. These are descriptive paired results, not evidence that each disagreement was caused by text removed from that particular opinion.

## Residual outcome cues

**NY-9301972 (C): a direct disposition survived masking.** The opening sentence ends “unanimously affirmed, without costs.” It is the current appellate result, not a cited precedent. The removal log contains no removals; FULL and MASKED are exactly identical, at 269 words and 367 content tokens. Both lexical models predict the saved label 0. LEGAL-BERT predicts 0 for FULL and 1 for MASKED.

The saved FULL/MASKED encoder vectors for this case are also exactly equal. The downstream pipelines are separately trained, including their scalers, so they can disagree on the same vector even at fixed C. The saved signed decision scores are −0.4117 and +1.3276. This is concrete evidence that this case's flip is not due to removal of its own text. It also shows that an explicit surviving cue does not guarantee a correct classifier output. The masking miss is recorded without editing the frozen input.

**NY-5304378 (A): explicit criticism of the prior ruling remains.** MASKED retains “the Supreme Court improvidently exercised its discretion in not accepting the plaintiff's excuse of law office failure” and the finding that the plaintiff had potentially meritorious opposition. These are appellate conclusions, not neutral pre-decision facts. The operative reversal and two “should have granted” passages are removed, yet all three learned models change from correct 1 to wrong 0.

**NY-6476214 (C): the long correct control still contains strong outcome-related language.** Although “we reverse,” the operative order and one “erred in granting” sentence are removed, MASKED retains “In light of these unresolved issues, defendants were not entitled to summary judgment dismissing the complaint and their motion should have been denied.” This expresses the appellate court's conclusion about the appealed motion. All three learned models predict 1 in both variants. Their MASKED success therefore cannot be described as prediction from factual narrative alone.

In **NY-4894160** and **NY-6459053**, MASKED also retains case-specific burden-of-proof conclusions. Both contain a dangling citation tail beginning `Ctr. , 64 NY2d 851, 853 [1985]` after the removal log cuts a sentence at `New York Univ. Med.`. The fragment supports an abbreviation-boundary artifact; it does not establish that this artifact caused an error.

## Confused procedural history

**NY-5304378 (A) — default, vacatur and underlying merits.** The trial court first granted an unopposed defense summary-judgment motion, then denied the plaintiff's request to vacate that order. The current appellate disposition reverses the appealed order, vacates the earlier order and denies the defense motion. MASKED retains the historical grant, later denial, missed deadline, law-office explanation and competing merits findings. It also contains language about the defendant initially establishing entitlement to judgment followed by the plaintiff raising triable issues. Tracking which motion, party and stage each clause concerns is essential. All three learned models miss the reversal in MASKED. Procedural-role and burden-shifting confusion is a plausible interpretation, not demonstrated feature attribution.

**NY-5957906 (C) — a procedural win does not determine the merits outcome.** The appellate court accepts the defendant's good cause for a late summary-judgment motion but reverses the judgment because evidence raises issues about preexisting ice and notice. MASKED retains that the lower court “providently exercised its discretion in entertaining the late motion,” alongside the prior grant of summary judgment. It also retains that the defendant failed to demonstrate entitlement to judgment. All three learned models switch from correct reversal to incorrect affirmance. A locally favorable procedural ruling and a favorable whole-appeal outcome are different targets.

**NY-6459053 (B) — losing a defense motion can be an affirmance.** The plaintiff allegedly slipped on oil in a supermarket aisle. The trial court denied defense summary judgment; the appellate court affirmed. MASKED retains the defendant's failure to meet its initial burden, but removes the operative affirmance and approval of the lower court's denial. LR predicts reversal in both variants; SVM and LEGAL-BERT change from correct 0 to wrong 1. Contrast NY-5957906: defense-burden failure supports reversal there because the trial court had granted the motion. The same reasoning vocabulary can accompany opposite appellate labels.

**NY-4894160 (C) — contractor liability and negation.** A janitorial contractor appealed a denial of summary judgment after a shopper slipped on bleach at Target. The appellate court affirmed. MASKED retains the historical denial, the general contractual-duty rule and exceptions, and the finding that the contractor “failed to affirmatively demonstrate” that its daytime porters did not create the danger. Both lexical models switch from correct 0 to wrong 1; LEGAL-BERT remains correct. This supplies a contrast where the encoder handles the retained material successfully while the lexical models do not. No individual phrase is proven causal.

## Short factual narratives

**NY-8511862 (B) — one chunk, sparse facts, nested negation.** The incident description only says the plaintiff tripped and fell inside the defendant's premises; it supplies no concrete obstacle. FULL has 359 words / 486 tokens and MASKED 336 words / 457 tokens. Both fit one chunk. The opinion quotes the generic rule that inability to identify a fall's cause is fatal, then finds that the defendant **failed to establish** that the plaintiff did not know the cause. All three learned models predict 1 in both variants despite the saved affirmance. The majority baseline is correct here. Sparse facts, prominent generic precedent and nested negation are plausible diagnostic themes. This failure cannot be explained by missing later chunks.

**NY-9301972 (C)** is shorter still, at 269 words in each variant, and also occupies one chunk. Its same-text, same-vector disagreement reinforces that short documents can fail through the fitted classifier rather than truncation. “Short factual narrative” describes limited incident information; it should not be equated with the absence of retrospective judicial reasoning.

## Long-text failures

**NY-4929051 (A) — a five-chunk error with substantial procedural and factual context.** FULL has 1,796 words / 2,320 tokens; MASKED has 1,671 words / 2,147 tokens. Both use five chunks. The opinion interweaves competing testimony about wet-floor warnings, photographs, three adjournment stipulations, a default judgment, leave to appeal and negligence merits. MASKED removes the two opening reversal synopses but leaves historical dismissals, default-related discussion, the finding that the defendant failed to make its merits showing and an ancillary denied motion. LR and SVM predict 0 in both variants; LEGAL-BERT is correct on FULL and wrong on MASKED. Every learned model therefore misses the MASKED reversal.

All five chunks contributed to the encoder vector. This is an observed failure **on a long document**, not proof of truncation or that length caused the failure. Content-token-weighted mean pooling may dilute short decisive passages among lengthy factual and procedural discussion and cannot provide cross-chunk attention. That is a mechanism worth investigating later, not a conclusion established by this case.

**NY-6476214 (C)** is a useful longer comparison: 2,499 / 2,461 tokens, also five chunks. It discusses fall identification, notice, triviality, photographs and an engineer's evidence. All three learned models are correct in both variants, although majority is wrong. Its retained appellate conclusions limit its use as a clean factual-reasoning control. It nevertheless rules out a simple claim that five-chunk opinions necessarily fail.

For context, the full evaluation inventory gives these LEGAL-BERT error counts. Chunk membership can change with masking, so columns are not identical subsets.

| Chunks | FULL errors / cases | MASKED errors / cases |
|---:|---:|---:|
| 1 | 1 / 6 | 6 / 9 |
| 2 | 3 / 28 | 14 / 27 |
| 3 | 1 / 5 | 1 / 3 |
| 5 | 0 / 2 | 1 / 2 |
| 6 | 0 / 1 | 0 / 1 |

These small counts do not establish a monotonic length effect. No unprocessed-tail failure was found: the run processed every content chunk, including short final chunks.

## Preservation and appropriate follow-up

The review records observed text and predictions separately from hypotheses about why models failed. It is not a new annotation or a source of human-review approval. It does not alter eligibility, labels, family assignments, masks, thresholds or model selection. In particular, NY-9301972's retained disposition is **documented**, not silently removed before rescoring.

`cases.json` provides source-line references, exact evidence quotes with character offsets, original removal-log entries, text/vector equality checks and saved predictions. `case_predictions.csv` copies the 64 sampled prediction rows without changing values. `development_inventory.csv` retains a diagnostic inventory of all 42 cases; `diagnostics.json` records all-case disagreement and length counts. `audit.json` verifies that every original dataset/run file, including all 336 predictions, original scores, matrices, embeddings and package checksums, remains byte-identical.

Any future masking revision should be developed on training material, receive a new version and preserve this run. These development cases have now been inspected and must not be presented as untouched confirmation data for revisions prompted by this review. Any genuine label concern requires a separate documented review process; this analysis proposes no relabeling and does not claim a causal explanation for individual errors.
