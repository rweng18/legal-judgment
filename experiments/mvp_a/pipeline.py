"""Reviewed-team-data MVP: immutable integration, development experiments, diagnostics.

No function evaluates final-test cases. Annotation metadata is never a feature.
Becca's frozen cleaner/masker are reused unchanged; earlier artifacts stay intact.
"""
from pathlib import Path
import collections,hashlib,importlib.metadata,json,math,random,re,subprocess,sys,time
import numpy as np
import joblib
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score,balanced_accuracy_score,f1_score,confusion_matrix,recall_score,cohen_kappa_score

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=HERE/'outputs';OUT.mkdir(exist_ok=True)
BECCA=ROOT/'annotation/submissions/becca/MVP'
HAYDEN=ROOT/'annotation/submissions/hyunsang/batches/A/mvp_additions'
TRIAL=ROOT/'experiments/provisional_a'
SEED=20261025;CONTROL_SEEDS=[11,23,37,51,71];C_GRID=[.1,1.,10.]
BASE_COMMIT='ecca2a4'  # Exact full SHA is recorded during preparation.
sys.path.insert(0,str(BECCA/'preprocessing'))
import full_text,masked_text_v2,model_inputs,verify_masked_v2
sys.path.insert(0,str(TRIAL))
from train import encoder_features  # Pinned, tested inference implementation; never calls trial main().

def read(path):return json.loads(Path(path).read_text(encoding='utf8'))
def rows(path):return [json.loads(s) for s in Path(path).read_text(encoding='utf8').splitlines() if s.strip()]
def canonical(path):return Path(path).read_bytes().replace(b'\r\n',b'\n')
def digest_bytes(b):return hashlib.sha256(b).hexdigest()
def file_hash(path):return digest_bytes(canonical(path))
def text_hash(text):return digest_bytes(text.encode('utf8'))
def write_json(path,obj,immutable=False):
    path=Path(path);content=json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if immutable and path.exists():assert read(path)==obj,f'Frozen artifact changed: {path}; use a new version.'
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content,encoding='utf8',newline='\n')
def write_rows(path,items,immutable=False):
    path=Path(path)
    if immutable and path.exists():assert rows(path)==items,f'Frozen artifact changed: {path}'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n' for r in items),encoding='utf8',newline='\n')
def describe(values):
    a=np.asarray(values);return dict(n=len(a),min=float(a.min()),median=float(np.median(a)),mean=float(a.mean()),p90=float(np.percentile(a,90)),max=float(a.max()))
def random_control(text,budget,seed,cid):
    """Uniform sentence order; partial last sentence exactly matches word loss."""
    tokens=list(re.finditer(r'\S+',text));spans=list(masked_text_v2.sentence_spans(text))
    groups=[[i for i,t in enumerate(tokens) if a<=t.start()<b] for a,b in spans]
    assert sorted(i for g in groups for i in g)==list(range(len(tokens)))
    rng=random.Random(int(text_hash(f'{seed}:{cid}')[:16],16));order=list(range(len(groups)));rng.shuffle(order);drop=set();partial=False
    for j in order:
        left=budget-len(drop)
        if left<=0:break
        ids=groups[j]
        if len(ids)<=left:drop.update(ids)
        else:
            start=rng.randrange(len(ids)-left+1);drop.update(ids[start:start+left]);partial=True
    assert len(drop)==budget and budget<len(tokens)
    return ' '.join(t.group() for i,t in enumerate(tokens) if i not in drop),dict(removed_word_indices=sorted(drop),partial_final_sentence=partial)

