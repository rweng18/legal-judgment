"""Reviewed release and single reserved-test evaluation, with immutable protocol."""
import argparse,datetime,time
from collections import Counter,defaultdict
from common import *
from quality import revised_mask
import numpy as np

FINAL=HERE/'final'

def freeze():
    target=FINAL/'inputs'
    if (target/'protocol.json').exists():raise FileExistsError('Protocol already frozen; do not silently replace it.')
    metadata=records(HERE/'inputs/release/manifest.jsonl');source={r['case_id']:r for r in records(ROOT/'annotation/source/cases.jsonl')}
    candidates=read(HERE/'review/test_review_template.json')['cases'];assert len(candidates)==50
    amap={r['case_id']:r for r in records(ROOT/'experiments/mvp_a/outputs/case_manifest.jsonl')}
    votes={};refs={};sourcehashes={}
    for batch in ['B','C']:
        votes[batch]={}
        for reviewer in ['becca','hyunsang','yinkui']:
            path=f'annotation/submissions/{reviewer}/batches/{batch}/annotations.jsonl'
            if reviewer=='yinkui':
                ref=('87f7771b01cb8fcd75860e240c0b075a09bb3f61' if batch=='C' else subprocess.check_output(['git','rev-parse','origin/annotations/yinkui-batch-b'],cwd=ROOT,text=True).strip())
                raw=subprocess.check_output(['git','show',f'{ref}:{path}'],cwd=ROOT);refs[path]=ref
            else:raw=blob(path);refs[path]=BASE
            sourcehashes[path]=digest(raw);votes[batch][reviewer]={r['case_id']:r for r in map(json.loads,raw.decode('utf8').splitlines())}
    aclean=module('final_a_clean','annotation/submissions/becca/MVP/preprocessing/full_text.py')
    def transform(r):
        full=aclean.clean_full(r['text'])[0] if r['batch']=='A' else OLD.clean_text(r['text'])[0]
        masked=SENTENCES.mask_text(full)[0] if r['batch']=='A' else NEW.mask(full)[0]
        assert full.strip() and masked.strip()
        texts={'FULL':full,'MASKED':masked,'REVISED':revised_mask(full)[0]};logs={}
        for seed in SEEDS:texts[f'RANDOM_{seed}'],logs[str(seed)]=random_remove(full,len(full.split())-len(masked.split()),seed,r['case_id'])
        return texts,logs
    # Prove the exact same batch-specific preparation recreates all development
    # strings before applying those frozen functions to the test opinions.
    development=load_rows();devvars={r['case_id']:r['texts'] for r in records(HERE/'inputs/variants.jsonl')}
    qvars={r['case_id']:r['texts']['REVISED'] for r in records(HERE/'inputs/quality_v1/variants.jsonl')}
    for r in development:
        rebuilt,_=transform({**source[r['case_id']],'batch':r['batch']})
        assert all(rebuilt[v]==r['texts'][v] for v in ['FULL','MASKED']),(r['case_id'],'pipeline mismatch')
    tests=[];logs=[];provenance=[];manifest=[]
    for c in candidates:
        cid=c['case_id'];s=source[cid];b=c['batch'];assert s['text_sha256']==c['source_text_sha256']==text_hash(s['text'])
        if b=='A':
            a=amap[cid];assert a['status']=='assigned' and a['period']=='test' and a['review_status']=='team_reviewed';label=a['label'];basis={'A_reviewed_manifest_label':label}
        else:
            vv={who:rr[cid] for who,rr in votes[b].items()}
            assert all(r['eligibility']['binary_task']=='include' and r['text_sha256']==s['text_sha256'] for r in vv.values()),cid
            labels=[r['outcome']['binary_label'] for r in vv.values()]
            assert len(set(labels))==1 and type(labels[0]) is int and labels[0] in [0,1],f'Conflicting test label: {cid}'
            label=labels[0];basis={who:{'label':r['outcome']['binary_label'],'source_status':r['run']['review_status']} for who,r in vv.items()}
        texts,rr=transform({**s,'batch':b});assert all(t.strip() for t in texts.values())
        row={'case_id':cid,'batch':b,'period':'test','date_filed':s['date_filed'],'family_id':c['suggested_family_id'],'label':label,
             'source_text_sha256':s['text_sha256'],'reviewer':'Yinkui Yu','review_date':'2026-11-19','review_status':'human_review_confirmed_by_user',
             'texts':texts,'text_sha256':{v:text_hash(t) for v,t in texts.items()}}
        tests.append(row);logs.append({'case_id':cid,'random':rr});provenance.append({'case_id':cid,'basis':basis})
    train=[]
    for r in development:
        if r['case_id']=='NY-6112018':continue
        texts={v:devvars[r['case_id']][v] for v in ['FULL','MASKED',*[f'RANDOM_{s}' for s in SEEDS]]};texts['REVISED']=qvars[r['case_id']]
        record={k:r[k] for k in ['case_id','batch','period','date_filed','family_id','label','source_text_sha256']}
        record.update(reviewer='Yinkui Yu',review_date='2026-11-19',review_status='human_review_confirmed_by_user')
        manifest.append(record)
        if r['period']=='train':train.append({**record,'texts':texts})
    manifest += [{k:v for k,v in r.items() if k not in ['texts','text_sha256']} for r in tests]
    assert len(train)==278 and len(tests)==50 and len(manifest)==370
    for p in ['train','validation','test']:
        fam={r['family_id'] for r in manifest if r['period']==p}
        assert fam.isdisjoint(r['family_id'] for r in manifest if r['period']!=p)
    assert not {r['source_text_sha256'] for r in tests}&{r['source_text_sha256'] for r in manifest if r['period']!='test'}
    jsonl(target/'train.jsonl',train);jsonl(target/'test.jsonl',tests);jsonl(target/'reviewed_manifest.jsonl',manifest)
    jsonl(target/'test_label_provenance.jsonl',provenance);jsonl(target/'test_random_logs.jsonl',logs)
    write(target/'human_review_confirmation.json',{'reviewer':'Yinkui Yu','review_date':'2026-11-19','recorded_client_date':'2026-11-20',
        'user_statement':"also I have done reviewing, no duplicate or related appeal corrections. Reviewer Yinkui Yu, date 11/19",
        'scope_interpretation':'Acceptance of the 320-row development and 50-candidate test review lists just supplied, with existing agreed labels and no additional family corrections; this interpretation was stated to the user in chat.',
        'earlier_decisions':'Exclude all 54 B/C eligibility disagreements; approved Mann duplicate removal and versioned mask corrections.',
        'limits':'User-attested review, not a newly measured blinded inter-human agreement study; original draft files and past provisional results preserved.',
        'source_revisions':refs,'annotation_sha256':sourcehashes})
    protocol={'version':'reviewed_final_v1','client_date':'2026-11-20','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'review_status':'user_confirmed_review','reviewer':'Yinkui Yu','review_date':'2026-11-19','source_commit':BASE,
        'training':'2010-2020 only, 278 rows; do not refit on 42 validation rows','test':'2023-2024, 50 reviewed selected records',
        'counts':{p:dict(Counter(r['label'] for r in manifest if r['period']==p)) for p in ['train','validation','test']},
        'C_by_model':SELECTED_C,'seeds':SEEDS,'primary_comparisons':'Majority, LR, SVM, BERT FULL/MASKED; five matched random controls for LR and BERT.',
        'secondary':'REVISED mask for all three classifiers, kept separate from primary. No choosing a mask, seed, or C after final scores.',
        'metrics':['accuracy','balanced_accuracy','macro_f1','confusion_matrix','class_counts','per_class_recall'],
        'bootstrap':'5000 paired family resamples, seed 20261120; same draws across conditions, omit single-class draws; percentile 95% intervals. Conditional on this fixed fitted training sample.',
        'dedup':'Approved Mann alias NY-6112018 removed; no further corrections per reviewer. Other retained same-family records are not asserted to be distinct decisions.',
        'masking':'Primary exact upstream policy by batch, secondary quality_v1; known residual cues and mixed reasoning loss disclosed. No further rules changed for test.',
        'code_sha256':{n:digest((HERE/n).read_bytes()) for n in ['final_test.py','quality.py','common.py']},
        'sha256':{p.name:digest(p.read_bytes()) for p in target.glob('*') if p.name!='protocol.json'}}
    write(target/'protocol.json',protocol);print(json.dumps(protocol['counts'],indent=2));print('FINAL PROTOCOL FROZEN; NO TEST PREDICTIONS YET')

