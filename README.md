# legal-judgment

NYU Tandon Machine Learning Final Project — 506 provisional New York slip/trip-and-fall opinions.

## Current MVP checkpoint — October 25, 2026

The team-reviewed Partition A integration is complete: **120 selected cases, 119 assigned (86 train / 16 validation / 17 reserved test), and one companion-appeal hold**. The end-to-end notebook runs the baselines, frozen LEGAL-BERT comparison, masking checks and five-seed random-removal control. Model results are preliminary validation findings; the test period has not been evaluated.

- [MVP results, protocol and reproduction](experiments/mvp_a/README.md)
- [Executed notebook](experiments/mvp_a/Team_11_MVP.ipynb)
- [IEEE checkpoint report — LaTeX project](reports/Team_11_MVP_IEEE/main.tex)

The workflow below remains the plan for later annotation rounds. Original draft statuses and the earlier provisional experiment are preserved as historical records.

## Current plan: everyone does A, then B, then C

All three teammates independently annotate the **same batch**, then compare before moving on. The batches are rounds, not exclusive assignments to people.

| Round | Each person annotates | Then we do together |
|---|---:|---|
| A — start here | 169 cases | Compare all three submissions, review disagreements and audit agreement |
| B | 169 cases | Repeat the comparison and review |
| C | 168 cases | Repeat, then consolidate all 506 case decisions |

At full completion, each person has covered all 506 cases: 1,518 individual annotation records, consolidated into at most 506 unique case decisions. Cases marked exclude or review stay in the records with reasons; the usable binary dataset will be smaller.

Start with [the teammate README](annotation/README.md). Everyone downloads [batch A](annotation/downloads/batch_A.zip) first, works in their own reviewer folder, and saves their independent answers before opening other people's outputs. Continue in small chunks; do not ask an LLM to process all 169 in one response.

## Next steps

1. Agree on the starting codebook using the calibration questions. Existing calibration work can be reused within its actual batch where the rules still apply; record prior exposure to shared answers.
2. Everyone completes A independently, including eligibility, outcome, facts, issues and evidence. Validate and freeze the three original submissions.
3. Compare A, resolve disagreements with source evidence, and audit a random sample of unanimous inclusions **and exclusions**. Three LLM runs can share mistakes; agreement is not human gold.
4. Record actual decisions and any rule changes, then repeat for B and C. Recheck earlier affected cases if rules change. Avoid tuning rules using held-out evaluation cases.

The previous one-person-per-batch assignment and five-case ring-review plan are superseded. The five-case pilot packets remain optional practice inputs, not an extra required stage.

## Smaller MVP if time is tight

A reviewed **batch A (169 candidate cases, approximately 170)** can be the MVP starting pool. This does not promise 169 eligible examples: report the actual retained count, exclusions, unresolved cases and class counts after review. Do not relax eligibility to hit a target size.

Compare TF-IDF + logistic regression, TF-IDF + linear SVM, and frozen LEGAL-BERT features + a linear classifier on the same reviewed cases and splits when feasible. Report **accuracy, balanced accuracy, macro F1, a confusion matrix and class counts**, plus split sizes and text-length/truncation statistics. Inspect class counts after filtering before choosing an evaluation design; a small test set may only support exploratory conclusions. A/B/C are not train/validation/test splits. The detailed README explains the smaller-MVP checks.

We can discuss progress and open questions on Monday and agree on a manageable pace. No Friday work, exact-hour deadlines or requirement to finish A before Monday is implied.

## Downloads and references

- [Batch A — 169 cases](annotation/downloads/batch_A.zip)
- [Batch B — 169 cases](annotation/downloads/batch_B.zip)
- [Batch C — 168 cases](annotation/downloads/batch_C.zip)
- [Codebook](annotation/docs/CODEBOOK.md) · [Deliverables and commands](annotation/docs/DELIVERABLES.md) · [Flexible timeline](annotation/docs/TIMELINE.md)
- [Earlier calibration comparison](https://github.com/rweng18/legal-judgment/blob/annotations/yinkui-calibration/annotation/submissions/yinkui/comparison/REPORT.md) — read only after saving your independent calibration answers; the historical two-person report is not batch-A completion.

Annotation workflow updated October 18, 2026; current MVP summary added October 25. The substantive codebook and original draft files are unchanged. See the current MVP above for team review acceptance and completed classifier results.