def prepare_dataset():
    """Validate the 114-case handoff, append approved additions, preserve old splits."""
    # Windows checkout line endings differ from the LF bytes used in Becca's manifests.
    # Verify against Git blobs, then supply a canonical LF copy to her strict loader.
    cache=HERE/'.cache/canonical_becca';files=['data/full_v1/full.jsonl','data/full_v1/manifest.json','data/masked_v2/masked.jsonl','data/masked_v2/manifest.json','data/mvp_split_v1/split_manifest.json']
    for name in files:
        original=BECCA/name;data=canonical(original)
        committed=subprocess.check_output(['git','show','HEAD:'+original.relative_to(ROOT).as_posix()],cwd=ROOT)
        assert data==committed,f'Working text differs from committed LF source: {name}'
        target=cache/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    # The original disk loader builds a backslash key on Windows but looks up a
    # slash key. Preserve its record validator and reproduce all file checks here.
    base_manifest=read(cache/'data/mvp_split_v1/split_manifest.json');exports={}
    split_hash=file_hash(cache/'data/mvp_split_v1/split_manifest.json')
    for variant,relative in model_inputs.VARIANTS.items():
        path=cache/'data'/relative;manifest=read(path.parent/'manifest.json')
        assert file_hash(path)==manifest['outputs'][path.name]
        if variant=='MASKED':
            assert manifest['input_sha256']['full']==file_hash(cache/'data/full_v1/full.jsonl')
            assert manifest['input_sha256']['split']==split_hash
        else:assert next(v for k,v in manifest['inputs'].items() if k.endswith('mvp_split_v1/split_manifest.json'))==split_hash
        exports[variant]=rows(path)
    indexed,base_cases=model_inputs.validate_records(exports,base_manifest)
    contract=dict(status='passed',validator='Becca model_inputs.validate_records',disk_adapter='LF canonical files verified against Git blobs; portable slash keys; all export/split/FULL-base checksum checks retained',base_counts={k:len(v) for k,v in base_manifest['split_case_ids'].items()})
    assert verify_masked_v2.check_rules()==33
    mask_policy=read(BECCA/'preprocessing/masked_rules_v2.json')
    assert file_hash(BECCA/'preprocessing/masked_text_v2.py')==mask_policy['input_sha256']['code']
    clean_policy=read(BECCA/'preprocessing/full_rules_v1.json')
    assert file_hash(BECCA/'preprocessing/full_text.py')==clean_policy['cleaner_sha256']
    sources={r['case_id']:r for r in rows(ROOT/'annotation/source/cases.jsonl')}
    families={r['case_id']:r for r in rows(BECCA/'data/family_v1/case_family_manifest.jsonl')}
    additions={r['case_id']:r for r in rows(HAYDEN/'additional_6.jsonl')}
    decisions={r['case_id']:r for r in read(HAYDEN/'decisions.json')}
    assert len(base_cases)==114 and len(additions)==6 and not set(base_cases)&set(additions)
    assert set(additions)==set(decisions)
    confirmation=read(HERE/'team_review_confirmation.json');assert confirmation['status']=='team_reviewed'
    manifest=[];dataset=[];masklogs=[];new_cleaning=[]
    for cid in sorted(set(base_cases)|set(additions)):
        s=sources[cid];f=families[cid];new=cid in additions
        if not new:
            old=base_cases[cid];label=old['target'];split=old['split'];status=old['status']
            # Preserve every existing assignment and pending hold exactly.
            assert f['case_family_id']==old['case_family_id']
        else:
            label=additions[cid]['outcome']['binary_label'];assert decisions[cid]['binary_label']==label
            split=f['date_period'];status='assigned'
            if f['cross_period_family'] or (f['family_training_only'] and split!='train'):status='excluded';split=None
            elif f['external_companion_unresolved']:status='pending';split=None
        assert label in [0,1]
        row=dict(case_id=cid,case_name=s['case_name'],date_filed=s['date_filed'],source_url=s['source_url'],family_id=f['case_family_id'],period={'development':'validation'}.get(split,split),status=status,label=label,review_status='team_reviewed',review_confirmation_date='2026-10-25',label_origin='Hayden_accepted_addition' if new else 'three_reviewer_consensus',calibration_exposure=f['family_training_only'],source_text_sha256=s['text_sha256'])
        manifest.append(row)
        if status!='assigned' or split=='test':continue  # No test preprocessing/embedding/modeling.
        if new:
            full,cleanlog=full_text.clean_full(s['text']);masked,masklog=masked_text_v2.mask_text(full)
            new_cleaning.append(dict(case_id=cid,**cleanlog))
        else:
            full=indexed['FULL'][cid]['text'];masked=indexed['MASKED'][cid]['text']
            rebuilt,cleanlog=full_text.clean_full(s['text']);assert rebuilt==full
            rebuilt,masklog=masked_text_v2.mask_text(full);assert rebuilt==masked
        assert full.strip() and masked.strip() and len(masked.split())>=1
        budget=len(full.split())-len(masked.split());assert budget==masklog['removed_words']
        texts={'FULL':full,'MASKED':masked};controls={};tokens=list(re.finditer(r'\S+',full))
        cue_indices={i for i,t in enumerate(tokens) if any(e['start']<=t.start()<e['end'] for e in masklog['edits'])}
        for seed in CONTROL_SEEDS:
            text,log=random_control(full,budget,seed,cid);assert len(text.split())==len(masked.split())
            log['outcome_words_removed']=len(cue_indices&set(log['removed_word_indices']));controls[str(seed)]=log;texts[f'RANDOM_{seed}']=text
        dataset.append(dict(**row,texts=texts,text_hashes={k:text_hash(v) for k,v in texts.items()},word_counts={k:len(v.split()) for k,v in texts.items()},removed_fraction=budget/len(full.split())))
        masklogs.append(dict(case_id=cid,period=row['period'],**masklog,random_controls=controls))
    assert len(manifest)==120 and len({r['case_id'] for r in manifest})==120
    assert {r['case_id'] for r in manifest if r['status']=='pending'}=={'NY-4655053'}
    for split in ['train','validation','test']:
        members=[r for r in manifest if r['period']==split];assert all(not r['calibration_exposure'] or split=='train' for r in members)
        for other in ['train','validation','test']:
            if split!=other:assert not {r['family_id'] for r in members}&{r['family_id'] for r in manifest if r['period']==other}
    assert all(r['period'] in ['train','validation'] for r in dataset)
    write_rows(OUT/'case_manifest.jsonl',manifest,True);write_rows(OUT/'development_cases.jsonl',dataset,True)
    write_rows(OUT/'masking_log.jsonl',masklogs,True);write_rows(OUT/'addition_cleaning_log.jsonl',new_cleaning,True)
    split_counts={p:dict(collections.Counter(str(r['label']) for r in manifest if r['period']==p)) for p in ['train','validation','test']}
    summary=dict(candidate_A=169,consensus_pool=114,accepted_additions=6,selected_pool=120,pending_family=1,assigned_cases=119,remaining_review=35,withheld_any_original_exclude=14,split_class_counts=split_counts,review_status='team_reviewed',test_evaluated=False,
        word_lengths={p:{v:describe([r['word_counts'][v] for r in dataset if r['period']==p]) for v in ['FULL','MASKED']} for p in ['train','validation']},removed_percent=describe([100*r['removed_fraction'] for r in dataset]))
    write_json(OUT/'dataset_summary.json',summary,True)
    # Reproducible, label-stratified audit selection happens before any model fitting.
    audit=[]
    for pi,period in enumerate(['train','validation']):
        for label in [0,1]:
            pool=sorted(r['case_id'] for r in dataset if r['period']==period and r['label']==label)
            audit+=random.Random(20261023+100*pi+label).sample(pool,2)
    write_json(OUT/'mask_audit_sample.json',dict(case_ids=audit,seed=20261023,sampling='two per class per train/validation split, selected before modeling'),True)
    logmap={r['case_id']:r for r in masklogs};packet=['# Pre-model audit: team MASKED v2','Sampled before training. Inspect whole-appeal outcome removal, retained reasoning and historical decisions. No test cases.']
    for row in dataset:
        if row['case_id'] not in audit:continue
        packet += [f"## {row['case_id']} | {row['case_name']} | {row['period']} | {row['label']}",'### FULL',row['texts']['FULL'],'### Removed','\n'.join(f"- [{e['reason']}] {e['removed_text']}" for e in logmap[row['case_id']]['edits']),'### MASKED',row['texts']['MASKED']]
    (OUT/'MASKING_AUDIT_PACKET.md').write_text('\n\n'.join(packet),encoding='utf8',newline='\n')
    input_paths=[BECCA/name for name in files]+[BECCA/'preprocessing/full_text.py',BECCA/'preprocessing/masked_text_v2.py',BECCA/'data/family_v1/case_family_manifest.jsonl',HAYDEN/'additional_6.jsonl',HAYDEN/'decisions.json',HERE/'team_review_confirmation.json',ROOT/'annotation/source/cases.jsonl']
    write_json(OUT/'data_provenance.json',dict(version='reviewed_A_mvp_v1',upstream_main_commit=subprocess.check_output(['git','rev-parse',BASE_COMMIT],cwd=ROOT,text=True).strip(),source_prs=[12,13,14,15,16],input_sha256_lf={p.relative_to(ROOT).as_posix():file_hash(p) for p in input_paths},dataset_sha256_lf=file_hash(OUT/'development_cases.jsonl'),hash_policy='Normalize only file CRLF to LF, verified against Git blobs; opinion strings/hashes remain exact.',review_confirmation=confirmation,original_loader_contract=contract,base_assignment_changes=0,base_text_changes=0,final_test_evaluated=False),True)
    return dataset,summary

