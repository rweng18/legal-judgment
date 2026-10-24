# PROVISIONAL — Partition A trial results

> **NOT FINAL PROJECT RESULTS.** This October 23, 2026 trial uses only Yinkui's independent LLM-draft annotations. It predates Hayden's adjudication and Becca's finalized dataset preparation. Labels, eligibility and masking remain provisional. The team will rerun the experiments on the reviewed dataset.

The trial started with 169 A candidates: 122 were marked include, 36 review and 11 exclude. The included cases provide **89 training, 16 validation and 17 reserved test cases**. All reported scores use validation only; the final test set was not evaluated. With only eight validation cases per class, small score differences are unstable.

- **[Results report](REPORT.md):** metrics, class counts, FULL/MASKED comparisons, five random-removal LR controls, text lengths and limitations.
- **[Executed notebook](provisional_A_results.ipynb):** saved results and independent metric checks.
- **[Masking audit](MASKING_AUDIT_REVIEW.md):** eight-case assistant review, including collateral removal; human approval remains pending.
- **[Initial error observations](ERROR_OBSERVATIONS.md):** four qualitative examples, not legal adjudications.
- **[Reproduction and reviewed-rerun instructions](../../README.md).**

At fixed C=1, validation balanced accuracy was:

| Model | FULL | MASKED |
|---|---:|---:|
| Majority baseline | 50.00% | 50.00% |
| TF-IDF + logistic regression | 68.75% | 62.50% |
| TF-IDF + linear SVM | 75.00% | 50.00% |
| Frozen LEGAL-BERT + logistic regression | 93.75% | 56.25% |

The majority baseline is text-independent. Random-removal LR averaged 67.50% across five fixed seeds. These results suggest sensitivity to removed outcome language, but masking also removed useful reasoning. They do not establish a causal effect, a stable model ranking, or the ability to predict future judgments.

For independent label adjudication, use the original opinions and annotation workflow before inspecting model predictions. This results package should not be treated as an answer key.
