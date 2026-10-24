"""Development experiments only. The final test opinions never enter this runner."""
import argparse, collections, importlib.metadata, json, math, os, platform, time
import joblib
import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, confusion_matrix, recall_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC
from common import HERE, ROOT, read, records, dump, jsonl, sha, output
from prepare import summary

def metrics(y, pred):
    return {'accuracy':float(accuracy_score(y,pred)), 'balanced_accuracy':float(balanced_accuracy_score(y,pred)),
        'macro_f1':float(f1_score(y,pred,labels=[0,1],average='macro',zero_division=0)),
        'confusion_matrix':confusion_matrix(y,pred,labels=[0,1]).tolist(),
        'confusion_matrix_row_normalized':confusion_matrix(y,pred,labels=[0,1],normalize='true').tolist(),
        'class_counts':{str(k):int(sum(np.asarray(y)==k)) for k in [0,1]},
        'recall_by_class':recall_score(y,pred,labels=[0,1],average=None,zero_division=0).tolist()}

def validate_development(rows):
    assert rows and {r['period'] for r in rows}=={'train','validation'}
    assert len({r['case_id'] for r in rows})==len(rows)
    assert all(r['eligibility']=='include' and r['label'] in [0,1] for r in rows)
    assert not ({r['family_id'] for r in rows if r['period']=='train'} & {r['family_id'] for r in rows if r['period']=='validation'})
    assert all(not r['calibration_exposure'] or r['period']=='train' for r in rows)

def encoder_features(rows, c, out):
    import torch
    from transformers import AutoTokenizer, AutoModel
    from huggingface_hub import snapshot_download
    lock=read(HERE/'model_lock.json')
    assert lock['model']==c['encoder']
    if c.get('encoder_revision'):assert c['encoder_revision']==lock['revision']
    # This stage is offline: explicitly download the locked snapshot beforehand.
    path=snapshot_download(c['encoder'],revision=lock['revision'],cache_dir=str(HERE/'.cache/huggingface'),local_files_only=True)
    tokenizer=AutoTokenizer.from_pretrained(path,local_files_only=True,use_fast=False)
    torch.set_num_threads(c['encoder_threads']);torch.manual_seed(c['seed'])
    cache=out/'encoder_cache';cache.mkdir(exist_ok=True)
    token_stats={};feature_sets={};model=None
    for variant in ['FULL','MASKED']:
        token_lists=[tokenizer.encode(r['texts'][variant],add_special_tokens=False,truncation=False,verbose=False) for r in rows]
        assert all(token_lists)
        token_stats[variant]={s:{**summary([len(t) for r,t in zip(rows,token_lists) if r['period']==s]),
            'fraction_over_510':float(np.mean([len(t)>510 for r,t in zip(rows,token_lists) if r['period']==s])),
            'total_chunks':sum(math.ceil(len(t)/510) for r,t in zip(rows,token_lists) if r['period']==s)} for s in ['train','validation']}
        identity={'model':lock,'pooling':'mean content tokens, then length-weighted chunk mean; 510 non-overlapping content tokens; excludes special and padding tokens',
            'case_ids':[r['case_id'] for r in rows], 'text_hashes':[r['text_hashes'][variant] for r in rows]}
        meta=cache/f'{variant}.json';npfile=cache/f'{variant}.npy'
        if meta.exists() and npfile.exists() and read(meta)==identity:
            feature_sets[variant]=np.load(npfile);print(f'{variant}: reused frozen feature cache',flush=True);continue
        if model is None:
            model=AutoModel.from_pretrained(path,local_files_only=True).eval()
            for p in model.parameters():p.requires_grad_(False)
        sums=np.zeros((len(rows),model.config.hidden_size),dtype=np.float64);weights=np.zeros(len(rows),dtype=np.int64)
        chunks=[(i,t[j:j+510]) for i,t in enumerate(token_lists) for j in range(0,len(t),510)]
        start=time.perf_counter();bs=c['encoder_batch_size']
        with torch.inference_mode():
            for j in range(0,len(chunks),bs):
                batch=chunks[j:j+bs]
                enc=[tokenizer.prepare_for_model(t,add_special_tokens=True,return_special_tokens_mask=True) for _,t in batch]
                padded=tokenizer.pad(enc,padding=True,return_tensors='pt')
                assert padded['input_ids'].shape[1]<=512
                content=padded['attention_mask'].bool() & ~padded.pop('special_tokens_mask').bool()
                h=model(**padded).last_hidden_state
                chunk_sums=(h*content.unsqueeze(-1)).sum(dim=1).numpy();lengths=content.sum(dim=1).numpy()
                for z,(i,_) in enumerate(batch):sums[i]+=chunk_sums[z];weights[i]+=lengths[z]
                if j%40==0 or j+bs>=len(chunks):print(f'{variant}: {min(j+bs,len(chunks))}/{len(chunks)} chunks; {time.perf_counter()-start:.0f}s',flush=True)
        assert np.array_equal(weights,[len(t) for t in token_lists])
        features=(sums/weights[:,None]).astype(np.float32);assert np.isfinite(features).all()
        np.save(npfile,features);dump(meta,identity);feature_sets[variant]=features
    dump(out/'token_length_statistics.json',token_stats)
    return feature_sets,lock

