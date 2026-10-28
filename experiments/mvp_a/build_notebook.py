"""Author a step-by-step notebook; its cells actually prepare, fit and evaluate."""
from pathlib import Path
import nbformat as n
HERE=Path(__file__).resolve().parent
def md(s):return n.v4.new_markdown_cell(s)
def code(s):return n.v4.new_code_cell(s)
cells=[
md('''# Team 11 — MVP and Evaluation Pipeline Checkpoint

**Team-reviewed data (October 25, 2026); preliminary development results.**

We classify **published New York private-property slip/trip-and-fall appellate opinions** as affirmed (0) or reversed/vacated (1). We do not predict future judgments or whether the plaintiff wins. Our question is whether models can still identify the outcome after direct outcome statements are removed.

This notebook demonstrates the five checkpoint requirements: a working core system, a data/evaluation pipeline, baselines, first experiments, and preliminary results. It runs the pipeline step by step, with reusable implementations in `pipeline.py`. Read its commented functions for the complete loops. Original teammate submissions and the earlier provisional trial remain unchanged.

The team confirmed independent review of Becca's and Hayden's work today. We record that confirmation in a new version; we do not retrospectively relabel old draft artifacts. The 2023–2024 test period remains sealed for the later final evaluation.'''),
md('''## 1. Environment and frozen inputs

Run from the repository with the documented Python environment. We use local opinion files and a pinned LEGAL-BERT checkpoint; no CourtListener token or paid annotation API is needed. This notebook may take several minutes when extracting embeddings for the first time. On repeat runs, cached embeddings are reused only if text IDs, hashes, model revision and pooling match.'''),
code('''from pathlib import Path
import sys, json
import numpy as np
import pandas as pd
from IPython.display import display, Markdown, Image

# Locate the repository independently of the notebook's launch directory.
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents]
            if (p / 'annotation/source/cases.jsonl').exists())
sys.path.insert(0, str(ROOT / 'experiments/mvp_a'))
import pipeline as p
pd.set_option('display.max_colwidth', 100)
display(p.read(p.HERE / 'team_review_confirmation.json'))
display(p.read(p.TRIAL / 'model_lock.json'))'''),
md('''## 2. Integrate the reviewed data and preserve chronological assignments

Becca's 114-case pool was selected by unanimous inclusion across three independent annotation submissions. Hayden accepted six additional candidates after review. We join by **case ID**, not row order, and preserve Becca's existing split assignments. All original FULL/MASKED strings are checked against her frozen exports. The additions use her same FULL v1 / MASKED v2 functions without changes.

One selected case, Sodhi, remains outside modeling because its companion-appeal identity/date is unresolved. Thirty-five review cases and 14 withheld cases remain outside the selected pool. Family and calibration restrictions apply before any model is fitted.

On Windows, Git can convert file line endings. The integration verifies canonical LF file bytes against committed Git blobs, retains Becca's structural input validator, and checks export/split/base-text hashes. This also resolves a path-separator problem in her original disk loader; it does not loosen the input contract.'''),
code('''# Rebuild deterministically; existing frozen artifacts must match exactly.
data, summary = p.prepare_dataset()
display(pd.DataFrame(summary['split_class_counts']).T.rename(
    columns={'0':'Affirmed', '1':'Reversed/vacated'}))
display({k: summary[k] for k in ['candidate_A','consensus_pool','accepted_additions',
    'selected_pool','pending_family','assigned_cases','remaining_review',
    'withheld_any_original_exclude','review_status','test_evaluated']})
assert len(data) == 102
assert {r['period'] for r in data} == {'train', 'validation'}
# 86 train / 16 validation enter models. The 17 test cases are metadata only.'''),
md('''## 3. Prevent label leakage and keep the unit of evaluation at the case level

The only model feature input is the cleaned opinion text. Labels are supplied separately to the training objective and scoring. Case names/IDs, review notes, extracted findings, selected evidence quotations and outcome metadata are never appended to features. All chunks from an opinion inherit that opinion's split. No known family crosses splits; calibration exposure is training-only.

Our labels describe the **current whole appeal**. A defendant can win a reversal, and a plaintiff can benefit from an affirmance of a denial of summary judgment. Learning “defendant wins” would therefore solve a different task.'''),
code('''train = [r for r in data if r['period'] == 'train']
validation = [r for r in data if r['period'] == 'validation']
assert not {r['family_id'] for r in train} & {r['family_id'] for r in validation}
assert all(not r['calibration_exposure'] or r['period'] == 'train' for r in data)
X_train_full = [r['texts']['FULL'] for r in train]  # Text strings only.
y_train = np.array([r['label'] for r in train])    # Separate supervision.
assert all(isinstance(text, str) for text in X_train_full)
display(pd.DataFrame([{'split':s, 'label':k, 'count':sum(r['label']==k for r in rs)}
                     for s,rs in [('train',train),('validation',validation)]
                     for k in [0,1]]))'''),
md('''## 4. Feedback 1 — audit masking before fitting models

We sample two cases from each class in both training and validation, before fitting. The coding assistant reads the full cleaned opinions and removed sentences and checks: (1) whether the current appeal outcome is removed, (2) whether useful reasoning remains, and (3) whether earlier rulings and precedents remain. This additional technical check is separate from the team's review confirmation.

The eight sampled main dispositions are removed, with substantial reasoning/history retained. The audit records remaining ancillary procedural outcomes and collateral loss of citations/reasoning. It is not a claim that the entire corpus is free of outcome cues. The rules are not changed in response to this validation audit.'''),
code('''audit = p.read(p.OUT / 'masking_audit_review.json')
assert set(audit['reviewed_case_ids']) == set(p.read(p.OUT/'mask_audit_sample.json')['case_ids'])
display(pd.DataFrame(audit['cases']))
print(audit['conclusion'])
# Show one TRAINING example so the intervention is concrete.
example = next(r for r in data if r['case_id'] == 'NY-4437532')
log = next(r for r in p.rows(p.OUT/'masking_log.jsonl') if r['case_id']==example['case_id'])
display(Markdown('### Example: Cross — removed passages' + chr(10) +
    chr(10).join('- ' + e['removed_text'] for e in log['edits'])))
display(Markdown('### Retained reasoning' + chr(10) + example['texts']['MASKED']))'''),
md('''## 5. Feedback 2 — a matched-word-budget random-removal control

Masking removes text as well as outcome language. For logistic regression, we therefore also remove the same number of words from each FULL opinion using five fixed seeds: 11, 23, 37, 51 and 71. Sentence order is shuffled uniformly; a random contiguous portion of the last selected sentence matches the budget exactly. Retained tokens keep their original order.

All sentences, including outcome sentences, are eligible. We save any outcome words accidentally removed. This controls the amount of text, not semantic information or BERT-token count. We report every seed and their mean/standard deviation instead of choosing the best seed.'''),
code('''for row in data:
    for seed in p.CONTROL_SEEDS:
        assert row['word_counts'][f'RANDOM_{seed}'] == row['word_counts']['MASKED']
display(pd.DataFrame([{'case_id':r['case_id'], 'FULL':r['word_counts']['FULL'],
                      'MASKED':r['word_counts']['MASKED'],
                      'RANDOM_11':r['word_counts']['RANDOM_11'],
                      'removed_percent':100*r['removed_fraction']} for r in train[:5]]))
display(summary['removed_percent'])'''),
md('''## 6. Baselines and first lexical experiments

Our sanity baseline always predicts the most common **training** label. The substantive baselines are TF-IDF + logistic regression and TF-IDF + linear SVM. TF-IDF uses word unigrams/bigrams, `min_df=2`, up to 30,000 features and L2 vector normalization. Each condition fits vocabulary and IDF on training text only.

Both classifiers use balanced class weights and C in {0.1, 1, 10}. The proposal chooses C by validation balanced accuracy, with macro F1 and then smaller C breaking ties. We also preselect **C=1** for the controlled FULL/MASKED/random comparison so a change in C does not confound the text intervention. No test score enters any choice.'''),
code('''# This cell fits the majority baseline and all lexical conditions.
# It refits on repeat execution and verifies equality with saved predictions.
lexical = p.run_lexical()
metric_columns = ['model','variant','C','accuracy','balanced_accuracy','macro_f1','confusion_matrix']
display(pd.DataFrame([r for r in lexical['grid'] if r['C'] in [None,1.]])[metric_columns])'''),
md('''## 7. Frozen LEGAL-BERT: use every chunk

We use `nlpaueb/legal-bert-base-uncased` at the pinned revision, with its slow uncased tokenizer (`use_fast=False`). Tokenize without truncation or initial special tokens; split into non-overlapping windows of 510 content tokens; add CLS/SEP to each window; right-pad each inference batch of four chunks.

The encoder is frozen and in evaluation/inference mode. Average final-layer hidden states over **content tokens only**, excluding special/padding tokens. Average chunk vectors weighted by content-token counts, producing one 768-dimensional vector per case. For 510 + 510 + 80 tokens, the weights are 510/1100, 510/1100 and 80/1100. All tokens contribute, but attention does not cross chunk boundaries.

StandardScaler and the downstream balanced logistic regression fit on training vectors only. The classifier tries the same C grid. Cached embeddings are representation features, not labels or generated answers.'''),
code('''# Extract frozen features (or verify/reuse the matching cache), then fit LR.
encoder = p.run_encoder()
display(pd.DataFrame(encoder['grid'])[metric_columns])
print('Frozen encoder revision:', encoder['encoder_lock']['revision'])'''),
md('''## 8. Word lengths, token lengths and chunk accounting

Words and subword tokens are different units. We report min, median, mean, P90 and max, the fraction exceeding 510 content tokens (one 512-token model input with special tokens), and total chunks. These are development-only statistics.'''),
code('''word_rows = [dict(split=split, variant=variant, **stats)
             for split,variants in summary['word_lengths'].items()
             for variant,stats in variants.items()]
display(pd.DataFrame(word_rows))
token_rows = [dict(split=split, variant=variant, **stats)
              for variant,splits in p.read(p.OUT/'token_length_statistics.json').items()
              for split,stats in splits.items()]
display(pd.DataFrame(token_rows))'''),
md('''## 9. Required metrics on identical validation cases

Accuracy measures total correctness; balanced accuracy averages recall across classes; macro F1 averages the two class F1 scores. We report raw and row-normalized confusion matrices, with **true labels as rows**, predicted labels as columns, and order [0,1]. Per-class recall explains which class fails.

Validation has eight cases per class, so accuracy and balanced accuracy happen to coincide. One error changes accuracy by 6.25 percentage points. The following fixed-C table is the main controlled experiment. These are preliminary validation findings, not final test performance.'''),
code('''results = p.summarize_results()
main = [r for r in results['fixed'] if not r['variant'].startswith('RANDOM_')]
display(pd.DataFrame(main)[metric_columns + ['class_counts','recall_by_class']])
display(pd.DataFrame(main)[['model','variant','confusion_matrix_row_normalized']])
display(pd.DataFrame([r for r in results['fixed'] if r['variant'].startswith('RANDOM_')])[metric_columns])
display(pd.DataFrame(results['random_control']).T)'''),
md('''## 10. Proposal hyperparameter selection — secondary table

This table selects C using the same validation set on which its scores are reported. It is useful for choosing a configuration, but is not an independent estimate of generalization. Interpret it separately from the fixed-C text ablation.'''),
code('''display(pd.DataFrame(results['selected_on_validation'])[metric_columns])'''),
md('''## 11. Descriptive uncertainty, with paired case-family resampling

We implement the proposal's paired family-bootstrap mechanism on validation as an MVP diagnostic: 5,000 family resamples, the same resample for FULL and MASKED, 95% percentile intervals. Replicates missing either class are skipped and counted. These development intervals are descriptive: they do not correct for repeated validation use, review uncertainty or dataset selection. The locked final-test intervals remain future work.'''),
code('''bootstrap = p.paired_bootstrap()
display({k:bootstrap[k] for k in ['scope','attempted','valid','skipped_single_class','seed']})
interval_rows = [dict(model=model, condition=condition, metric=metric, low=bounds[0], high=bounds[1])
                for model,conditions in bootstrap['intervals'].items()
                for condition,metrics in conditions.items() for metric,bounds in metrics.items()]
display(pd.DataFrame(interval_rows))'''),
md('''## 12. Errors, class imbalance, length and training features

We inspect all 16 validation cases rather than claiming a 20-case gallery from a 16-case set. Fixed length bins use FULL word counts (<400, 400–799, >=800); bin sizes and class counts accompany scores. Original independent annotation-agreement statistics describe the earlier drafts, not a new human-gold study.

Feature coefficients show training associations, not causal explanations. Qualitative interpretations are hypotheses about failures; we do not change labels or masks after looking at predictions.'''),
code('''overview, subgroups = p.diagnostics()
display(pd.DataFrame(overview))
display(pd.DataFrame(subgroups))
display(p.read(p.OUT/'annotation_agreement.json'))
display(p.read(p.OUT/'random_control_overlap.json'))
display(pd.DataFrame(lexical['coefficients']['MASKED']['toward_0']))
display(pd.DataFrame(lexical['coefficients']['MASKED']['toward_1']))'''),
md('''## 13. Figures and interpretation

The report uses the same saved numbers as this notebook. FULL/MASKED changes within this run are controlled comparisons; differences from the older provisional trial are not, because case selection and preprocessing both changed.'''),
code('''import presentation
presentation.make_figures()
display(Image(filename=str(p.OUT/'figures/confusion_matrices.png')))
display(Image(filename=str(p.OUT/'figures/ablation.png')))
observations = p.HERE/'ERROR_OBSERVATIONS.md'
if observations.exists(): display(Markdown(observations.read_text(encoding='utf8')))'''),
md('''## 14. Verify the end-to-end system

Recompute every saved metric from case-level predictions; verify shared IDs, exact random-removal budgets, train-only vocabulary, valid encoder feature shapes and absence of test predictions. These checks establish pipeline consistency; they do not prove complete legal eligibility or exhaustive removal of outcome cues.'''),
code('''display(p.validate_results())'''),
md('''## 15. Checkpoint status and next steps

- **Working MVP:** deterministic data integration, versioned text variants, three learned models and a majority baseline, predictions, metrics, figures and report.
- **Data/evaluation pipeline:** 120 team-reviewed selected candidates; 119 assigned, with one unresolved family hold. Train 86, validation 16, test 17 reserved. Stable case/family IDs and training-only fitting.
- **Baselines:** majority, TF-IDF LR, TF-IDF SVM; frozen LEGAL-BERT is the representation comparison.
- **First experiments:** FULL/MASKED comparisons, fixed-C ablation, five-seed LR random removal, small C-grid search, lengths and error review.
- **Preliminary results:** shown above with required metrics and uncertainty; the sample is too small for strong ranking or prospective-prediction claims.

The reviewed pool is below the proposal's 150-case MVP target; the pipeline is operational and this ungraded checkpoint demonstrates experimental evidence. Next, resolve outstanding cases/companions, expand reviewed coverage, document the evaluation-review protocol, and freeze the final pipeline before a single final-test evaluation. More complex models are secondary to these checks.

References: [Medvedeva & McBride (2023)](https://aclanthology.org/2023.nllp-1.9/), [Chalkidis et al. (2020)](https://aclanthology.org/2020.findings-emnlp.261/), [Pangakis & Wolken (2024)](https://arxiv.org/abs/2406.17633).''')]
nb=n.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python (Team 11 MVP)','language':'python','name':'team11-mvp'}})
n.write(nb,HERE/'Team_11_MVP.ipynb');print(f'Created {len(cells)} cells ({sum(c.cell_type=="code" for c in cells)} code).')