def score(y,pred):
    return dict(accuracy=float(accuracy_score(y,pred)),balanced_accuracy=float(balanced_accuracy_score(y,pred)),macro_f1=float(f1_score(y,pred,labels=[0,1],average='macro',zero_division=0)),confusion_matrix=confusion_matrix(y,pred,labels=[0,1]).tolist(),confusion_matrix_row_normalized=confusion_matrix(y,pred,labels=[0,1],normalize='true').tolist(),class_counts={str(k):int(sum(np.asarray(y)==k)) for k in [0,1]},recall_by_class=recall_score(y,pred,labels=[0,1],average=None,zero_division=0).tolist())

def modeling_rows():
    data=rows(OUT/'development_cases.jsonl');p=read(OUT/'data_provenance.json')
    assert file_hash(OUT/'development_cases.jsonl')==p['dataset_sha256_lf']
    for name,h in p['input_sha256_lf'].items():assert file_hash(ROOT/name)==h,f'Changed frozen input: {name}'
    audit=read(OUT/'masking_audit_review.json');assert set(audit['reviewed_case_ids'])==set(read(OUT/'mask_audit_sample.json')['case_ids'])
    assert audit['performed_before_model_fit']
    assert all(r['period'] in ['train','validation'] for r in data)
    return data

def fit_condition(data,name,variant,features=None):
    """Fit each C on train only; predictions and all comparisons use validation IDs."""
    tr=np.array([r['period']=='train' for r in data]);y=np.array([r['label'] for r in data]);va=~tr
    Xtr=features[tr] if features is not None else [r['texts'][variant] for r in data if r['period']=='train']
    Xva=features[va] if features is not None else [r['texts'][variant] for r in data if r['period']=='validation']
    grid=[];predictions=[];coefficients={};start=time.perf_counter();models=OUT/'models';models.mkdir(exist_ok=True)
    for C in C_GRID:
        clf=LinearSVC(C=C,class_weight='balanced',dual='auto',max_iter=20000,random_state=SEED) if name=='TFIDF_SVM' else LogisticRegression(C=C,class_weight='balanced',solver='liblinear',max_iter=10000,random_state=SEED)
        transform=StandardScaler() if features is not None else TfidfVectorizer(ngram_range=(1,2),min_df=2,max_features=30000)
        estimator=make_pipeline(transform,clf).fit(Xtr,y[tr]);pred=estimator.predict(Xva);scores=estimator.decision_function(Xva)
        grid.append(dict(model=name,variant=variant,C=C,**score(y[va],pred)))
        for r,p,s in zip([r for r in data if r['period']=='validation'],pred,scores):predictions.append(dict(case_id=r['case_id'],model=name,variant=variant,C=C,label=r['label'],prediction=int(p),decision_score=float(s)))
        joblib.dump(estimator,models/f'{name}_{variant}_C{C:g}.joblib')
        if name=='TFIDF_LR' and C==1:
            names=estimator[0].get_feature_names_out();coef=estimator[-1].coef_[0];order=np.argsort(coef)
            coefficients={'toward_0':[dict(term=str(names[i]),weight=float(coef[i])) for i in order[:15]],'toward_1':[dict(term=str(names[i]),weight=float(coef[i])) for i in order[-15:][::-1]]}
    return dict(grid=grid,predictions=predictions,coefficients=coefficients,seconds=time.perf_counter()-start)

