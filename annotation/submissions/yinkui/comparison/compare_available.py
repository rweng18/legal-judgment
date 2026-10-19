"""Two-submission calibration audit; preserves original records and validation errors.

Run from any working directory. This script never repairs peer annotations or
calculates classifier accuracy against a model-generated 'gold' label.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from common import read_records,validate,dump

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def field(row,path):
    value=row
    for part in path.split('.'):value=value[part]
    return value
def stable(value):return json.dumps(value,sort_keys=True,ensure_ascii=False)
def pair_stats(a,b):
    n=len(a);ca=Counter(map(stable,a));cb=Counter(map(stable,b))
    matched=sum(x==y for x,y in zip(a,b));po=matched/n if n else None
    pe=sum(ca[k]*cb[k] for k in set(ca)|set(cb))/(n*n) if n else None
    labels=sorted(set(ca)|set(cb))
    return {'n':n,'agree':matched,'agreement':po,'cohen_kappa':(po-pe)/(1-pe) if n and pe<1 else None,
      'labels':[json.loads(k) for k in labels],
      'counts':{'yinkui':{k:ca[k] for k in labels},'becca':{k:cb[k] for k in labels}},
      'cross_tab_rows_yinkui_columns_becca':[[sum(stable(x)==i and stable(y)==j for x,y in zip(a,b)) for j in labels] for i in labels]}

expected=json.loads((ROOT/'calibration/manifest.json').read_text(encoding='utf8'))['case_ids']
sources={r['case_id']:r for r in read_records(ROOT/'source/cases.jsonl')}
ap=ROOT/'submissions/yinkui/calibration.jsonl'
bps=[ROOT/f'submissions/becca/CAL_{i:03d}.json' for i in (1,2,3)]
ar=read_records(ap);br=[r for p in bps for r in read_records(p)]
a={r['case_id']:r for r in ar};b={r['case_id']:r for r in br}
assert len(ar)==len(br)==12 and set(a)==set(b)==set(expected)
va=validate(ar,sources,expected);vb=validate(br,sources,expected)
dump(HERE/'yinkui.validation.json',va);dump(HERE/'becca.validation.json',vb)
assert va['passed']
record_valid={cid:validate([b[cid]],sources,[cid])['passed'] for cid in expected}
clean=[cid for cid in expected if record_valid[cid]]
common=[cid for cid in clean if a[cid]['eligibility']['binary_task']==b[cid]['eligibility']['binary_task']=='include']
fields=['eligibility.scope','eligibility.property_status','eligibility.binary_task','outcome.appellate_disposition','outcome.binary_label']
stats={f:pair_stats([field(a[c],f) for c in expected],[field(b[c],f) for c in expected]) for f in fields}
core=[];case_rows=[]
for c in expected:
    diff={f:{'yinkui':field(a[c],f),'becca':field(b[c],f)} for f in fields if field(a[c],f)!=field(b[c],f)}
    if diff:core.append({'case_id':c,'differences':diff})
    case_rows.append({'case_id':c,'case_name':sources[c].get('case_name'),
      'yinkui':{f:field(a[c],f) for f in fields},'becca':{f:field(b[c],f) for f in fields},'becca_record_valid':record_valid[c]})
extra=[];issue_a=[];issue_b=[]
categorical=['eligibility.property_basis','eligibility.fall_type','eligibility.merits','outcome.multiple_orders','outcome.favors',
             'facts.premises_type','facts.location','facts.hazards','facts.injured_role','facts.defendant_roles','facts.accident_date']
for c in expected:
    diffs={}
    for f in categorical:
        av=field(a[c],f);bv=field(b[c],f)
        if isinstance(av,list):av=sorted(av);bv=sorted(bv)
        if av!=bv:diffs[f]={'yinkui':av,'becca':bv}
    for topic in [i['topic'] for i in a[c]['legal_issues']]:
        ai=next(i for i in a[c]['legal_issues'] if i['topic']==topic)
        bi=next(i for i in b[c]['legal_issues'] if i['topic']==topic)
        issue_a.append(ai['discussion']);issue_b.append(bi['discussion'])
        if ai['discussion']!=bi['discussion']:
            diffs['legal_issues.'+topic]={'yinkui':ai,'becca':bi}
    at=sorted(i['type'] for i in a[c]['evidence_discussed']);bt=sorted(i['type'] for i in b[c]['evidence_discussed'])
    if at!=bt:diffs['evidence_discussed.types']={'yinkui':at,'becca':bt}
    ao=[i['appellant_role'] for i in a[c]['outcome']['orders']];bo=[i['appellant_role'] for i in b[c]['outcome']['orders']]
    if ao!=bo:diffs['outcome.order_appellant_roles']={'yinkui':ao,'becca':bo}
    if diffs:extra.append({'case_id':c,'differences':diffs})
freeze=json.loads((ROOT/'submissions/yinkui/independent_freeze.json').read_text(encoding='utf8'))
assert all(sha(ROOT/'submissions/yinkui'/p)==h for p,h in freeze['files'].items())
assert all(sha(ROOT/p)==h for p,h in freeze['inputs'].items()),'Source/codebook changed after independent pass'
ref=subprocess.check_output(['git','-C',str(ROOT.parent),'rev-parse','origin/main'],text=True).strip()
counts={}
for name,rows in [('yinkui',ar),('becca',br)]:
 counts[name]={'binary_task':dict(Counter(r['eligibility']['binary_task'] for r in rows)),
   'appellate_disposition':dict(Counter(r['outcome']['appellate_disposition'] for r in rows)),
   'included_binary_labels':dict(Counter(str(r['outcome']['binary_label']) for r in rows if r['eligibility']['binary_task']=='include'))}
report={'generated_at':datetime.now(timezone.utc).isoformat(),'cases':12,'available_submissions':['yinkui','becca'],
 'missing_submission':'hyunsang','remote_main_commit':ref,'independent_draft_commit':'b94ae3c',
 'input_hashes':{p.relative_to(ROOT).as_posix():sha(p) for p in [ap]+bps+[ROOT/'submissions/becca/independent_calibration_notes.md']},
 'source_and_codebook_match_frozen_inputs':True,'independent_outputs_unchanged':True,
 'validation':{'yinkui':{'passed':va['passed'],'errors':va['errors']},'becca':{'passed':vb['passed'],'errors':vb['errors']}},
 'counts':counts,'raw_core_field_agreement':stats,'core_disagreements':core,'cases_table':case_rows,
 'valid_record_binary_label_agreement':pair_stats([a[c]['outcome']['binary_label'] for c in clean],[b[c]['outcome']['binary_label'] for c in clean]),
 'valid_record_case_ids':clean,'common_included_case_ids':common,
 'common_included_binary_agreement':pair_stats([a[c]['outcome']['binary_label'] for c in common],[b[c]['outcome']['binary_label'] for c in common]),
 'legal_issue_discussion_agreement':pair_stats(issue_a,issue_b),'extra_feature_disagreements':extra,
 'limitations':['Raw statistics retain the invalid Verges binary label; valid-record statistics explicitly omit that entire peer record.',
   'Null is a non-inclusion category in raw binary-label agreement, not a third predictive target.',
   'Both structured submissions are LLM drafts, not independent human gold. Agreement is not classifier accuracy.',
   'Two of three teammate submissions available; no fabricated third submission, accuracy, balanced accuracy, macro F1, or majority-vote gold.',
   'Legal-issue agreement pools 228 correlated case-topic entries and is dominated by not_discussed; it is a descriptive diagnostic only.']}
dump(HERE/'calibration_comparison.json',report)
dump(HERE/'proposed_corrections.json',{'applied':False,'human_review_required':True,'changes':[
 {'source_file':'annotation/submissions/becca/CAL_003.json','case_id':'NY-4795834','field':'outcome.binary_label','original':0,'proposed':None,'reason':'binary_task=review requires null under codebook; preserve affirmed disposition.'}],
 'provenance_requests':['Confirm Becca actual prompt and its version; current files say unspecified_by_team. Do not invent a retroactive version.',
 'Confirm annotator_id convention; files use GPT-6 rather than becca. Preserve originals and retain model identity separately.',
 'Review replacement-character encoding in peer narrative fields before final merge. Evidence quote validation still passed.']})
print(json.dumps({'counts':counts,'agreement':{k:{x:v[x] for x in ('n','agree','agreement','cohen_kappa')} for k,v in stats.items()},'common_included_n':len(common),'extra_difference_cases':len(extra),'peer_validation_errors':vb['errors']},indent=2))

table=['| Case | Yinkui eligibility | Becca LLM eligibility | Outcome (both) | Yinkui label | Becca label |', '|---|---|---|---|---|---|']
for c in expected:
    table.append(f"| {c} | {a[c]['eligibility']['binary_task']} | {b[c]['eligibility']['binary_task']} | {a[c]['outcome']['appellate_disposition']} | {a[c]['outcome']['binary_label']} | {b[c]['outcome']['binary_label']} |")
(HERE/'case_table.md').write_text('\n'.join(table)+'\n',encoding='utf8')
