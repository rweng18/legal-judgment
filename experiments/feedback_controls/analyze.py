"""Recompute metrics, paired family uncertainty, and audit/prediction links."""
from collections import defaultdict,Counter
from common import *
import numpy as np
from modeling import scores

def main():
    out=HERE/'results';metrics=sum([read(out/s/'metrics.json') for s in ['lexical','bert']],[])
    pp=sum([records(out/s/'predictions.jsonl') for s in ['lexical','bert']],[])
    rows=load_rows();dev=[r for r in rows if r['period']=='validation'];ids=[r['case_id'] for r in dev];y=np.array([r['label'] for r in dev])
    preds={};byrun=defaultdict(list)
    for p in pp:byrun[p['run_id']].append(p)
    for m in metrics:
        p=byrun[m['run_id']];assert [x['case_id'] for x in p]==ids
        assert [x['label'] for x in p]==y.tolist()
        preds[m['run_id']]=np.array([x['prediction'] for x in p])
        s=scores(y,preds[m['run_id']]);assert all(m[k]==v for k,v in s.items())
    def get(exp,model,variant,c=None):
        found=[r for r in metrics if r['experiment']==exp and r['model']==model and r['variant']==variant and (c is None or r['C']==c)]
        assert len(found)==1,(exp,model,variant,c);return found[0]
    def p(m):return preds[m['run_id']]
    # Sample whole validation families with replacement, using the SAME draws
    # for every model, seed and text condition. Repeated validation use remains.
    families=sorted({r['family_id'] for r in dev});rng=np.random.default_rng(20261119)
    fm=np.array([families.index(r['family_id']) for r in dev])
    weights=rng.multinomial(len(families),np.ones(len(families))/len(families),5000)[:,fm]
    valid=(weights[:,y==0].sum(1)>0)&(weights[:,y==1].sum(1)>0);weights=weights[valid]
    def boot(yp):
        a,b,c,d=[weights@((y==i)&(yp==j)).astype(float) for i,j in [(0,0),(0,1),(1,0),(1,1)]]
        return np.stack([(a+d)/(a+b+c+d),.5*(a/(a+b)+d/(c+d)),.5*(2*a/(2*a+b+c)+2*d/(2*d+b+c))],axis=1)
    bcache={m['run_id']:boot(p(m)) for m in metrics};names=['accuracy','balanced_accuracy','macro_f1'];intervals=[]
    def compare(name,left,right):
        # Lists average independently trained seed-wise metrics, not predictions.
        ll=np.mean([bcache[m['run_id']] for m in left],axis=0);rr=np.mean([bcache[m['run_id']] for m in right],axis=0)
        for j,k in enumerate(names):
            point=np.mean([m[k] for m in left])-np.mean([m[k] for m in right]);lo,hi=np.quantile((ll-rr)[:,j],[.025,.975])
            intervals.append({'comparison':name,'metric':k,'difference':float(point),'lower':float(lo),'upper':float(hi),'resamples':len(weights),'unit':'validation_family','interpretation':'descriptive; repeatedly used validation, not final-test inference'})
    summaries=[];shifts=[]
    for model in SELECTED_C:
        full=get('primary',model,'FULL');mask=get('primary',model,'MASKED');compare(model+' FULL - MASKED',[full],[mask])
        compare(model+' revised - original mask',[get('mask_only',model,'REVISED')],[mask])
        compare(model+' dedup mask - original mask',[get('dedup_only',model,'MASKED')],[mask])
        variants=[mask]+([get('primary',model,f'RANDOM_{s}') for s in SEEDS] if model!='TFIDF_SVM' else [])
        for m in variants:
            a=p(full);b=p(m);shifts.append({'model':model,'variant':m['variant'],'changed':int(sum(a!=b)),
                'correct_to_wrong':int(sum((a==y)&(b!=y))),'wrong_to_correct':int(sum((a!=y)&(b==y))),
                'correct_both':int(sum((a==y)&(b==y))),'wrong_both':int(sum((a!=y)&(b!=y)))})
        if model!='TFIDF_SVM':
            for exp,prefix,masked in [('primary','RANDOM','MASKED'),('same_fitted_FULL','RANDOM','MASKED'),('mask_only','REVISED_RANDOM','REVISED'),('dedup_and_mask','REVISED_RANDOM','REVISED')]:
                controls=[get(exp,model,f'{prefix}_{s}') for s in SEEDS];target=get(exp,model,masked)
                compare(model+' '+exp+' mean random - mask',controls,[target])
                summaries.append({'model':model,'experiment':exp,'seeds':SEEDS,
                    **{k+'_mean':float(np.mean([m[k] for m in controls])) for k in names},
                    **{k+'_sample_sd':float(np.std([m[k] for m in controls],ddof=1)) for k in names}})
    for c in [.1,1.]:
        for v in ['FULL','MASKED']:compare(f'BERT all - first {v} C={c}',[get('chunk_ablation','LEGAL_BERT_LR',v,c)],[get('chunk_ablation','LEGAL_BERT_LR',v+'_FIRST',c)])

    # Link the prior, fixed eight-case audit to every seed. Validate all quotes
    # and offsets before measuring how many of their words each random draw cut.
    audited=read(REFERENCE/'error_analysis_v1/cases.json')['cases']
    source={r['case_id']:r for r in rows};logs={r['case_id']:r for r in records(HERE/'inputs/removal_logs.jsonl')}
    primarytext={r['case_id']:r['texts'] for r in records(HERE/'inputs/variants.jsonl')}
    qualitative={
      'NY-4929051':'Long procedural history; removed opening orders also describe prior rulings; retained merits and ancillary motion disposition.',
      'NY-5304378':'Retained law-office-failure and merits reasoning; explicit evaluative wording remains. Generic court-should-have language is missed by the revised B/C rule.',
      'NY-8511862':'Denial of defense summary judgment is affirmed; retained reasoning concerns failure of defendant proof, not a plaintiff victory on liability.',
      'NY-6459053':'Historical denial and notice reasoning retained; original MASKED has a truncated trailing citation.',
      'NY-5957906':'Procedural permission to file late differs from merits reversal. The deleted merits sentence mixes a result clause with failure-of-proof reasoning.',
      'NY-9301972':'FULL equals MASKED and still says unanimously affirmed. Any separately refitted classifier prediction change is not caused by deleting this opinion text.',
      'NY-4894160':'Contractor duty and creation-of-hazard reasoning remains; original MASKED truncates a trailing citation.',
      'NY-6476214':'Long correct example; evaluative statement that the motion should have been denied remains. All chunks were processed.'}
    auditout=[];overlap=[]
    for a in audited:
        cid=a['case_id'];r=source[cid];i=ids.index(cid);text=r['texts']['FULL'];words=list(re.finditer(r'\S+',text));evidence=[]
        for j,e in enumerate(a['evidence']):
            for loc in e['locations']:assert r['texts'][loc['variant']][loc['start']:loc['end']]==e['quote']
            loc=next(x for x in e['locations'] if x['variant']=='FULL')
            tokenids={n for n,w in enumerate(words) if w.end()>loc['start'] and w.start()<loc['end']}
            fractions={}
            for s in SEEDS:
                cut=set(logs[cid]['variants'][f'RANDOM_{s}']['removed_word_indices']);fractions[str(s)]=len(cut&tokenids)/len(tokenids)
            evidence.append({**e,'fraction_of_quote_words_removed_by_seed':fractions})
        for model in ['TFIDF_LR','LEGAL_BERT_LR']:
            for exp in ['primary','same_fitted_FULL']:
                selected=[get(exp,model,v) for v in ['FULL','MASKED',*[f'RANDOM_{s}' for s in SEEDS]]]
                auditout.append({'case_id':cid,'label':r['label'],'model':model,'experiment':exp,
                    'predictions':{m['variant']:int(p(m)[i]) for m in selected},'evidence':evidence,'interpretation':qualitative[cid],
                    'audit_source':'Previously committed eight-case passage audit; exact quotes/offsets reverified; semantic notes are qualitative, not causal attribution.'})
        masks=a['masking_removals'];masked_words=set();cursor=0
        for rem in masks:
            removed=rem.get('removed_text',rem.get('text',rem.get('sentence')))
            lo=rem['start'] if 'start' in rem else text.index(removed,cursor)
            hi=rem.get('end',lo+len(removed));cursor=hi
            assert text[lo:hi]==removed
            masked_words.update(n for n,w in enumerate(words) if w.end()>lo and w.start()<hi)
        for seed in SEEDS:
            cut=set(logs[cid]['variants'][f'RANDOM_{seed}']['removed_word_indices'])
            overlap.append({'case_id':cid,'seed':seed,'random_words':len(cut),'mask_span_words':len(masked_words),'overlap_words':len(cut&masked_words),
                'fraction_mask_span_words_randomly_removed':len(cut&masked_words)/len(masked_words) if masked_words else None})

    # Reproduction check is prediction-level across operating systems; also report
    # vector differences rather than claiming bit-identical floating point.
    ref=list(csv.DictReader((REFERENCE/'predictions.csv').open(encoding='utf8')));reproduction=[]
    for model in ['Majority',*SELECTED_C]:
        for v in ['FULL','MASKED']:
            m=get('primary',model,v);rp={r['case_id']:int(r['prediction']) for r in ref if r['model']==model and r['variant']==v}
            assert set(rp)==set(ids)
            reproduction.append({'model':model,'variant':v,'different_predictions':sum(int(rp[c]!=pred) for c,pred in zip(ids,p(m)))})
    embindex=read(out/'embeddings/index.json');refindex=read(REFERENCE/'embedding_index.json')
    assert embindex['case_ids']==[r['case_id'] for r in refindex['rows']]
    diffs={}
    for v in ['FULL','MASKED']:
        for r,idx in zip(rows,refindex['rows']):assert r['text_sha256'][v]==idx['text_sha256'][v]
        original=REFERENCE/f'embeddings_{v}.npy';assert digest(original.read_bytes())==refindex['files_sha256'][original.name]
        diff=np.abs(np.load(out/'embeddings'/f'{v}.npy')-np.load(original));diffs[v]={'max_absolute':float(diff.max()),'mean_absolute':float(diff.mean())}
    counts=[];tokenindex={(x['case_id'],x['variant']):x for x in embindex['texts']}
    for period in ['train','validation']:
        for v in ['FULL','MASKED','REVISED',*[f'RANDOM_{s}' for s in SEEDS]]:
            take=[tokenindex[(r['case_id'],v)] for r in rows if r['period']==period]
            counts.append({'period':period,'variant':v,'n':len(take),'tokens_median':float(np.median([x['tokens'] for x in take])),
                'tokens_max':max(x['tokens'] for x in take),'more_than_one_chunk':sum(x['chunks']>1 for x in take),'chunks_total':sum(x['chunks'] for x in take)})
    lengthgroups=[]
    for group,condition in [('one',lambda n:n==1),('two',lambda n:n==2),('three_plus',lambda n:n>=3)]:
        take=np.array([condition(tokenindex[(r['case_id'],'FULL')]['chunks']) for r in dev]);yy=y[take]
        for v in ['FULL','MASKED']:
            for suffix in ['','_FIRST']:
                m=get('chunk_ablation','LEGAL_BERT_LR',v+suffix,.1);yp=p(m)[take]
                lengthgroups.append({'full_chunks_group':group,'variant':v+suffix,'n':int(take.sum()),'class_0':int(sum(yy==0)),'class_1':int(sum(yy==1)),**scores(yy,yp)})
    components=[]
    for name in ['OLD','BOUNDARY_ONLY','RULE_ONLY','COMBINED','REVISED']:
        texts=({r['case_id']:r['texts']['REVISED'] for r in records(HERE/'inputs/quality_v1/variants.jsonl')} if name=='REVISED' else {c:t[name] for c,t in primarytext.items()})
        components.append({'variant':name,'cases_changed_from_OLD':sum(t!=primarytext[c]['OLD'] for c,t in texts.items()),
            'words_removed_total':sum(len(source[c]['texts']['FULL'].split())-len(t.split()) for c,t in texts.items()),
            'empty_cases':sum(not t.strip() for t in texts.values())})
    for name,data in [('metrics',metrics),('seed_summaries',summaries),('paired_intervals',intervals),('prediction_changes',shifts),('audit_prediction_links',auditout),('audit_random_overlap',overlap),('length_statistics',counts),('chunk_length_groups',lengthgroups),('component_retention',components)]:
        write(out/(name+'.json'),data)
        if name!='audit_prediction_links':csvout(out/(name+'.csv'),data)
    jsonl(out/'predictions.jsonl',pp)
    write(out/'verification.json',{'metrics_recomputed':len(metrics),'prediction_rows':len(pp),'validation_ids':ids,
       'validation_families':len(families),'bootstrap_draws':5000,'bootstrap_valid_draws':len(weights),
       'reference_prediction_reproduction':reproduction,'reference_embedding_difference':diffs,
       'quoted_evidence_verified':sum(len(x['evidence']) for x in audited),'no_test_predictions':True,
       'source_commit':BASE,'analysis_code_sha256':digest(Path(__file__).read_bytes()),
       'limitations':['Repeated validation use; no independent final test.','B/C user reports human review, exact case-level final handoff pending.','Mann-only dedup sensitivity; other family candidates remain.','Revised mask still has false negatives and mixed reasoning/result deletions.']})
    print('Analysis verified',len(metrics),'conditions;',len(pp),'predictions')

if __name__=='__main__':main()