def run_lexical():
    data=modeling_rows();train=[r for r in data if r['period']=='train'];val=[r for r in data if r['period']=='validation']
    dummy=DummyClassifier(strategy='most_frequent').fit(np.zeros((len(train),1)),[r['label'] for r in train]);pred=dummy.predict(np.zeros((len(val),1)))
    result=dict(grid=[dict(model='Majority',variant='FULL',C=None,**score([r['label'] for r in val],pred))],predictions=[dict(case_id=r['case_id'],model='Majority',variant='FULL',C=None,label=r['label'],prediction=int(p),decision_score=None) for r,p in zip(val,pred)],coefficients={},timings={})
    for name in ['TFIDF_LR','TFIDF_SVM']:
        for variant in ['FULL','MASKED']+([f'RANDOM_{s}' for s in CONTROL_SEEDS] if name=='TFIDF_LR' else []):
            fitted=fit_condition(data,name,variant);result['grid']+=fitted['grid'];result['predictions']+=fitted['predictions'];result['timings'][f'{name}_{variant}']=fitted['seconds']
            if name=='TFIDF_LR':result['coefficients'][variant]=fitted['coefficients']
            print(f'Finished {name} {variant}',flush=True)
    if (OUT/'lexical_results.json').exists():
        old=read(OUT/'lexical_results.json')
        for key in ['grid','predictions','coefficients']:assert old[key]==result[key],f'Changed lexical {key}; use a new run.'
    else:write_json(OUT/'lexical_results.json',result)
    return read(OUT/'lexical_results.json')