def evaluate():
    from modeling import estimator,scores
    target=FINAL/'inputs';protocol=read(target/'protocol.json');out=FINAL/'results'
    if (out/'metrics.json').exists():raise FileExistsError('Reserved test already evaluated; read its saved outputs.')
    for n,h in protocol['sha256'].items():assert digest((target/n).read_bytes())==h
    for n,h in protocol['code_sha256'].items():assert digest((HERE/n).read_bytes())==h
    train=records(target/'train.jsonl');test=records(target/'test.jsonl');yt=np.array([r['label'] for r in train]);y=np.array([r['label'] for r in test])
    dev=load_rows();take=[i for i,r in enumerate(dev) if r['period']=='train' and r['case_id']!='NY-6112018']
    assert [dev[i]['case_id'] for i in take]==[r['case_id'] for r in train]
    index=read(FINAL/'embeddings/index.json');assert index['case_ids']==[r['case_id'] for r in test]
    for n,h in index['sha256'].items():assert digest((FINAL/'embeddings'/n).read_bytes())==h
    di=read(HERE/'results/embeddings/index.json')
    for n,h in di['sha256'].items():assert digest((HERE/'results/embeddings'/n).read_bytes())==h
    metrics=[];preds=[];prediction_vectors={};started=time.perf_counter()
    for model in ['Majority',*SELECTED_C]:
        variants=['FULL','MASKED']+([] if model=='Majority' else ['REVISED'])+([f'RANDOM_{s}' for s in SEEDS] if model in ['TFIDF_LR','LEGAL_BERT_LR'] else [])
        for v in variants:
            c=SELECTED_C.get(model)
            if model=='Majority':yp=np.full(len(y),np.argmax(np.bincount(yt,minlength=2)));d=[None]*len(y)
            else:
                if model=='LEGAL_BERT_LR':
                    x=np.load(HERE/'results/embeddings'/f'{v}.npy')[take];xt=np.load(FINAL/'embeddings'/f'{v}.npy')
                else:x=[r['texts'][v] for r in train];xt=[r['texts'][v] for r in test]
                fitted=estimator(model,c).fit(x,yt);yp=fitted.predict(xt);d=fitted.decision_function(xt).tolist()
            run=f'{model}:{v}';prediction_vectors[run]=yp
            metrics.append({'run_id':run,'model':model,'variant':v,'C':c,'n_train':len(yt),'train_0':int(sum(yt==0)),'train_1':int(sum(yt==1)),
                'n_test':len(y),'test_0':int(sum(y==0)),'test_1':int(sum(y==1)),**scores(y,yp)})
            preds.extend({'run_id':run,'case_id':r['case_id'],'family_id':r['family_id'],'batch':r['batch'],'label':r['label'],'prediction':int(p),'decision_score':s} for r,p,s in zip(test,yp,d))
    # Test predictions are made exactly once; subsequent notebook runs verify
    # saved predictions and do not retrain or search this test set.
    fam=sorted({r['family_id'] for r in test});fi=np.array([fam.index(r['family_id']) for r in test])
    w=np.random.default_rng(20261120).multinomial(len(fam),np.ones(len(fam))/len(fam),5000)[:,fi]
    w=w[(w[:,y==0].sum(1)>0)&(w[:,y==1].sum(1)>0)]
    def boot(p):
        a,b,c,d=[w@((y==i)&(p==j)).astype(float) for i,j in [(0,0),(0,1),(1,0),(1,1)]]
        return np.stack([(a+d)/(a+b+c+d),.5*(a/(a+b)+d/(c+d)),.5*(2*a/(2*a+b+c)+2*d/(2*d+b+c))],1)
    boots={k:boot(p) for k,p in prediction_vectors.items()};intervals=[];diffs=[];names=['accuracy','balanced_accuracy','macro_f1']
    for m in metrics:
        for j,key in enumerate(names):
            lo,hi=np.quantile(boots[m['run_id']][:,j],[.025,.975]);intervals.append({'run_id':m['run_id'],'metric':key,'value':m[key],'lower':float(lo),'upper':float(hi)})
    for model in SELECTED_C:
        pairs=[('FULL - MASKED',[f'{model}:FULL'],[f'{model}:MASKED']),('REVISED - MASKED',[f'{model}:REVISED'],[f'{model}:MASKED'])]
        if model!='TFIDF_SVM':pairs.append(('mean RANDOM - MASKED',[f'{model}:RANDOM_{s}' for s in SEEDS],[f'{model}:MASKED']))
        for name,ll,rr in pairs:
            dist=np.mean([boots[k] for k in ll],0)-np.mean([boots[k] for k in rr],0)
            for j,key in enumerate(names):
                lo,hi=np.quantile(dist[:,j],[.025,.975]);point=np.mean([next(m[key] for m in metrics if m['run_id']==k) for k in ll])-np.mean([next(m[key] for m in metrics if m['run_id']==k) for k in rr])
                diffs.append({'model':model,'comparison':name,'metric':key,'difference':float(point),'lower':float(lo),'upper':float(hi)})
    write(out/'metrics.json',metrics);csvout(out/'metrics.csv',metrics);jsonl(out/'predictions.jsonl',preds)
    write(out/'intervals.json',intervals);write(out/'paired_intervals.json',diffs)
    write(out/'verification.json',{'runs':len(metrics),'predictions':len(preds),'test_families':len(fam),'bootstrap_valid_draws':len(w),
        'protocol_sha256':digest((target/'protocol.json').read_bytes()),'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'elapsed_seconds':time.perf_counter()-started,'test_once':True,'no_test_tuning':True,
        'code_sha256':digest(Path(__file__).read_bytes()),'output_sha256':{p.name:digest(p.read_bytes()) for p in out.glob('*') if p.name!='verification.json'}})
    print('FINAL EVALUATION COMPLETE:',len(metrics),'conditions;',len(y),'test records')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['freeze','evaluate']);args=ap.parse_args()
    freeze() if args.action=='freeze' else evaluate()