def main():
    p=argparse.ArgumentParser();p.add_argument('--run-name');p.add_argument('--skip-encoder',action='store_true');p.add_argument('--reproduce',action='store_true');args=p.parse_args()
    c=read(HERE/'config.json')
    if args.run_name:c['run_name']=args.run_name
    out=output(c);c=read(out/'run_config.json');assert c['test_evaluation_enabled'] is False
    previous=read(out/'metrics.json') if (out/'metrics.json').exists() else None
    if previous and not args.reproduce:raise SystemExit('Results exist. Use --reproduce to verify identical scores, or prepare a NEW run.')
    provenance=read(out/'data_provenance.json')
    assert sha(out/'dataset_development.jsonl')==provenance['data_sha256']
    assert sha(HERE/'preprocessing.py')==provenance['preprocessing_file_sha256'],'Reprepare under a new run name after changing masks.'
    assert sha(ROOT/c['annotations'])==provenance['annotation_file_sha256'],'Annotations changed: prepare a new run.'
    assert (out/'MASKING_AUDIT_REVIEW.md').exists(),'Complete and record pre-model audit first.'
    rows=records(out/'dataset_development.jsonl');validate_development(rows)
    train=np.array([r['period']=='train' for r in rows]);val=~train;y=np.array([r['label'] for r in rows]);valrows=[r for r in rows if r['period']=='validation']
    assert set(y[train])==set(y[val])=={0,1}
    models=out/'models';models.mkdir(exist_ok=True)
    results=[];predictions=[];importance={};timings={};started=time.perf_counter()
    dummy=DummyClassifier(strategy='most_frequent').fit(np.zeros((train.sum(),1)),y[train]);yp=dummy.predict(np.zeros((val.sum(),1)))
    results.append({'model':'Majority','variant':'FULL','C':None,**metrics(y[val],yp)})
    for r,pred in zip(valrows,yp):predictions.append({'case_id':r['case_id'],'model':'Majority','variant':'FULL','C':None,'true_label':r['label'],'predicted_label':int(pred),'score':None})
    def fit_grid(name,variant,Xtr,Xva,make_estimator):
        begin=time.perf_counter()
        for C in c['C_grid']:
            estimator=make_estimator(C);estimator.fit(Xtr,y[train]);pred=estimator.predict(Xva);score=estimator.decision_function(Xva)
            results.append({'model':name,'variant':variant,'C':C,**metrics(y[val],pred)})
            for r,pr,sc in zip(valrows,pred,score):predictions.append({'case_id':r['case_id'],'model':name,'variant':variant,'C':C,'true_label':r['label'],'predicted_label':int(pr),'score':float(sc)})
            joblib.dump(estimator,models/f'{name}_{variant}_C{C:g}.joblib')
            if C==c['controlled_C'] and name=='TFIDF_LR':
                names=estimator[0].get_feature_names_out();coef=estimator[-1].coef_[0];order=np.argsort(coef)
                importance[variant]={'toward_affirmed':[{'term':str(names[i]),'weight':float(coef[i])} for i in order[:20]],'toward_reversed':[{'term':str(names[i]),'weight':float(coef[i])} for i in order[-20:][::-1]]}
        timings[f'{name}_{variant}']=time.perf_counter()-begin
        print(f'Finished {name} {variant}',flush=True)
    for name in ['TFIDF_LR','TFIDF_SVM']:
        variants=['FULL','MASKED']+([f'RANDOM_{s}' for s in c['random_seeds']] if name=='TFIDF_LR' else [])
        for variant in variants:
            X=[r['texts'][variant] for r in rows]
            def factory(C):
                clf=LogisticRegression(C=C,class_weight='balanced',solver='liblinear',max_iter=10000,random_state=c['seed']) if name=='TFIDF_LR' else LinearSVC(C=C,class_weight='balanced',max_iter=20000,random_state=c['seed'],dual='auto')
                return make_pipeline(TfidfVectorizer(ngram_range=(1,2),min_df=2,max_features=30000),clf)
            fit_grid(name,variant,[x for x,t in zip(X,train) if t],[x for x,t in zip(X,val) if t],factory)
    lock=None
    if not args.skip_encoder:
        start=time.perf_counter();features,lock=encoder_features(rows,c,out);timings['encoder_seconds']=time.perf_counter()-start
        for variant,X in features.items():
            fit_grid('LEGAL_BERT_LR',variant,X[train],X[val],lambda C:make_pipeline(StandardScaler(),LogisticRegression(C=C,class_weight='balanced',solver='liblinear',max_iter=10000,random_state=c['seed'])))
    controlled=[r for r in results if r['C'] in [None,c['controlled_C']]]
    selected=[]
    for name,variant in sorted({(r['model'],r['variant']) for r in results}):
        choices=[r for r in results if r['model']==name and r['variant']==variant]
        selected.append(sorted(choices,key=lambda r:(-r['balanced_accuracy'],-r['macro_f1'],r['C'] or 0))[0])
    random_control={}
    for metric in ['accuracy','balanced_accuracy','macro_f1']:
        values=[r[metric] for r in controlled if r['model']=='TFIDF_LR' and r['variant'].startswith('RANDOM_')]
        random_control[metric]={'mean':float(np.mean(values)),'sd_across_seeds':float(np.std(values,ddof=1)),'values':values}
    metric_output={'evaluation':'validation only; provisional LLM draft labels; C selection uses this same validation set','class_order':[0,1],'controlled_C':c['controlled_C'],'controlled':controlled,'selected_on_validation':selected,'grid':results,'random_control_fixed_C':random_control}
    if previous:assert previous==metric_output,'Reproduction changed scores: preserve prior metrics and investigate under a NEW run name.'
    dump(out/'metrics.json',metric_output)
    jsonl(out/'validation_predictions.jsonl',predictions);dump(out/'tfidf_features.json',importance)
    dump(out/'execution.json',{'seed':c['seed'],'python':platform.python_version(),'packages':{k:importlib.metadata.version(k) for k in ['numpy','scipy','scikit-learn','torch','transformers','huggingface-hub','nbformat','nbclient']},'encoder_lock':lock,'timings_seconds':timings,'total_seconds':time.perf_counter()-started,'dataset_sha256':sha(out/'dataset_development.jsonl'),'script_sha256':{k:sha(HERE/k) for k in ['train.py','prepare.py','preprocessing.py']},'validation_ids':[r['case_id'] for r in valrows],'test_evaluated':False})
    print(json.dumps({'controlled':controlled,'random_control':random_control},indent=2))
if __name__=='__main__':main()