def run_encoder():
    data=modeling_rows();config=read(TRIAL/'config.json');config['seed']=SEED;config['encoder_revision']=read(TRIAL/'model_lock.json')['revision']
    start=time.perf_counter();features,lock=encoder_features(data,config,OUT);result=dict(grid=[],predictions=[],encoder_lock=lock,seconds=time.perf_counter()-start)
    for variant,X in features.items():
        assert X.shape==(len(data),768)
        fitted=fit_condition(data,'LEGAL_BERT_LR',variant,X);result['grid']+=fitted['grid'];result['predictions']+=fitted['predictions']
    # Time is run-specific, but scores must remain reproducible.
    if (OUT/'encoder_results.json').exists():
        old=read(OUT/'encoder_results.json');assert old['grid']==result['grid'] and old['predictions']==result['predictions']
    else:write_json(OUT/'encoder_results.json',result)
    return read(OUT/'encoder_results.json')

def summarize_results():
    lexical=read(OUT/'lexical_results.json');bert=read(OUT/'encoder_results.json');grid=lexical['grid']+bert['grid'];pred=lexical['predictions']+bert['predictions']
    fixed=[r for r in grid if r['C'] in [None,1.]];selected=[]
    for model,variant in sorted({(r['model'],r['variant']) for r in grid}):
        selected.append(sorted([r for r in grid if (r['model'],r['variant'])==(model,variant)],key=lambda r:(-r['balanced_accuracy'],-r['macro_f1'],r['C'] or 0))[0])
    random_stats={k:dict(mean=float(np.mean(a:=[r[k] for r in fixed if r['variant'].startswith('RANDOM_')])),sd_across_seeds=float(np.std(a,ddof=1)),values=a) for k in ['accuracy','balanced_accuracy','macro_f1']}
    output=dict(review_status='team_reviewed_2026-10-25',evaluation='development_validation_only',class_order=[0,1],fixed_C=1,grid=grid,fixed=fixed,selected_on_validation=selected,random_control=random_stats,test_evaluated=False)
    write_json(OUT/'metrics.json',output,True);write_rows(OUT/'validation_predictions.jsonl',pred,True)
    write_json(OUT/'runtime_provenance.json',dict(seed=SEED,C_grid=C_GRID,random_seeds=CONTROL_SEEDS,packages={p:importlib.metadata.version(p) for p in ['numpy','scipy','scikit-learn','torch','transformers','nbformat','nbclient']},encoder_lock=bert['encoder_lock'],encoder_seconds=bert['seconds'],code_hashes_lf={p.relative_to(ROOT).as_posix():file_hash(p) for p in [Path(__file__),TRIAL/'train.py',TRIAL/'model_lock.json']},test_evaluated=False))
    return output

