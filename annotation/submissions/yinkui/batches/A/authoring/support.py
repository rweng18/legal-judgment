"""Serialization and exact-quote helpers for manually authored case readings.

No keyword classification, remote model calls or peer annotations are used.
Callers explicitly select every substantive value after reading all passages.
"""
import json,sys,hashlib
from datetime import datetime,timezone,timedelta
from pathlib import Path
HERE=Path(__file__).resolve().parent
OUT=HERE.parent
ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import ISSUES,read_records,dump,write_jsonl,validate
SOURCE={r['case_id']:r for r in read_records(ROOT/'source/cases.jsonl')}
CALIBRATION=set(json.loads((ROOT/'calibration/manifest.json').read_text(encoding='utf8'))['case_ids'])

class Case:
 def __init__(self,cid,chunk):
  self.s=SOURCE['NY-'+str(cid)]
  self.r={'schema_version':'1.0.0','prompt_version':'1.0.0','case_id':self.s['case_id'],'text_sha256':self.s['text_sha256'],'input_chunk_id':chunk,
   'run':{'annotator_id':'yinkui','model_name':'GPT-6 (Codex; exact variant not exposed)','model_version':None,
     'annotated_at':datetime.now(timezone(timedelta(hours=-4))).isoformat(timespec='seconds'),'review_status':'llm_draft','human_reviewer_id':None,
     'review_note':'Full supplied opinion read; no peer batch-A outputs consulted. Initial codebook 1.0.0; team substantive freeze pending. No human review claimed.','supersedes':None},
   'legal_issues':[{'topic':t,'discussion':'not_discussed','finding':'','evidence_ids':[]} for t in ISSUES],
   'evidence':[],'evidence_discussed':[],'outcome_cues':[]}
  if self.s['case_id'] in CALIBRATION:
   self.r['run']['review_note']+=' Calibration overlap: this case was previously annotated and compared during calibration; this rereading is not a fresh blinded annotation. Retain training-only designation. No peer production outputs read.'
 def e(self,p,start,end=None,status='court_finding'):
  text=self.s['passages'][p-1]['text'];q=start
  if end:
   i=text.index(start);q=text[i:text.index(end,i)+len(end)]
  assert text.count(q)==1,(self.s['case_id'],p,q)
  eid=f'E{len(self.r["evidence"])+1:03d}'
  self.r['evidence'].append({'evidence_id':eid,'passage_id':f'P{p:03d}','quote':q,'statement_status':status})
  return eid
 def eligibility(self,fall,prop,incident,merits,*,basis='owned',decision='include',property_status='private',scope=None,reasons=None,flags=None,note='',merits_type='substantive'):
  self.r['eligibility']={'scope':scope or {'include':'in_scope','exclude':'out_of_scope','review':'uncertain'}[decision],'binary_task':decision,'reasons':reasons or [],'property_status':property_status,'property_basis':basis,'fall_type':fall,'merits':merits_type,'property_evidence':prop,'incident_evidence':incident,'scope_evidence':merits}
  self.r['quality']={'needs_review':decision=='review','flags':flags or [],'notes':note}
 def outcome(self,disp,favors,appellant,trial,refs,description='Current appealed order',orders=None):
  self.r['outcome']={'appellate_disposition':disp,'binary_label':({'affirmed':0,'reversed':1,'vacated':1}.get(disp) if self.r['eligibility']['binary_task']=='include' else None),'multiple_orders':len(orders)>1 if orders else False,'favors':favors,'disposition_evidence':[refs[-1]],'orders':orders or [{'description':description,'appellant_role':appellant,'trial_court_action':trial,'appellate_disposition':disp,'evidence_ids':refs}]}
  self.cue('current_disposition',refs[-1])
 def facts(self,premises,loc,hazards,role,defendants,summary,refs,date=None):
  self.r['facts']={'premises_type':premises,'location':loc,'hazards':hazards.split(),'injured_role':role,'defendant_roles':defendants.split(),'accident_date':date,'factual_summary':summary,'evidence_ids':refs}
 def issue(self,topics,finding,refs,discussion='court_addressed'):
  for t in topics.split():
   i=next(x for x in self.r['legal_issues'] if x['topic']==t);i.update(discussion=discussion,finding=finding,evidence_ids=refs)
 def material(self,kind,description,refs):self.r['evidence_discussed'].append({'type':kind,'description':description,'evidence_ids':refs})
 def cue(self,kind,*refs):self.r['outcome_cues'].append({'kind':kind,'evidence_ids':list(refs)})
 def sections(self,*types):
  assert len(types)==len(self.s['passages'])
  self.r['text_sections']=[{'passage_id':f'P{i:03d}','types':s.split()} for i,s in enumerate(types,1)]

def save(chunk,cases):
 rows=[c.r if isinstance(c,Case) else c for c in cases]
 expected=json.loads((ROOT/f'batches/A/chunks/{chunk}.expected.json').read_text(encoding='utf8'))['case_ids']
 report=validate(rows,SOURCE,expected)
 if not report['passed']:raise ValueError(report['errors'])
 draft=OUT/f'drafts/{chunk}.draft-v1.json'
 if draft.exists():raise FileExistsError(f'Preserve existing draft: {draft}')
 dump(draft,rows);dump(OUT/f'chunks/{chunk}.json',rows);dump(OUT/f'chunks/{chunk}.validation.json',report)
 completed=sorted((OUT/'chunks').glob('A_[0-9][0-9][0-9].json'))
 combined=[r for p in completed for r in read_records(p)]
 allids=json.loads((ROOT/'batches/A/manifest.json').read_text(encoding='utf8'))['case_ids']
 check=validate(combined,SOURCE,allids,partial=True)
 assert check['passed'],check['errors']
 write_jsonl(OUT/'checkpoint.jsonl',combined);dump(OUT/'checkpoint.validation.json',check)
 dump(OUT/'progress.json',{'completed_chunks':[p.stem for p in completed],'completed_cases':len(combined),'expected_cases':169,'pending_case_ids':check['missing_ids'],'all_llm_drafts':True,'cross_comparison_performed':False})
 print(f'{chunk}: {len(rows)} validated; batch progress {len(combined)}/169')
