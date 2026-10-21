"""Serialize manually authored semantic annotations; never infer labels from text.
Evidence selectors are authored after reading each complete chunk.
"""
import json,sys,hashlib,subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts'))
from common import ISSUES,validate,dump,write_jsonl
BASE=Path(__file__).resolve().parent
SOURCES={r['case_id']:r for r in map(json.loads,(ROOT/'source/cases.jsonl').read_text().splitlines())}
def record(cid,chunk,elig,out,facts,quotes,issues,sections,materials=(),cues=(),notes='',flags=(),orders=None):
 s=SOURCES[cid]; evidence=[]
 for i,(pn,status,quote) in enumerate(quotes,1):
  pid=f'P{pn:03d}';p=next(p for p in s['passages'] if p['passage_id']==pid)
  assert p['text'].count(quote)==1,(cid,pid,quote)
  evidence.append(dict(evidence_id=f'E{i:03d}',passage_id=pid,quote=quote,statement_status=status))
 def refs(nums):return [f'E{x:03d}' for x in nums]
 scope,task,reasons,prop,basis,fall,merits,pe,ie,se=elig
 disp,favors,appellant,trial,de=out
 premise,location,hazards,role,defroles,date,summary,fe=facts
 orderlist=orders or [(appellant,trial,disp,de)]
 r=dict(schema_version='1.0.0',prompt_version='1.0.0',case_id=cid,text_sha256=s['text_sha256'],input_chunk_id=chunk,
 run=dict(annotator_id='hyunsang',model_name='GPT-6',model_version=None,annotated_at=datetime.now(ZoneInfo('America/New_York')).isoformat(),review_status='llm_draft',human_reviewer_id=None,review_note='Full supplied chunk read by assistant; no independent human review. Snapshot/version not observable.',supersedes=None),
 eligibility=dict(scope=scope,binary_task=task,reasons=reasons,property_status=prop,property_basis=basis,fall_type=fall,merits=merits,property_evidence=refs(pe),incident_evidence=refs(ie),scope_evidence=refs(se)),
 outcome=dict(appellate_disposition=disp,binary_label=({'affirmed':0,'reversed':1,'vacated':1}.get(disp) if task=='include' else None),multiple_orders=len(orderlist)>1,favors=favors,disposition_evidence=refs(de),orders=[dict(description=tr,appellant_role=ap,trial_court_action=tr,appellate_disposition=di,evidence_ids=refs(ev)) for ap,tr,di,ev in orderlist]),
 facts=dict(premises_type=premise,location=location,hazards=hazards,injured_role=role,defendant_roles=defroles,accident_date=date,factual_summary=summary,evidence_ids=refs(fe)),
 legal_issues=[dict(topic=t,discussion=issues[t][0],finding=issues[t][1],evidence_ids=refs(issues[t][2])) if t in issues else dict(topic=t,discussion='not_discussed',finding='',evidence_ids=[]) for t in ISSUES],
 evidence_discussed=[dict(type=t,description=d,evidence_ids=refs(es)) for t,d,es in materials],
 text_sections=[dict(passage_id=f'P{i:03d}',types=types.split(',')) for i,types in enumerate(sections,1)],
 outcome_cues=[dict(kind=k,evidence_ids=refs(es)) for k,es in cues],quality=dict(needs_review=task=='review',flags=list(flags),notes=notes),evidence=evidence)
 return r

def save(chunk,rows):
 expected=json.loads((ROOT/f'batches/A/chunks/{chunk}.expected.json').read_text())['case_ids']
 assert [r['case_id'] for r in rows]==expected
 draft=BASE/f'drafts/{chunk}.draft-v1.json'; assert not draft.exists()
 dump(draft,rows)
 dump(BASE/f'chunks/{chunk}.json',rows)
 result=validate(rows,SOURCES,expected);dump(BASE/f'chunks/{chunk}.validation.json',result)
 print(chunk,'records',len(rows),'passed',result['passed'],'errors',result['errors'])
 assert result['passed']
 update()
def update():
 paths=sorted((BASE/'chunks').glob('A_???.json'))
 rows=[r for p in paths for r in json.loads(p.read_text())]
 expected=json.loads((ROOT/'batches/A/manifest.json').read_text())['case_ids']
 write_jsonl(BASE/'checkpoint.jsonl',rows)
 v=validate(rows,SOURCES,expected,partial=True);dump(BASE/'checkpoint.validation.json',v)
 dump(BASE/'progress.json',dict(expected_cases=len(expected),completed_cases=len(rows),completed_chunks=[p.stem for p in paths],pending_ids=[x for x in expected if x not in {r['case_id'] for r in rows}],validation_passed=v['passed'],human_reviewed_cases=0,peer_outputs_read=False,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()))
 prompt=(ROOT/'prompts/START_HERE.md').read_text().replace('[REVIEWER_ID]','hyunsang')+'\n'+(ROOT/'prompts/ANNOTATE_CHUNK.md').read_text()
 for p in paths:
  target=BASE/f'prompts_used/{p.stem}.md'
  if not target.exists():target.write_text(prompt.replace('[CHUNK_ID / INPUT_FILENAME]',f'batches/A/chunks/{p.stem}.md').replace('[CHUNK_ID]',p.stem)+'\nSession scope: A_001 through A_034 in order; independent labels; no peer submissions; no repeated calibration. Human review pending. Model snapshot unobservable. Exact additional user instruction is preserved in session_scope.md.\n')
def compact(cid,chunk,elig,out,facts,passages,issues,sections,materials=(),cues=(),notes='',flags=(),orders=None):
 """Explicit passage evidence choices, based on semantic full reading, serialized verbatim."""
 s=SOURCES[cid];qs=[(n,status,next(p['text'] for p in s['passages'] if p['passage_id']==f'P{n:03d}')) for n,status in passages]
 return record(cid,chunk,elig,out,facts,qs,issues,sections,materials,cues,notes,flags,orders)
def q(cid,chunk,*,prop,basis,fall,disp,favor,trial,facts,sections,issues,material=(),decision=1,task='include',reasons=(),notes='',flags=(),merits='substantive',app='plaintiff',orders=None):
 # All classification inputs below are authored explicitly, never extracted or predicted by this helper.
 p=SOURCES[cid]['passages']; ids=list(range(1,len(p)+1))
 passages=[(i,'current_disposition' if i==decision else 'court_finding') for i in ids]
 scope='uncertain' if task=='review' else ('out_of_scope' if merits!='substantive' or 'public_property' in reasons or 'outside_slip_trip_scope' in reasons or 'no_person_fall' in reasons else 'in_scope')
 return compact(cid,chunk,(scope,task,list(reasons),prop,basis,fall,merits,ids,ids,ids),(disp,favor,app,trial,[decision]),(*facts,ids),passages,issues,sections,material,[('current_disposition',[decision])],notes,flags,orders)
