"""Build a portable results report, error-review packet and executed-notebook source."""
import argparse,collections,math,re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import nbformat as nbf
from common import HERE,read,records,dump,jsonl,output,sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--run-name');a=p.parse_args();c=read(HERE/'config.json')
    if a.run_name:c['run_name']=a.run_name
    out=output(c);m=read(out/'metrics.json');stats=read(out/'dataset_summary.json');rows=records(out/'dataset_development.jsonl');preds=records(out/'validation_predictions.jsonl');logs=records(out/'masking_log.jsonl')
    assert all(r['period']!='test' for r in rows)
    primary=[r for r in m['controlled'] if not r['variant'].startswith('RANDOM_')]
    def table(results):
        lines=['| Model | Text | C | Accuracy | Balanced accuracy | Macro F1 | Confusion matrix |','|---|---|---:|---:|---:|---:|---|']
        for r in results:lines.append(f"| {r['model']} | {r['variant']} | {r['C']} | {r['accuracy']:.3f} | {r['balanced_accuracy']:.3f} | {r['macro_f1']:.3f} | {r['confusion_matrix']} |")
        return '\n'.join(lines)
    counts=stats['split_class_counts'];nval=sum(counts['validation'].values());candidate_count=stats['candidate_cases']
    split_table=['| Period | Use | Affirmed (0) | Reversed/vacated (1) | Total |','|---|---|---:|---:|---:|']
    for period,use,key in [('2010–2020','Training','train'),('2021–2022','Validation','validation'),('2023–2024','Sealed test','test')]:
        z=counts[key];split_table.append(f"| {period} | {use} | {z.get('0',0)} | {z.get('1',0)} | {sum(z.values())} |")
    original=c['run_name']=='yinkui_A_provisional_v1'
    report=['# PROVISIONAL — Partition A trial results',
        '> **NOT FINAL PROJECT RESULTS.** Development run only; label and dataset review are not certified by this report. For the original Yinkui trial, Hayden’s adjudication and Becca’s final preparation are pending. Do not interpret these scores as final test performance or a reliable model ranking.',
        f"Run: {c['run_name']}. Input annotations: {read(out/'run_config.json')['annotations']}. " + ('Uses only Yinkui’s frozen independent LLM-draft annotations, not adjudicated human ground truth. ' if original else 'Review status must be established from the new annotation provenance before claiming human ground truth. ') + 'All scores below are DEVELOPMENT validation scores. No test text is passed to preprocessing/feature extraction/model evaluation; only test metadata/counts and unsupervised family screening are used.',
        '## Dataset and split',
        f"{candidate_count} candidate decisions: {stats['reviewer_eligibility'].get('include',0)} marked include, {stats['reviewer_eligibility'].get('review',0)} pending review, {stats['reviewer_eligibility'].get('exclude',0)} excluded. Modeling status counts: {stats['modeling_status']}. The family screen does not certify complete family resolution.",
        '\n'.join(split_table),
        f"One validation error changes accuracy by {100/nval:.2f} percentage points. Accuracy and balanced accuracy coincide only if the validation classes are balanced. This set is also used for C selection, so tuned scores are not independent performance estimates. Check the reviewed case count against the proposal’s 150-reviewed-case MVP target and 300-eligible-case threshold for stronger final conclusions.",
        '## Main controlled experiment',
        'Fix C=1 in advance for all learned conditions to isolate text changes. Class weights, vocabulary/IDF and BERT feature scaling are fitted using training data only. Confusion matrices use true rows and predicted columns in order [0, 1]. Full per-class recall and row-normalized matrices are in metrics.json and the notebook.',table(primary),
        '## Matched-length random-removal control (main LR experiment)',
        'Five fixed seeds, uniform sentence removal order, with a random contiguous portion of the final sentence when needed to exactly match each opinion’s masked word-loss budget. Outcome sentences remain eligible for random removal. This is a word-budget control, not a matched BERT-token or matched semantic-content control. No seed is selected as the winner.',table([r for r in m['controlled'] if r['variant'].startswith('RANDOM_')])]
    for metric,r in m['random_control_fixed_C'].items():report.append(f"- {metric}: {r['mean']:.3f} ± {r['sd_across_seeds']:.3f} (sample standard deviation across five seeds, not a confidence interval).")
    lookup={(r['model'],r['variant']):r for r in primary};full=lookup[('TFIDF_LR','FULL')];masked=lookup[('TFIDF_LR','MASKED')];randommean=m['random_control_fixed_C']['balanced_accuracy']['mean']
    report += [f"At fixed C, LR balanced accuracy changes from {full['balanced_accuracy']:.3f} (FULL) to {masked['balanced_accuracy']:.3f} (MASKED); the random-removal mean is {randommean:.3f}. The differences describe this tiny provisional validation sample. They do not identify a causal effect of outcome language: masking also removes some useful reasoning, and random removal can itself remove outcome cues.",
        '## Proposal-specified hyperparameter search (secondary)',
        'C ∈ {0.1, 1, 10}; maximize validation balanced accuracy, then macro F1, then smaller C. These are scores on the same validation set used for selection, not final test scores. Compare the fixed-C results above when isolating the masking effect.',table(m['selected_on_validation']),
        '## Masking audit and professor feedback',
        'See the run-specific MASKING_AUDIT_REVIEW.md and MASKING_AUDIT_PACKET.md. The sampling design includes both classes in training and validation. Review outcome removal, retained reasoning and historical decisions before fitting; record the actual reviewer and findings. An assistant check is not human approval.',
        'For the original yinkui_A_provisional_v1 run, all eight sampled whole-appeal dispositions were removed, but two validation opinions showed collateral deletion and a training outlier lost 57% of its words. One sampled opinion retained ancillary procedural results. Those validation findings were recorded without changing rules. New runs require a fresh audit rather than inheriting these observations. The audit and five-seed random-removal control implement both feedback requests.',
        '## Text lengths',
        '| Split | Text | Minimum words | Median | Mean | P90 | Maximum |\n|---|---|---:|---:|---:|---:|---:|']
    for split,variants in stats['word_lengths'].items():
        for variant,r in variants.items():report.append(f"| {split} | {variant} | {r['min']:.0f} | {r['median']:.1f} | {r['mean']:.1f} | {r['p90']:.1f} | {r['max']:.0f} |")
    removed=stats['removed_fraction'];report.append(f"Masking removes a mean {removed['mean']:.1f}% of words per opinion (median {removed['median']:.1f}%, maximum {removed['max']:.1f}%). The historical dataset_summary.json key `removed_fraction` contains percentage statistics; individual dataset rows contain true fractions.")
    if (out/'token_length_statistics.json').exists():
        tokens=read(out/'token_length_statistics.json');report += ['\n| Split | Text | Min tokens | Median | Mean | P90 | Max | >510 content tokens | Total chunks |','|---|---|---:|---:|---:|---:|---:|---:|---:|']
        for variant,by_split in tokens.items():
            for split,r in by_split.items():report.append(f"| {split} | {variant} | {r['min']:.0f} | {r['median']:.1f} | {r['mean']:.1f} | {r['p90']:.1f} | {r['max']:.0f} | {r['fraction_over_510']:.1%} | {r['total_chunks']} |")
    report += ['LEGAL-BERT uses every non-overlapping chunk of up to 510 content tokens plus CLS/SEP. Padding and special tokens are excluded from mean pooling. Chunk vectors are averaged with content-token-count weights; no first-512 truncation and no fine-tuning.',
        '## Error analysis and next review',
        f'ERROR_REVIEW_PACKET.md includes all {nval} validation opinions, their original source links, FULL/MASKED LR and cross-model predictions, removed passages, and masked text. This is a review queue, not a claim that every error has been legally adjudicated. The original run also has ERROR_OBSERVATIONS.md with four assistant-reviewed examples. Automatic length-group summaries are in subgroup_metrics.json; each bin’s class counts must accompany its scores.',
        'tfidf_features.json lists training-derived positive/negative coefficients at C=1. Coefficients are diagnostic associations, not explanations of legal causation. Because validation is small, no claim that LEGAL-BERT is superior is justified by one run.',
        'Hayden: confirm eligibility and labels independently of these predictions, especially procedural-plus-merits and ambiguous property cases; preserve disagreements. Becca: finalize case families, source cleanup and masks, inspect collateral removal and residual cues, and freeze the reviewed dataset. Yinkui: rerun all conditions under a new run name on that dataset. Keep the test period sealed until the final pipeline and evaluation labels are fixed.',
        'For the final study, compute paired 95% bootstrap intervals using case families for test metrics and FULL-minus-MASKED differences. This prototype deliberately provides no test intervals or test metrics. Expand beyond A if stronger comparative conclusions are needed.']
    report_text=re.sub(r'(?m)(^\|[^\n]*\|)\n\n(?=\|)',r'\1\n','\n\n'.join(report))
    (out/'REPORT.md').write_text(report_text+'\n',encoding='utf8')
    # Review queue: all validation cases prevents selecting only favorable examples.
    logmap={r['case_id']:r for r in logs};packet=['# Validation error-review packet','Provisional draft labels. Read original sources before resolving eligibility/outcome. No automatic correction or human approval is implied. No test cases.'];subgroups=[]
    for r in rows:
        if r['period']!='validation':continue
        pp=[p for p in preds if p['case_id']==r['case_id'] and p['C']==1 and p['variant'] in ['FULL','MASKED']]
        packet += [f"## {r['case_id']} — {r['case_name']}",f"[Original opinion]({r['source_url']}); provisional label {r['label']}; FULL {r['word_counts']['FULL']} words; MASKED {r['word_counts']['MASKED']} words.", '\n'.join(f"- {p['model']} {p['variant']}: {p['predicted_label']} ({'matches draft' if p['predicted_label']==r['label'] else 'differs from draft'})" for p in pp),'### Removed', '\n'.join(x['text'] for x in logmap[r['case_id']]['removed']),'### MASKED',r['texts']['MASKED'],'Review: eligibility / label / residual cues / lost reasoning / procedural history / other — human review pending.']
    (out/'ERROR_REVIEW_PACKET.md').write_text('\n\n'.join(packet),encoding='utf8')
    from train import metrics
    rmap={r['case_id']:r for r in rows}
    for result in primary:
        for label,lo,hi in [('short',0,400),('medium',400,800),('long',800,float('inf'))]:
            pp=[p for p in preds if (p['model'],p['variant'],p['C'])==(result['model'],result['variant'],result['C']) and lo<=rmap[p['case_id']]['word_counts']['FULL']<hi]
            # Single-class subgroups get confusion/counts, but no misleading BA ranking.
            if not pp:continue
            y=[p['true_label'] for p in pp];pr=[p['predicted_label'] for p in pp]
            d={'model':result['model'],'variant':result['variant'],'length_group':label,'bounds_full_words':[lo,None if math.isinf(hi) else hi],'n':len(pp),'class_counts':dict(collections.Counter(y))}
            if len(set(y))==2:d.update(metrics(y,pr))
            else:d['note']='Single true class; no two-class score comparison.'
            subgroups.append(d)
    dump(out/'subgroup_metrics.json',subgroups)
    plotdir=out/'plots';plotdir.mkdir(exist_ok=True)
    fig,axes=plt.subplots(2,3,figsize=(11,7))
    for ax,r in zip(axes.flat,[r for r in primary if r['model']!='Majority']):
        mat=np.array(r['confusion_matrix']);scale=max(counts['validation'].values());ax.imshow(mat,vmin=0,vmax=scale,cmap='Blues')
        for i in range(2):
            for j in range(2):ax.text(j,i,f'{mat[i,j]}\n({r["confusion_matrix_row_normalized"][i][j]:.0%})',ha='center',va='center',color='white' if mat[i,j]>scale/2 else 'black')
        ax.set(title=f"{r['model']} · {r['variant']}",xlabel='Predicted',ylabel='True',xticks=[0,1],yticks=[0,1])
    fig.suptitle(f"PROVISIONAL · Validation only · C=1 · class counts {counts['validation']}");fig.tight_layout();fig.savefig(plotdir/'confusion_matrices.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4));names=[r['model']+'\n'+r['variant'] for r in primary];ax.bar(names,[r['balanced_accuracy'] for r in primary]);ax.axhline(.5,color='black',ls='--');ax.set(ylim=(0,1),ylabel='Balanced accuracy',title=f'PROVISIONAL · Validation scores at fixed C=1 (n={nval})');fig.tight_layout();fig.savefig(plotdir/'balanced_accuracy.png',dpi=160);plt.close(fig)
    # Notebook reads and checks actual saved experimental artifacts; expensive training is a separate reproducible command.
    cells=[nbf.v4.new_markdown_cell('# PROVISIONAL — Partition A trial results\n\n> **NOT FINAL PROJECT RESULTS.** Yinkui draft annotations only, before Hayden’s adjudication and Becca’s finalized preparation. All scores are development validation results; no final test evaluation.\n\nThis notebook displays the completed run and verifies saved metrics. Training commands are in README.md. The team will rerun on the reviewed dataset.'),
        nbf.v4.new_code_cell("from pathlib import Path\nimport json, hashlib\nimport pandas as pd\nfrom IPython.display import display, Markdown, Image\nRUN = Path('.')\nread = lambda name: json.loads((RUN/name).read_text(encoding='utf8'))\nprovenance = read('data_provenance.json')\nassert hashlib.sha256((RUN/'dataset_development.jsonl').read_bytes()).hexdigest() == provenance['data_sha256']\nrows = [json.loads(s) for s in (RUN/'dataset_development.jsonl').read_text(encoding='utf8').splitlines()]\nassert {r['period'] for r in rows} == {'train', 'validation'}\ndisplay(pd.DataFrame(read('dataset_summary.json')['split_class_counts']).T.rename(columns={'0':'affirmed','1':'reversed/vacated'}))"),
        nbf.v4.new_markdown_cell('## Feedback 1: masking audit before modeling\nTwo cases per class in each development split. Human review remains pending; collateral deletion is a documented limitation.'),
        nbf.v4.new_code_cell("display(Markdown((RUN/'MASKING_AUDIT_REVIEW.md').read_text(encoding='utf8')))"),
        nbf.v4.new_markdown_cell('## Fixed-C experiments and the random-removal control\nFixed C=1 isolates the text intervention. Seed variability is not a confidence interval.'),
        nbf.v4.new_code_cell("results=read('metrics.json')\ncolumns=['model','variant','C','accuracy','balanced_accuracy','macro_f1','confusion_matrix','class_counts']\ndisplay(pd.DataFrame(results['controlled'])[columns])\ndisplay(pd.DataFrame(results['random_control_fixed_C']).T)\ndisplay(Image(filename=str(RUN/'plots/confusion_matrices.png')))"),
        nbf.v4.new_markdown_cell('## Proposal C-grid selection\nValidation was also used to choose C; these are development scores, not independent test estimates.'),
        nbf.v4.new_code_cell("display(pd.DataFrame(results['selected_on_validation'])[columns])"),
        nbf.v4.new_markdown_cell('## Lengths and frozen encoder\nEvery chunk contributes. Word lengths and token lengths are different measurements.'),
        nbf.v4.new_code_cell("lengths=[]\nfor split, variants in read('dataset_summary.json')['word_lengths'].items():\n    for variant, stats in variants.items(): lengths.append(dict(split=split,variant=variant,**stats))\ndisplay(pd.DataFrame(lengths))\ntokens=[]\nfor variant, splits in read('token_length_statistics.json').items():\n    for split, stats in splits.items(): tokens.append(dict(split=split,variant=variant,**stats))\ndisplay(pd.DataFrame(tokens))"),
        nbf.v4.new_markdown_cell('## Independently recompute all saved validation metrics'),
        nbf.v4.new_code_cell("from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, confusion_matrix\npredictions=[json.loads(s) for s in (RUN/'validation_predictions.jsonl').read_text(encoding='utf8').splitlines()]\nexpected={r['case_id'] for r in rows if r['period']=='validation'}\nfor result in results['grid']:\n    p=[p for p in predictions if (p['model'],p['variant'],p['C'])==(result['model'],result['variant'],result['C'])]\n    assert {x['case_id'] for x in p}==expected\n    y=[x['true_label'] for x in p]; yp=[x['predicted_label'] for x in p]\n    assert accuracy_score(y,yp)==result['accuracy']\n    assert balanced_accuracy_score(y,yp)==result['balanced_accuracy']\n    assert f1_score(y,yp,average='macro',labels=[0,1],zero_division=0)==result['macro_f1']\n    assert confusion_matrix(y,yp,labels=[0,1]).tolist()==result['confusion_matrix']\nprint(f\"Verified {len(results['grid'])} model/C conditions on the same {len(expected)} validation cases; no test predictions.\")"),
        nbf.v4.new_markdown_cell('## Findings and next iteration'),
        nbf.v4.new_code_cell("display(Markdown((RUN/'REPORT.md').read_text(encoding='utf8')))"),
        nbf.v4.new_markdown_cell('## Before the reviewed rerun\nHayden resolves eligibility/outcomes independently of model predictions; Becca freezes the reviewed dataset, families and masks; Yinkui reruns this grid under a new version. Do not interpret this run as human-ground-truth evaluation. No final-test analysis was performed. Paired family bootstrap intervals belong to the eventual final evaluation.')]
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python (provisional A)','language':'python','name':'provisional-a'}});nbf.write(nb,out/'provisional_A_results.ipynb')
    print(out/'REPORT.md')
if __name__=='__main__':main()
