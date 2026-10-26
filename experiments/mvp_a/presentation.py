"""Generate publication figures and LaTeX tables directly from saved results."""
from pathlib import Path
import shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pipeline as p
REPORT=p.ROOT/'reports/Team_11_MVP_IEEE'
NAMES={'Majority':'Majority','TFIDF_LR':'TF-IDF LR','TFIDF_SVM':'TF-IDF SVM','LEGAL_BERT_LR':'LEGAL-BERT LR'}

def make_figures():
    results=p.read(p.OUT/'metrics.json');fixed=results['fixed'];lookup={(r['model'],r['variant']):r for r in fixed}
    dest=p.OUT/'figures';dest.mkdir(exist_ok=True);images=REPORT/'images';images.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':9,'axes.titlesize':10,'pdf.fonttype':42,'ps.fonttype':42})
    fig,axes=plt.subplots(2,3,figsize=(7.1,4.3),constrained_layout=True)
    for j,model in enumerate(['TFIDF_LR','TFIDF_SVM','LEGAL_BERT_LR']):
        for i,variant in enumerate(['FULL','MASKED']):
            ax=axes[i,j];r=lookup[(model,variant)];a=np.array(r['confusion_matrix'])
            ax.imshow(a,cmap='Blues',vmin=0,vmax=8)
            for x in range(2):
                for y in range(2):ax.text(y,x,f'{a[x,y]}\n{100*r["confusion_matrix_row_normalized"][x][y]:.1f}%',ha='center',va='center',fontsize=9,color='white' if a[x,y]>4 else 'black')
            ax.set(title=f'{NAMES[model]} · {variant}',xticks=[0,1],yticks=[0,1],xlabel='Predicted',ylabel='True')
    fig.suptitle('Preliminary validation results · team-reviewed labels · C=1 · n=16',fontsize=10)
    for ext in ['png','pdf']:fig.savefig(dest/f'confusion_matrices.{ext}',dpi=200)
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(5.8,3.2),constrained_layout=True)
    lr=[lookup[('TFIDF_LR',v)]['balanced_accuracy'] for v in ['FULL','MASKED']]
    control=results['random_control']['balanced_accuracy'];values=lr+[control['mean']]
    ax.bar(['FULL','MASKED','Random removal\nmean of 5 seeds'],values,color=['#2863a5','#dc8e32','#6a8f60'],width=.6)
    ax.errorbar(2,control['mean'],yerr=control['sd_across_seeds'],fmt='none',ecolor='black',capsize=5,label='±1 SD across seeds')
    ax.scatter(np.full(5,2)+np.linspace(-.12,.12,5),control['values'],s=20,c='black',zorder=4)
    for i,v in enumerate(values):ax.text(i,v+.075,f'{100*v:.2f}%',ha='center')
    ax.axhline(.5,ls='--',color='#555555',lw=1);ax.set(ylim=(0,1),ylabel='Balanced accuracy',title='TF-IDF LR at C=1: outcome masking versus text loss')
    ax.legend(loc='lower right',fontsize=8)
    for ext in ['png','pdf']:fig.savefig(dest/f'ablation.{ext}',dpi=200)
    plt.close(fig)
    for name in ['confusion_matrices.pdf','ablation.pdf']:shutil.copyfile(dest/name,images/name)
    return dest

