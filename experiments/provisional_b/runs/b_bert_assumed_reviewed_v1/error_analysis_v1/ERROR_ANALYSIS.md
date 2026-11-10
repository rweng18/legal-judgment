# Batch B development error analysis

This qualitative review covers **eight cases** from the saved 15-case development evaluation: all five cases with a FULL/MASKED disagreement in any learned model, one error shared by every model, one short-opinion encoder error, and the longest opinion as a comparison case. Both complete text variants and the removal logs were read for these eight cases. This is a deliberately selected diagnostic sample, not an estimate of error-category prevalence. The other seven cases were inventoried from saved predictions and lengths but not substantively reviewed here.

The source is `b_bert_assumed_reviewed_v1`, with its original label-review assumption and provisional families. Labels are **0 = affirmed; 1 = reversed/vacated**, referring to the current appellate disposition, not who benefits or what the trial court previously ordered. This review makes no label corrections or new adjudications. Failed predictions remain in the evaluation, and no models, thresholds, masking rules, or settings were changed.

## Sample and preserved predictions

Each prediction pair is **FULL / MASKED**. The majority classifier predicts **0 / 0 for every case**. Token counts exclude special tokens. Chunk counts refer to LEGAL-BERT; the lexical models do not use these chunks.

| Case | Saved label | TF-IDF LR | TF-IDF SVM | LEGAL-BERT LR | Content tokens F/M | Chunks F/M | Selection reason |
|---|---:|---|---|---|---|---|---|
| NY-4860863 | 0 | 1 / 0 | 1 / 1 | 0 / 0 | 779 / 751 | 2 / 2 | LR disagreement; procedural-history contrast |
| NY-5312913 | 0 | 0 / 0 | 0 / 0 | 1 / 0 | 935 / 897 | 2 / 2 | Encoder disagreement; longest opinion with a learned-model error |
| NY-6459053 | 0 | 0 / 0 | 0 / 0 | 0 / 1 | 580 / 528 | 2 / 2 | Encoder disagreement; residual reasoning and citation fragment |
| NY-6475974 | 1 | 1 / 0 | 1 / 0 | 1 / 1 | 527 / 478 | 2 / 1 | Both lexical models lose a correct reversal after masking |
| NY-9355448 | 0 | 0 / 0 | 0 / 0 | 0 / 1 | 595 / 539 | 2 / 2 | Encoder disagreement; procedural reasoning |
| NY-4898123 | 1 | 0 / 0 | 0 / 0 | 0 / 0 | 639 / 549 | 2 / 2 | Shared error in both variants, including majority |
| NY-8511862 | 0 | 0 / 0 | 0 / 0 | 1 / 1 | 486 / 457 | 1 / 1 | Short narrative; encoder error without chunking |
| NY-5302359 | 0 | 0 / 0 | 0 / 0 | 0 / 0 | 2617 / 2594 | 6 / 6 | Longest development opinion; correctly classified control |

Across all 15 development cases, LR disagrees across variants on 2 cases, SVM on 1, and LEGAL-BERT on 3: 6 model-case disagreements across 5 distinct cases. For LR, masking fixes one error and introduces one, leaving accuracy at 80%. For SVM it introduces one error. For LEGAL-BERT it fixes one and introduces two. These are paired observations from separately trained FULL and MASKED pipelines at fixed C; they are **not** a same-model deletion experiment or proof that a particular removed phrase caused a prediction.

## Residual outcome cues

Masking removes operative dispositions and explicit statements that the lower court “properly” or “should have” ruled a particular way. It still leaves substantial retrospective appellate reasoning. These are indirect outcome cues, even when the words “affirmed” or “reversed” are absent. The selected cases do not establish a surviving direct operative disposition in MASKED text.

- **NY-6475974:** MASKED retains “Here, the defendant established its prima facie entitlement to judgment as a matter of law dismissing the complaint” and the finding that the plaintiff failed to raise a triable issue. Coupled with the earlier denial of the defendant's motion, this reasoning points toward reversal. Both lexical models change from correct 1 to incorrect 0 after masking, while LEGAL-BERT remains correct. Residual reasoning remains useful, but is not reliably used by every model.
- **NY-5312913:** MASKED retains findings that the defendant established entitlement to judgment, lacked the requisite culpability, and that the plaintiff failed to raise a triable issue. LEGAL-BERT changes from incorrect 1 to correct 0. The improvement does not establish that removing outcome information is generally beneficial; the learned representations and fitted classifiers differ across variants.
- **NY-5302359:** The long MASKED opinion retains “we conclude that they have established triable issues of fact” and the statement that the defendants' remaining contentions lack merit. The current disposition is removed, but the appellate conclusion is not. Correct MASKED predictions therefore do not demonstrate prediction from neutral facts alone.

There is also a concrete text-cleaning artifact: **NY-6459053, NY-9355448, and NY-4898123** retain a citation tail beginning `Ctr. , 64 NY2d 851, 853 [1985]` after the masking log's removed sentence ends at `New York Univ. Med.`. This is consistent with an abbreviation being treated as a sentence boundary. It is an observed fragment, not evidence that the fragment caused any error. The frozen texts are preserved.

## Confused procedural history and the current appeal

