"""Freeze paired interventions before fitting; no labels enter text transformations."""
from collections import Counter
from common import *

def main():
    out=HERE/'inputs'
    if (out/'protocol.json').exists():raise FileExistsError('Preserve frozen protocol; use a new version.')
    release_path='experiments/provisional_abc/inputs/abc_provisional_v1/'
    release=json.loads(blob(release_path+'release.json'))
    for name in ['release.json',*release['sha256']]:
        data=blob(release_path+name)
        if name!='release.json':assert digest(data)==release['sha256'][name]
        path=out/'release'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    rows=load_rows();assert len(rows)==321 and Counter(r['period'] for r in rows)=={'train':279,'validation':42}
    variants=[];logs=[];empty=[]
    for row in rows:
        full=row['texts']['FULL'];masked=row['texts']['MASKED'];cid=row['case_id']
        texts=dict(row['texts']);loss=len(full.split())-len(masked.split());assert loss>=0
        entry={'case_id':cid,'period':row['period'],'variants':{}}
        for seed in SEEDS:
            text,log=random_remove(full,loss,seed,cid)
            texts[f'RANDOM_{seed}']=text;entry['variants'][f'RANDOM_{seed}']=log
            assert len(text.split())==len(masked.split())
        for boundaries,rules,name in [('old','old','OLD'),('new','old','BOUNDARY_ONLY'),('old','new','RULE_ONLY'),('new','new','COMBINED')]:
            text,removed=component_mask(full,boundaries,rules)
            if not text.strip():empty.append({'case_id':cid,'variant':name})
            texts[name]=text;entry['variants'][name]={'boundaries':boundaries,'rules':rules,'removed':removed,'removed_words':len(full.split())-len(text.split())}
            for seed in SEEDS:
                budget=len(full.split())-len(text.split())
                if budget==len(full.split()):
                    control='';log={'removed_words':budget,'all_words_removed':True}
                else:control,log=random_remove(full,budget,seed,cid)
                texts[f'{name}_RANDOM_{seed}']=control;entry['variants'][f'{name}_RANDOM_{seed}']=log
                assert len(control.split())==len(text.split())
        if row['batch'] in 'BC':assert texts['COMBINED']==masked,(cid,'new policy does not reproduce B/C text')
        variants.append({'case_id':cid,'batch':row['batch'],'period':row['period'],'texts':texts})
        logs.append(entry)
    # Verify the old policy against the original B handoff; no guessed historical baseline.
    baseline=records(ROOT/'annotation/submissions/hyunsang/preprocessing/batch_b/provisional_v1/inputs/B_development_baseline_PROVISIONAL.jsonl')
    assert all(component_mask(r['texts']['FULL'],'old','old')[0]==r['texts']['MASKED'] for r in baseline)
    jsonl(out/'variants.jsonl',variants);jsonl(out/'removal_logs.jsonl',logs)
    selection=read(REFERENCE/'selection.json')
    assert all(selection[m]['selected_C']==c for m,c in SELECTED_C.items())
    protocol={'version':'feedback_controls_v1','date_local':'2026-11-19','upstream_commit':BASE,
      'scope':'Provisional development only; actual human review reported complete by user, decision records awaited. No source status promotion; no final test.',
      'training_cases':279,'validation_cases':42,'training_classes':dict(Counter(r['label'] for r in rows if r['period']=='train')),'validation_classes':dict(Counter(r['label'] for r in rows if r['period']=='validation')),
      'primary':'LR and frozen LEGAL-BERT: FULL/MASKED plus five word-matched random removals on identical cases; independently refit per variant at the previously selected fixed C.',
      'C_by_model':SELECTED_C,'C_sensitivity':1.0,'seeds':SEEDS,
      'additional_diagnostic':'Keep FULL-trained scaler/vectorizer and classifier fitted parameters fixed; predict MASKED/random variants without refitting. This is distribution-shift diagnostic, not primary performance.',
      'component_ablation':'LR fixed C=10; old/new sentence boundaries x old/new matcher; all four combinations; five matched controls per combination. FULL cleaning, case IDs, labels and splits held fixed. Uniform reconstructed policies across ABC, unlike upstream mixed mask.',
      'length_ablation':'Frozen LEGAL-BERT first content chunk versus all chunks on FULL and MASKED at C=.1 and C=1; identical cases. No new tuning.',
      'learning_curve':'Optional completed if feasible: LR and frozen BERT MASKED, nested family samples at 25/50/75/100 percent using seeds 11/23/37; unchanged validation and fixed selected C.',
      'inference':'5000 paired validation-family bootstrap resamples; descriptive only. Seed SD measures removal variability, not sampling uncertainty.',
      'empty_component_texts':empty,'old_policy_matches_B_original':len(baseline),
      'no_validation_optimized_rule_changes':True,'prior_validation_exposure_disclosed':True,
      'sha256':{n:digest((out/n).read_bytes()) for n in ['variants.jsonl','removal_logs.jsonl']},
      'code_sha256':{p.name:digest(p.read_bytes()) for p in [HERE/'common.py',Path(__file__)]}}
    write(out/'protocol.json',protocol)
    print(json.dumps({'cases':len(rows),'variants':len(variants[0]['texts']),'empty_component_texts':empty},indent=2))

if __name__=='__main__':main()
