import argparse,collections,itertools,json,random,re,sys
import numpy as np
from common import ROOT,HERE,read,records,dump,jsonl,sha,textsha,output,split_for
from preprocessing import clean_text,mask_text,random_remove,words,VERSION

def norm(s):return re.sub(r'[^a-z0-9]','',s.lower())
def family_groups(sources,assigned,hints=None):
    parent={k:k for k in sources};edges=[]
    def find(k):
        while parent[k]!=k:parent[k]=parent[parent[k]];k=parent[k]
        return k
    def union(a,b,why,score=None):
        ra,rb=find(a),find(b)
        if ra!=rb:parent[max(ra,rb)]=min(ra,rb)
        edges.append({'a':a,'b':b,'basis':why,'score':score})
    for field in ['case_name','docket_number','text_sha256']:
        seen={}
        for k,r in sources.items():
            v=norm(str(r.get(field) or ''))
            if not v or v in ['none','unknown']:continue
            if v in seen:union(seen[v],k,'same_'+field)
            else:seen[v]=k
    for group in hints or []:
        ids=group['case_ids']
        assert all(k in sources for k in ids),'Family hint refers to an unknown source ID'
        for k in ids[1:]:union(ids[0],k,'explicit_family_hint')
    # Unsupervised duplicate screening only, never reused as predictive features.
    grams={}
    for k in assigned:
        w=re.findall(r'\w+',sources[k]['text'].lower());grams[k]={tuple(w[i:i+5]) for i in range(len(w)-4)}
    candidates=[]
    for a,b in itertools.combinations(sorted(assigned),2):
        inter=len(grams[a]&grams[b]);den=len(grams[a]|grams[b]);sim=inter/den if den else 0
        if sim>=.65:
            candidates.append({'a':a,'b':b,'fivegram_jaccard':sim,'action':'group_conservatively' if sim>=.85 else 'manual_review_pending'})
            if sim>=.85:union(a,b,'near_duplicate_5gram',sim)
    return {k:find(k) for k in sources},edges,candidates