**NY-4860863 — snow at a home visited by a letter carrier.** The defendants appealed a denial of summary judgment, and the appellate court affirmed. The MASKED text retains both the historical denial and the finding that the defendants failed to establish lack of constructive notice. This is a plaintiff-favorable result with label 0. LR changes from wrong 1 to correct 0; SVM is wrong in both variants. Their signed decision scores are very close to zero: LR +0.0086 / −0.0091 and SVM +0.0066 / +0.0053. These are threshold-adjacent decisions, not strong evidence of a particular semantic mechanism. Scores are not calibrated probabilities and should not be compared across model types.

**NY-6459053 — oil in a supermarket aisle.** The trial court denied the defendant's motion, and the appellate court affirmed. MASKED retains “the defendant failed to meet its initial burden as the movant” but removes the explicit affirmance and the sentence approving the denial. LEGAL-BERT changes from correct 0 to wrong 1. The distinction between a defendant losing its motion and a lower-court decision being reversed is essential; the two are not equivalent.

**NY-9355448 — worn carpet on a stair.** The defendant argued no defect, triviality, and lack of notice. Both courts left the claim standing; the saved outcome is affirmance. MASKED still says that the defendant failed to establish that the condition was not dangerous or defective, and that notice was not argued on appeal. LEGAL-BERT changes from correct 0 to wrong 1. Party arguments, negated findings, and the historical denial coexist in the input. Procedural-role or negation confusion is a plausible explanation, not an attribution demonstrated by these predictions.

**NY-4898123 — liquid on an apartment staircase.** This is the strongest shared failure: every model predicts 0 for both variants even though FULL explicitly says the order is reversed. The trial court had granted defense summary judgment, but the appellate reasoning says the defendant failed to eliminate triable issues about constructive notice. MASKED retains the historical grant while removing the reversal and “should have denied” sentence. The same defense-burden failure that supports affirmance in NY-6459053 supports reversal here because the appealed order differs. This illustrates why favorable/unfavorable reasoning cannot substitute for tracking the prior ruling. Failure even in FULL shows that an explicit outcome cue does not guarantee a correct learned prediction. The saved label 1 and both failed predictions are retained.

## Short factual narratives

**NY-8511862** has 359 FULL words and 336 MASKED words, only 486 / 457 content tokens, and one chunk per variant. Its factual description says merely that the plaintiff tripped and fell inside the defendant's premises; it does not describe a concrete obstacle. Most of the opinion discusses a causation argument, precedent, and burdens of proof. The generic rule says inability to identify a cause is fatal; the case-specific finding says the defendant **failed to establish** that the plaintiff did not know the cause. LEGAL-BERT predicts reversal in both variants despite the saved affirmance. Sparse factual detail plus negation and generic precedent is a plausible failure pattern. A missed chunk or 510-token cutoff cannot explain this case.

**NY-6459053** likewise gives a brief incident account, then devotes much of the text to notice and summary-judgment reasoning. “Short factual narrative” describes the limited factual substance, not simply a short whole-document token count. These opinions still contain considerable retrospective legal reasoning.

## Long-text failures and their limits

**NY-5312913** is the longest development opinion with any learned-model error: 935 / 897 tokens in two chunks. It combines common-law notice analysis with a separate General Municipal Law § 205-e claim. LEGAL-BERT fails on FULL and succeeds on MASKED. Multiple issues, boilerplate, and pooling across chunks could dilute or mix relevant signals, but this review does not isolate any of them as the cause. Both variants use two chunks, so the error is not simply a switch from one to multiple chunks.

**NY-5302359**, the longest opinion overall, is a useful counterexample: 2,617 / 2,594 tokens in six chunks, with conflicting weather reports, notice evidence, gutter testimony, and competing legal arguments. Every model is correct in both variants. All chunks contributed to the cached encoder vectors, including the final chunk; there was no first-510-token truncation. The other FULL opinion longer than two chunks is also correctly classified by every model, based on the prediction inventory; its text was not part of this qualitative sample.

For LEGAL-BERT, the full evaluation yields the following descriptive counts. These are too small to infer a reliable length effect, and masking moves one case between the one- and two-chunk groups.

| Chunk count | FULL errors / cases | MASKED errors / cases |
|---:|---:|---:|
| 1 | 1 / 2 | 1 / 3 |
| 2 | 3 / 11 | 4 / 11 |
| 3 | 0 / 1 | No cases |
| 6 | 0 / 1 | 0 / 1 |

Mean pooling can lose cross-chunk relationships even when all tokens are processed. That remains a methodological limitation and a hypothesis for later study, **not an established long-text failure in this sample**. No truncation-based failure is demonstrated here.

## Preservation and follow-up

The source snapshots, label file, family file, all 120 original prediction rows, metrics, splits, selection records, and embeddings are unchanged. `audit.json` records before/after checksums. `cases.json` supplies exact excerpt offsets into FULL/MASKED text, removal-log entries, lengths, saved labels, and all model outputs for the sample. `case_predictions.csv` is an unmodified-value copy of the 64 sampled prediction rows; `development_inventory.csv` covers all 15 evaluation cases, including unsampled errors and correct predictions.

The evidence supports reporting residual reasoning cues, procedural-role ambiguity, and sparse facts as recurring diagnostic themes. It does not prove how a specific feature drove a prediction. These development observations must not be used to quietly repair frozen labels or masks and replace the reported scores. Any later protocol change should be developed using training data, assigned a new version, and evaluated with the original failed predictions still available. Any genuine label concern requires separate documented human review; this analysis does not promote review status or propose a relabeling.
