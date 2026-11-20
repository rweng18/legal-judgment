"""Read-only contract checks for complete saved development and final experiments."""
from collections import defaultdict
from common import *
import numpy as np
from modeling import scores

def main():
    rows=load_rows();variants=records(HERE/'inputs/variants.jsonl');quality=records(HERE/'inputs/quality_v1/variants.jsonl')
    budgets=0
    for raw,q in zip(variants,quality):
        assert raw['case_id']==q['case_id']
        for name,text in raw['texts'].items():
            if 'RANDOM_' in name:
                target='MASKED' if name.startswith('RANDOM_') else name.split('_RANDOM_')[0]
                assert len(text.split())==len(raw['texts'][target].split());budgets+=1
        for seed in SEEDS:
            assert len(q['texts'][f'REVISED_RANDOM_{seed}'].split())==len(q['texts']['REVISED'].split());budgets+=1
    final=HERE/'final';protocol=read(final/'inputs/protocol.json')
    for n,h in protocol['sha256'].items():assert digest((final/'inputs'/n).read_bytes())==h
    manifest=records(final/'inputs/reviewed_manifest.jsonl');tests=records(final/'inputs/test.jsonl');train=records(final/'inputs/train.jsonl')
    assert len(manifest)==370 and len({r['case_id'] for r in manifest})==370
    assert len(train)==278 and len(tests)==50
    periods={}
    for r in manifest:
        year=int(r['date_filed'][:4]);expected='train' if year<=2020 else 'validation' if year<=2022 else 'test'
        assert r['period']==expected and type(r['label']) is int and r['label'] in [0,1]
        assert r['reviewer']=='Yinkui Yu' and r['review_date']=='2026-11-19'
        assert periods.setdefault(r['family_id'],r['period'])==r['period']
    excluded=read(HERE/'review/user_exclusion_decisions_2026-11-19.json')['decisions']
    assert not {r['case_id'] for r in excluded}&{r['case_id'] for r in manifest}
    assert 'NY-6112018' not in {r['case_id'] for r in manifest}
    for r in tests:
        for v,t in r['texts'].items():assert text_hash(t)==r['text_sha256'][v]
        for s in SEEDS:assert len(r['texts'][f'RANDOM_{s}'].split())==len(r['texts']['MASKED'].split());budgets+=1
    devfull={text_hash(r['texts']['FULL']) for r in rows}
    assert not devfull&{text_hash(r['texts']['FULL']) for r in tests}
    counts={}
    for base,mp,pp in [(HERE/'results','metrics.json','predictions.jsonl'),(final/'results','metrics.json','predictions.jsonl')]:
        mm=read(base/mp);preds=records(base/pp);group=defaultdict(list)
        for r in preds:group[r['run_id']].append(r)
        for m in mm:
            rr=group[m['run_id']];y=np.array([r['label'] for r in rr]);yp=np.array([r['prediction'] for r in rr])
            assert len({r['case_id'] for r in rr})==len(rr)
            for k,v in scores(y,yp).items():assert v==m[k],(m['run_id'],k)
        counts[str(base.relative_to(HERE))]={'conditions':len(mm),'prediction_rows':len(preds)}
    for path in [HERE/'results/embeddings',final/'embeddings']:
        idx=read(path/'index.json')
        for n,h in idx['sha256'].items():
            assert digest((path/n).read_bytes())==h
            arr=np.load(path/n,allow_pickle=False);assert arr.shape==(len(idx['case_ids']),768) and np.isfinite(arr).all()
    metrics=read(HERE/'results/metrics.json');preds=records(HERE/'results/predictions.jsonl')
    devmap={r['case_id']:r for r in rows};unchanged={cid for cid,r in devmap.items() if r['period']=='validation' and r['texts']['FULL']==r['texts']['MASKED']}
    for model in ['TFIDF_LR','LEGAL_BERT_LR']:
        keys={m['variant']:m['run_id'] for m in metrics if m['model']==model and m['experiment']=='same_fitted_FULL'}
        a={r['case_id']:r['prediction'] for r in preds if r['run_id']==keys['FULL']};b={r['case_id']:r['prediction'] for r in preds if r['run_id']==keys['MASKED']}
        assert all(a[cid]==b[cid] for cid in unchanged)
    fv=read(final/'results/verification.json')
    assert fv['protocol_sha256']==digest((final/'inputs/protocol.json').read_bytes())
    for n,h in fv['output_sha256'].items():assert digest((final/'results'/n).read_bytes())==h
    write(HERE/'results/complete_verification.json',{'status':'passed','random_word_budgets_checked':budgets,
        'saved_metrics_recomputed':counts,'reviewed_manifest_rows':370,'same_fitted_identical_input_cases_checked':len(unchanged),
        'chronological_and_known_family_separation':True,'no_cross_period_exact_FULL_duplicates':True,
        'frozen_test_protocol_and_output_hashes':True,'encoder_shapes_hashes_finiteness':True,
        'note':'Verification reads saved final predictions; it does not rerun or tune the reserved test.'})
    print('All saved experiment contracts passed:',counts)

if __name__=='__main__':main()