def paired_bootstrap(n_boot=5000):
    """Descriptive paired family bootstrap on validation; NOT final-test uncertainty.

    Ordinary family resampling preserves pairing. Replicates lacking either true
    class are skipped and counted. Fixed-C scores avoid hyperparameter selection
    inside this interval, but prior development reuse still limits inference.
    """
    data=[r for r in modeling_rows() if r['period']=='validation'];pred=rows(OUT/'validation_predictions.jsonl');ids=[r['case_id'] for r in data];y=np.array([r['label'] for r in data]);groups=sorted({r['family_id'] for r in data})
    bygroup={g:[i for i,r in enumerate(data) if r['family_id']==g] for g in groups};rng=np.random.default_rng(SEED);indices=[];skipped=0
    for _ in range(n_boot):
        idx=np.concatenate([bygroup[g] for g in rng.choice(groups,len(groups),replace=True)])
        if len(set(y[idx]))<2:skipped+=1
        else:indices.append(idx)
    def fast_metrics(t,p):
        cm=np.bincount(2*t+p,minlength=4).reshape(2,2);tp=np.diag(cm);rec=tp/cm.sum(axis=1);den=cm.sum(axis=0)+cm.sum(axis=1);f=np.divide(2*tp,den,out=np.zeros(2),where=den!=0)
        return np.array([tp.sum()/cm.sum(),rec.mean(),f.mean()])
    metrics=['accuracy','balanced_accuracy','macro_f1'];result={}
    for model in ['TFIDF_LR','TFIDF_SVM','LEGAL_BERT_LR']:
        values={}
        for variant in ['FULL','MASKED']:
            pp={r['case_id']:r['prediction'] for r in pred if r['model']==model and r['variant']==variant and r['C']==1};p=np.array([pp[cid] for cid in ids]);values[variant]=np.array([fast_metrics(y[ix],p[ix]) for ix in indices])
        result[model]={variant:{k:list(map(float,np.percentile(v[:,j],[2.5,97.5]))) for j,k in enumerate(metrics)} for variant,v in {**values,'FULL_minus_MASKED':values['FULL']-values['MASKED']}.items()}
    out=dict(scope='descriptive_validation_only',method='paired ordinary family percentile bootstrap; not adjusted for previous development reuse',attempted=n_boot,valid=len(indices),skipped_single_class=skipped,seed=SEED,intervals=result)
    write_json(OUT/'bootstrap_validation.json',out,True);return out

def diagnostics():
    """Descriptive groups and complete validation review queue, not further tuning."""
    data=modeling_rows();val=[r for r in data if r['period']=='validation'];pred=rows(OUT/'validation_predictions.jsonl');result=read(OUT/'metrics.json');lookup={r['case_id']:r for r in val}
    subgroups=[]
    for condition in result['fixed']:
        if condition['variant'].startswith('RANDOM_'):continue
        pp=[r for r in pred if (r['model'],r['variant'],r['C'])==(condition['model'],condition['variant'],condition['C'])]
        for name,lo,hi in [('short',0,400),('medium',400,800),('long',800,1000000)]:
            p=[r for r in pp if lo<=lookup[r['case_id']]['word_counts']['FULL']<hi]
            if not p:continue
            row=dict(model=condition['model'],variant=condition['variant'],group=name,n=len(p),class_counts=dict(collections.Counter(str(r['label']) for r in p)))
            if len({r['label'] for r in p})==2:row.update(score([r['label'] for r in p],[r['prediction'] for r in p]))
            else:row['note']='Single true class; omit two-class subgroup scores.'
            subgroups.append(row)
    write_json(OUT/'length_subgroups.json',subgroups,True)
    logs={r['case_id']:r for r in rows(OUT/'masking_log.jsonl')};packet=['# Development error review: all 16 validation opinions','Team-reviewed labels, preliminary model results. Model scores are not calibrated probabilities. No labels or masks are revised using this packet.']
    overview=[]
    for r in val:
        pp=[p for p in pred if p['case_id']==r['case_id'] and p['C']==1 and p['variant'] in ['FULL','MASKED']]
        line=dict(case_id=r['case_id'],case_name=r['case_name'],label=r['label'],full_words=r['word_counts']['FULL'],masked_words=r['word_counts']['MASKED'])
        for p in pp:line[p['model']+'_'+p['variant']]=p['prediction']
        overview.append(line)
        packet += [f"## {r['case_id']} — {r['case_name']}",f"[Source]({r['source_url']}); reviewed label {r['label']}; FULL {r['word_counts']['FULL']} words, MASKED {r['word_counts']['MASKED']} words.",'\n'.join(f"- {p['model']} {p['variant']}: {p['prediction']} ({'correct' if p['prediction']==r['label'] else 'error'})" for p in pp),'### Removed passages','\n'.join(e['removed_text'] for e in logs[r['case_id']]['edits']),'### FULL',r['texts']['FULL'],'### MASKED',r['texts']['MASKED']]
    write_rows(OUT/'error_overview.jsonl',overview,True);(OUT/'ERROR_REVIEW_PACKET.md').write_text('\n\n'.join(packet),encoding='utf8',newline='\n')
    # These measure original independent annotation submissions, NOT new human gold.
    reviewers={name:{r['case_id']:r for r in rows(ROOT/f'annotation/submissions/{name}/batches/A/annotations.jsonl')} for name in ['becca','hyunsang','yinkui']}
    common_ids=sorted(set.intersection(*(set(r) for r in reviewers.values())));agreement=[]
    import itertools
    for a,b in itertools.combinations(reviewers,2):
        x=[reviewers[a][cid]['eligibility']['binary_task'] for cid in common_ids];y=[reviewers[b][cid]['eligibility']['binary_task'] for cid in common_ids]
        agreement.append(dict(reviewers=[a,b],n=len(common_ids),eligibility_agreement=float(np.mean(np.array(x)==np.array(y))),eligibility_kappa=float(cohen_kappa_score(x,y))))
    original_consensus={r['case_id']:r for r in read(BECCA/'data/mvp_split_v1/split_manifest.json')['cases']}
    consensus_binary=sum(len({reviewers[name][cid]['outcome']['binary_label'] for name in reviewers})==1 for cid in original_consensus)
    write_json(OUT/'annotation_agreement.json',dict(scope='Original independent LLM-assisted drafts, before team acceptance; not agreement of new blinded human labels',pairwise=agreement,unanimous_pool=len(original_consensus),unanimous_binary_labels_in_pool=consensus_binary),True)
    random_overlap={str(seed):dict(removed_words=sum(len(logs[r['case_id']]['random_controls'][str(seed)]['removed_word_indices']) for r in data),outcome_words_accidentally_removed=sum(logs[r['case_id']]['random_controls'][str(seed)]['outcome_words_removed'] for r in data)) for seed in CONTROL_SEEDS}
    write_json(OUT/'random_control_overlap.json',random_overlap,True)
    return overview,subgroups

