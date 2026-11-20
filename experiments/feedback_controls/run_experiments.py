"""Fixed-setting development comparisons. No test access or model selection."""
import argparse,time
from collections import Counter
from importlib.metadata import version
from common import *
import numpy as np
from modeling import estimator,scores

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['lexical','bert'],required=True);args=ap.parse_args()
    start=time.perf_counter();rows=load_rows();inputs=records(HERE/'inputs/variants.jsonl');quality=records(HERE/'inputs/quality_v1/variants.jsonl')
    for root in [HERE/'inputs',HERE/'inputs/quality_v1']:
        for file,h in read(root/'protocol.json')['sha256'].items():assert digest((root/file).read_bytes())==h
    assert [r['case_id'] for r in rows]==[r['case_id'] for r in inputs]==[r['case_id'] for r in quality]
    for r,q in zip(inputs,quality):r['texts'].update(q['texts'])
    train=np.array([r['period']=='train' for r in rows]);val=~train;y=np.array([r['label'] for r in rows]);dev=[r for r in rows if r['period']=='validation']
    assert {r['family_id'] for r in rows if r['period']=='train'}.isdisjoint(r['family_id'] for r in dev)
    dedup=train&np.array([r['case_id']!='NY-6112018' for r in rows])
    primary=['FULL','MASKED',*[f'RANDOM_{s}' for s in SEEDS]]
    results=[];predictions=[];fitcache={};featurecache={};subsets=[]
    models=['TFIDF_LR','TFIDF_SVM'] if args.stage=='lexical' else ['LEGAL_BERT_LR']
    if args.stage=='bert':
        ep=HERE/'results/embeddings';index=read(ep/'index.json')
        assert index['case_ids']==[r['case_id'] for r in rows]
        for file,h in index['sha256'].items():assert digest((ep/file).read_bytes())==h

    def features(model,variant):
        key=(model=='LEGAL_BERT_LR',variant)
        if key not in featurecache:
            featurecache[key]=(np.load(HERE/'results/embeddings'/f'{variant}.npy',allow_pickle=False) if key[0] else
                np.array([r['texts'][variant] for r in inputs],dtype=object))
        return featurecache[key]

    def run(model,variant,c,experiment,fitmask=train,fit_variant=None,seed=None,fraction=None):
        fv=fit_variant or variant;key=(model,fv,c,tuple(np.flatnonzero(fitmask)))
        if model=='Majority':
            yp=np.full(val.sum(),int(np.argmax(np.bincount(y[fitmask],minlength=2))));decision=[None]*len(yp)
        else:
            if key not in fitcache:fitcache[key]=estimator(model,c).fit(features(model,fv)[fitmask],y[fitmask])
            pipeline=fitcache[key];yp=pipeline.predict(features(model,variant)[val]);decision=pipeline.decision_function(features(model,variant)[val]).tolist()
        rid=f'{experiment}:{model}:{variant}:C={c}:seed={seed}:fraction={fraction}'
        result={'run_id':rid,'experiment':experiment,'model':model,'variant':variant,'fit_variant':fv,'C':c,'seed':seed,'fraction':fraction,
                'n_train':int(fitmask.sum()),'train_0':int(sum(y[fitmask]==0)),'train_1':int(sum(y[fitmask]==1)),
                'n_validation':int(val.sum()),'validation_0':int(sum(y[val]==0)),'validation_1':int(sum(y[val]==1)),**scores(y[val],yp)}
        results.append(result)
        for r,p,d in zip(dev,yp,decision):
            predictions.append({'run_id':rid,'case_id':r['case_id'],'batch':r['batch'],'family_id':r['family_id'],'label':r['label'],'prediction':int(p),'decision_score':d})
        print(rid,'balanced_accuracy',round(result['balanced_accuracy'],4),flush=True)
        return result

    if args.stage=='lexical':
        for v in ['FULL','MASKED']:run('Majority',v,None,'primary')
    for model in models:
        c=SELECTED_C[model]
        for v in (primary if model!='TFIDF_SVM' else primary[:2]):run(model,v,c,'primary')
        for v in ['FULL','MASKED']:run(model,v,1.,'C1_sensitivity')
        if model!='TFIDF_SVM':
            for v in primary:run(model,v,c,'same_fitted_FULL',fit_variant='FULL')
        for v in ['FULL','MASKED']:run(model,v,c,'dedup_only',fitmask=dedup)
        run(model,'REVISED',c,'mask_only')
        run(model,'REVISED',c,'dedup_and_mask',fitmask=dedup)
        if model!='TFIDF_SVM':
            for seed in SEEDS:
                run(model,f'REVISED_RANDOM_{seed}',c,'mask_only')
                run(model,f'REVISED_RANDOM_{seed}',c,'dedup_and_mask',fitmask=dedup)
        if model=='TFIDF_LR':
            for v in ['OLD','BOUNDARY_ONLY','RULE_ONLY','COMBINED']:
                run(model,v,c,'components')
                for seed in SEEDS:run(model,f'{v}_RANDOM_{seed}',c,'components')
        if model=='LEGAL_BERT_LR':
            for cc in [.1,1.]:
                for v in ['FULL','MASKED']:
                    run(model,v,cc,'chunk_ablation')
                    run(model,v+'_FIRST',cc,'chunk_ablation')
        if model!='TFIDF_SVM':
            # Nested samples of whole training families, unrelated to validation
            # outcomes. No selection of a favourable seed or sample afterwards.
            groups=sorted({r['family_id'] for r in rows if r['period']=='train'})
            for seed in SEEDS[:3]:
                order=np.random.default_rng(seed).permutation(groups)
                for f in [.25,.5,.75,1.]:
                    chosen=set(order[:int(np.ceil(len(groups)*f))]);mask=train&np.array([r['family_id'] in chosen for r in rows])
                    assert set(y[mask])=={0,1}
                    subsets.append({'model':model,'seed':seed,'fraction':f,'case_ids':[r['case_id'] for r,m in zip(rows,mask) if m]})
                    run(model,'MASKED',c,'learning_curve',fitmask=mask,seed=seed,fraction=f)
    out=HERE/'results'/args.stage;out.mkdir(parents=True,exist_ok=True)
    write(out/'metrics.json',results);csvout(out/'metrics.csv',results);jsonl(out/'predictions.jsonl',predictions)
    write(out/'learning_subsets.json',subsets)
    write(out/'run.json',{'stage':args.stage,'elapsed_seconds':time.perf_counter()-start,
        'code_sha256':digest(Path(__file__).read_bytes()),'software':{k:version(k) for k in ['numpy','scikit-learn','scipy']},
        'counts':dict(Counter(r['period'] for r in rows)),'test_accessed':False,'fits':len(fitcache),'runs':len(results),
        'sha256':{p.name:digest(p.read_bytes()) for p in out.glob('*') if p.name!='run.json'}})
    print('STAGE COMPLETE',args.stage,flush=True)

if __name__=='__main__':main()