def make_tables():
    results=p.read(p.OUT/'metrics.json');summary=p.read(p.OUT/'dataset_summary.json');tokens=p.read(p.OUT/'token_length_statistics.json');boot=p.read(p.OUT/'bootstrap_validation.json')
    lines=[r'\begin{table}[t]',r'\caption{Preliminary validation results at fixed $C=1$. All conditions use the same 16 cases (8 per class).}',r'\label{tab:results}',r'\centering\footnotesize',r'\begin{tabular}{llrrr}',r'\toprule Model & Text & Acc. & Bal. acc. & Macro F1 \\',r'\midrule']
    for r in results['fixed']:
        if r['variant'].startswith('RANDOM_'):continue
        lines.append(f"{NAMES[r['model']]} & {'--' if r['model']=='Majority' else r['variant']} & {r['accuracy']:.3f} & {r['balanced_accuracy']:.3f} & {r['macro_f1']:.3f}"+r' \\')
    lines += [r'\bottomrule\end{tabular}',r'\end{table}']
    (REPORT/'results_table.tex').write_text('\n'.join(lines),encoding='utf8',newline='\n')
    lines=[r'\begin{table}[t]',r'\caption{LR random-removal controls at $C=1$. SD describes seed variability, not a confidence interval.}',r'\label{tab:control}',r'\centering\footnotesize',r'\begin{tabular}{lrrr}',r'\toprule Seed & Acc. & Bal. acc. & Macro F1 \\',r'\midrule']
    for r in results['fixed']:
        if r['variant'].startswith('RANDOM_'):lines.append(f"{r['variant'].split('_')[1]} & {r['accuracy']:.3f} & {r['balanced_accuracy']:.3f} & {r['macro_f1']:.3f}"+r' \\')
    mean=[results['random_control'][k]['mean'] for k in ['accuracy','balanced_accuracy','macro_f1']];sd=[results['random_control'][k]['sd_across_seeds'] for k in ['accuracy','balanced_accuracy','macro_f1']]
    lines += [r'\midrule','Mean & '+' & '.join(f'{v:.3f}' for v in mean)+r' \\','SD & '+' & '.join(f'{v:.3f}' for v in sd)+r' \\',r'\bottomrule\end{tabular}',r'\end{table}']
    (REPORT/'control_table.tex').write_text('\n'.join(lines),encoding='utf8',newline='\n')
    lines=[r'\begin{table*}[t]',r'\caption{Development text lengths. Tokens exclude CLS/SEP and padding; one model input holds 510 content tokens.}',r'\label{tab:length}',r'\centering\scriptsize',r'\begin{tabular}{llrrrrrrrrrrrr}',r'\toprule & & \multicolumn{5}{c}{Words} & \multicolumn{5}{c}{Content tokens} & $>510$ & Total \\',r'\cmidrule(lr){3-7}\cmidrule(lr){8-12}',r'Split & Text & Min & Median & Mean & P90 & Max & Min & Median & Mean & P90 & Max & tokens & chunks \\',r'\midrule']
    for split in ['train','validation']:
        for variant in ['FULL','MASKED']:
            w=summary['word_lengths'][split][variant];t=tokens[variant][split]
            vals=[w[k] for k in ['min','median','mean','p90','max']]+[t[k] for k in ['min','median','mean','p90','max']]
            lines.append(f"{split.title()} & {variant} & "+' & '.join(f'{v:.1f}' for v in vals)+f" & {100*t['fraction_over_510']:.1f}\\% & {t['total_chunks']}"+r' \\')
    lines += [r'\bottomrule\end{tabular}',r'\end{table*}']
    (REPORT/'length_table.tex').write_text('\n'.join(lines),encoding='utf8',newline='\n')
    lines=[r'\begin{table}[t]',r'\caption{Descriptive validation bootstrap: 95\% intervals for balanced accuracy and paired FULL--MASKED difference at $C=1$.}',r'\label{tab:bootstrap}',r'\centering\footnotesize',r'\setlength{\tabcolsep}{3pt}',r'\begin{tabular}{lrrr}',r'\toprule Model & FULL & MASKED & Difference \\',r'\midrule']
    for model,conditions in boot['intervals'].items():
        cells=['['+f"{conditions[v]['balanced_accuracy'][0]:.2f}, {conditions[v]['balanced_accuracy'][1]:.2f}"+']' for v in ['FULL','MASKED','FULL_minus_MASKED']]
        lines.append(NAMES[model]+' & '+' & '.join(cells)+r' \\')
    lines += [r'\bottomrule\end{tabular}',r'\end{table}']
    (REPORT/'bootstrap_table.tex').write_text('\n'.join(lines),encoding='utf8',newline='\n')

if __name__=='__main__':make_figures();make_tables();print(REPORT)