def validate_results():
    """Independent metric recomputation and leakage invariants for delivered artifacts."""
    data=modeling_rows();m=read(OUT/'metrics.json');pred=rows(OUT/'validation_predictions.jsonl');expected={r['case_id'] for r in data if r['period']=='validation'}
    for condition in m['grid']:
        p=[r for r in pred if (r['model'],r['variant'],r['C'])==(condition['model'],condition['variant'],condition['C'])]
        assert len(p)==len(expected) and {r['case_id'] for r in p}==expected
        calculated=score([r['label'] for r in p],[r['prediction'] for r in p])
        assert all(condition[k]==v for k,v in calculated.items())
    assert len(m['grid'])==34
    for r in data:
        for seed in CONTROL_SEEDS:assert r['word_counts']['MASKED']==r['word_counts'][f'RANDOM_{seed}']
    for variant in ['FULL','MASKED']:
        model=joblib.load(OUT/'models'/f'TFIDF_LR_{variant}_C1.joblib');analyzer=model[0].build_analyzer()
        trainterms=set(term for r in data if r['period']=='train' for term in analyzer(r['texts'][variant]))
        assert set(model[0].vocabulary_)<=trainterms
        features=np.load(OUT/'encoder_cache'/f'{variant}.npy');assert features.shape==(len(data),768) and np.isfinite(features).all()
    checks=dict(status='passed',model_C_conditions=34,validation_cases=len(expected),development_cases=len(data),matched_random_budgets=True,training_only_vocabulary=True,feature_shapes_valid=True,test_predictions=0,review_status='team_reviewed')
    write_json(OUT/'verification.json',checks,True);return checks

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','lexical','encoder','summarize','bootstrap']);a=p.parse_args()
    result={'prepare':prepare_dataset,'lexical':run_lexical,'encoder':run_encoder,'summarize':summarize_results,'bootstrap':paired_bootstrap}[a.stage]()
    if a.stage=='prepare':print(json.dumps(result[1],indent=2))
    else:print(f'Completed {a.stage}')