def summary(values):
    return {'n':len(values),'min':float(min(values)),'median':float(np.median(values)),'mean':float(np.mean(values)),'p90':float(np.percentile(values,90)),'max':float(max(values))} if values else {'n':0}

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',default=str(HERE/'config.json'));p.add_argument('--annotations');p.add_argument('--run-name');args=p.parse_args()
    c=read(args.config)
    if args.annotations:c['annotations']=args.annotations
    if args.run_name:c['run_name']=args.run_name
    assert c['test_evaluation_enabled'] is False,'This development runner never evaluates final test data.'
    out=output(c)
    if (out/'dataset_development.jsonl').exists():
        raise SystemExit('Run already exists. Use --run-name with a NEW name to preserve previous datasets and results.')
    out.mkdir(parents=True,exist_ok=True)
    sources={r['case_id']:r for r in records(ROOT/c['source'])};anns=records(ROOT/c['annotations']);expected=read(ROOT/c['expected'])['case_ids'];cal=set(read(ROOT/c['calibration'])['case_ids'])
    # Import existing validator under distinct module name to avoid common.py collision.
    import importlib.util
    spec=importlib.util.spec_from_file_location('annotation_common',ROOT/'annotation/scripts/common.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    report=mod.validate(anns,sources,expected);dump(out/'annotation_validation.json',report)
    assert report['passed'],report['errors']
    hints=read(ROOT/c['family_hints'])['groups']
    families,edges,candidates=family_groups(sources,expected,hints)
    members=collections.defaultdict(list)
    for k,g in families.items():members[g].append(k)
    cross={g for g,ids in members.items() if len({split_for(int(sources[k]['date_filed'][:4]),c) for k in ids})>1}
    for h in hints:
        assert len({families[k] for k in h['case_ids']})==1,'Family hint not represented'
    dump(out/'family_audit.json',{'edges':edges,'near_duplicate_candidates':candidates,'groups':[{'family_id':g,'case_ids':ids,'cross_period':g in cross} for g,ids in members.items() if len(ids)>1],'warning':'Metadata and similarity checks are provisional. Family review remains incomplete; same docket strings may be ambiguous across counties. No model features use this screening.'})
    dataset=[];manifest=[];masklogs=[];seen_hash={}
    for a in sorted(anns,key=lambda r:r['case_id']):
        k=a['case_id'];s=sources[k];year=int(s['date_filed'][:4]);split=split_for(year,c);g=families[k]
        assert 2010<=year<=c['test_end']
        reason=None
        if a['eligibility']['binary_task']!='include':reason=a['eligibility']['binary_task']
        elif g in cross:reason='cross_period_family'
        elif k in cal and split!='train':reason='calibration_not_training_period'
        elif s['text_sha256'] in seen_hash:reason='exact_duplicate'
        if reason is None:seen_hash[s['text_sha256']]=k
        row={'case_id':k,'case_name':s['case_name'],'date_filed':s['date_filed'],'source_url':s['source_url'],'source_text_sha256':s['text_sha256'],'family_id':g,'eligibility':a['eligibility']['binary_task'],'label':a['outcome']['binary_label'],'review_status':a['run']['review_status'],'calibration_exposure':k in cal,'period':split,'modeling_status':reason or ('sealed_test' if split=='test' else 'included')}
        manifest.append(row)
        if reason or split=='test':continue
        assert row['label'] in [0,1]
        full,clog=clean_text(s['text']);masked,removed=mask_text(full)
        assert full and masked,('Empty text requires explicit handling',k)
        budget=len(words(full))-len(words(masked));assert budget==sum(x['words'] for x in removed)
        texts={'FULL':full,'MASKED':masked};random_logs={}
        outcome_words={i for i,w in enumerate(words(full)) if any(x['start']<=w.start()<x['end'] for x in removed)}
        for seed in c['random_seeds']:
            text,rl=random_remove(full,budget,seed,k);texts[f'RANDOM_{seed}']=text
            assert len(words(text))==len(words(masked))
            rl['outcome_words_removed']=len(outcome_words.intersection(rl['removed_word_indices']));random_logs[str(seed)]=rl
        row={**row,'texts':texts,'word_counts':{v:len(words(t)) for v,t in texts.items()},'masked_words_removed':budget,'removed_fraction':budget/len(words(full)),'text_hashes':{v:textsha(t) for v,t in texts.items()}}
        dataset.append(row);masklogs.append({'case_id':k,'period':split,'removed':removed,'cleaning':clog,'random':random_logs})
    jsonl(out/'dataset_development.jsonl',dataset);jsonl(out/'split_manifest.jsonl',manifest);jsonl(out/'masking_log.jsonl',masklogs)
    assert not {r['family_id'] for r in dataset if r['period']=='train'} & {r['family_id'] for r in dataset if r['period']=='validation'}
    assert not any(r['period']=='test' for r in dataset)
    audit=[]
    for split in ['train','validation']:
        for label in [0,1]:
            pool=sorted([r['case_id'] for r in dataset if r['period']==split and r['label']==label])
            rng=random.Random(c['seed']+(0 if split=='train' else 100)+label)
            audit+=rng.sample(pool,min(c['audit_cases_per_class_per_split'],len(pool)))
    dump(out/'mask_audit_sample.json',{'seed':c['seed'],'sampling':'Two per class in training and validation, before fitting models. Assistant semantic audit; human review pending.','case_ids':audit})
    packet=['# Masking audit sample','Source-based assistant review only; not human gold. Training and validation both represented. No test cases.']
    logs={r['case_id']:r for r in masklogs}
    for r in dataset:
        if r['case_id'] not in audit:continue
        packet += [f"\n## {r['case_id']} | {r['period']} | label {r['label']} | {r['case_name']}",'\n### FULL',r['texts']['FULL'],'\n### Removed']
        packet += [f"- [{x['rule']}] {x['text']}" for x in logs[r['case_id']]['removed']]
        packet += ['\n### MASKED',r['texts']['MASKED']]
    (out/'MASKING_AUDIT_PACKET.md').write_text('\n\n'.join(packet),encoding='utf8')
    counts={s:dict(collections.Counter(str(r['label']) for r in manifest if r['period']==s and r['modeling_status'] in ['included','sealed_test'])) for s in ['train','validation','test']}
    stats={'candidate_cases':len(anns),'reviewer_eligibility':dict(collections.Counter(a['eligibility']['binary_task'] for a in anns)),'modeling_status':dict(collections.Counter(r['modeling_status'] for r in manifest)),'split_class_counts':counts,'word_lengths':{s:{v:summary([r['word_counts'][v] for r in dataset if r['period']==s]) for v in ['FULL','MASKED']} for s in ['train','validation']},'removed_fraction':summary([r['removed_fraction']*100 for r in dataset]),'test_text_processed_or_evaluated':False,'human_gold':False}
    dump(out/'dataset_summary.json',stats);dump(out/'run_config.json',c)
    dump(out/'data_provenance.json',{'source_file_sha256':sha(ROOT/c['source']),'annotation_file_sha256':sha(ROOT/c['annotations']),'manifest_file_sha256':sha(ROOT/c['expected']),'preprocessing_file_sha256':sha(HERE/'preprocessing.py'),'mask_version':VERSION,'data_sha256':sha(out/'dataset_development.jsonl'),'label_source':c['annotations'],'human_review':'pending; this is a provisional engineering run','test_policy':'2023–2024 metadata/counts only; no text in modeling dataset, no predictions or metrics. Raw source used only in unsupervised duplicate/family screening.','annotation_fields_as_features':False})
    print(json.dumps(stats,indent=2))
if __name__=='__main__':main()
