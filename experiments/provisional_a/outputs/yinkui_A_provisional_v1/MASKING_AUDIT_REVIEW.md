# Pre-model masking audit — assistant review, not human approval

Reviewed on 2026-10-23 against the full cleaned opinions and the removed sentences in MASKING_AUDIT_PACKET.md, before fitting any models. Two seeded cases per class per development split: eight opinions total. Training examples informed a repair to judicial-concurrence footer removal. The four validation examples were inspected after that repair; their findings below did not change the masking rules. No test opinion was inspected for this audit. Reviewer: the coding assistant; human review remains pending.

The target is the whole current appeal's affirmed/reversed outcome, not who won the original motion. Historical lower-court rulings and cited precedents should remain. Removing the final disposition does not turn a published opinion into a pre-decision prediction task: judicial reasoning itself can strongly imply the answer.

| Case | Split / label | Current whole-appeal outcome | Useful reasoning / earlier decisions | Assessment |
|---|---|---|---|---|
| NY-4394527, Fellner | Training / 0 | Opening affirmance removed | Surveillance and notice reasoning remain; earlier appeal dismissal and Bray/Cox references remain | Pass on sampled criteria |
| NY-6004283, Germain | Training / 0 | Operative affirmance and express approval of appealed ruling removed | Rug dimensions, trivial-defect reasoning and expert evidence remain; historical grant of summary judgment retained | Pass on sampled criteria; some reasoning is lost with the approval sentence |
| NY-5934687, Williams | Training / 1 | Ordered reversal and repeated motion disposition removed | Mat, creation/notice, proof and precedents remain; original denial retained | Pass on sampled criteria |
| NY-4253165, Keum Ok Han | Training / 1 | Ordered reversal and concluding should-have-granted sentence removed | Out-of-possession and notice reasoning and earlier trial ruling remain | Pass on sampled criteria |
| NY-9355453, Cheprakova | Validation / 0 | Operative affirmance and concluding approval removed | Causation, speculation, surveillance and precedents remain; the historical grant remains in a later sentence | Partial: sentence segmentation joins the first historical ruling ending in “Inc.” to the Ordered sentence, so some history is unnecessarily removed |
| NY-5302167, Luttenberger | Validation / 0 | Operative affirmance and concluding approval removed | Threshold facts, open/obvious reasoning, precedents and earlier motion disposition remain | Pass on sampled criteria |
| NY-4929051, Zubillaga | Validation / 1 | Both opening reversed orders removed | Extensive warning-sign and notice reasoning and earlier default rulings retained | Whole-appeal target removed, but current leave-to-appeal and ancillary motion results remain. Hayden should confirm eligibility for this procedural-plus-merits, multiple-order opinion |
| NY-7857572, Yerry | Validation / 1 | Ordered reversal and concluding should-have-denied sentence removed | Notice/remedial-measure reasoning, earlier ruling and many precedents remain | Partial: “Supreme Court properly considered” also removes an evidentiary ruling and its precedents, although it does not state the whole appeal's result |

All eight sampled whole-appeal dispositions were removed; this is not a corpus-wide leakage clearance. Six had no material failure on the specified sampled criteria, while two show avoidable collateral removal. Zubillaga additionally illustrates the need to define the boundary for ancillary procedural outcomes. These are qualitative observations, not an estimate of masking accuracy.

## Training-set outliers, inspected separately

- NY-5936535: 85 of 149 words (57.0%) removed. The opinion is extremely short; its final sentence combines direct appellate approval, reasoning and precedents. Whole-sentence removal retains basic accident facts but loses most of the explanation. Flag for human review, not automatic exclusion.
- NY-4619223: more than 30% removed, including an introductory summary-judgment sentence that also contains accident context. Flag for human review. The initial excerpt was inspected; do not count this as a full semantic review of that opinion.

## Frozen prototype decision

Run the present rules unchanged, retain all included development cases, and report these limitations. The five matched-word-budget random-removal runs are central to interpretation. This trial is a diagnostic of the masking strategy, not evidence that a final mask is ready. Becca and Hayden should review collateral loss and residual cues using development opinions before finalizing the production pipeline. Any revision must have a new mask version/run name and a rerun of all conditions; do not use test outcomes to revise rules.
