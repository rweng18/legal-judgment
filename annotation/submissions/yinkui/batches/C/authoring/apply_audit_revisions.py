"""Explicit source-read self-audit corrections; retain immutable v1 drafts.

These are manual semantic decisions, not automated classification or human review.
Duplicate checks used original opinions only, without reading peer annotations.
"""
import copy,json
from datetime import datetime,timezone
from support import OUT,ROOT,SOURCE,Case
from common import read_records,validate,dump,write_jsonl

duplicates={
 'NY-6207931':('NY-4304286','Wintermute; same December 31, 2015 decision, May 9, 2014 judgment, parties, facts and evidentiary new-trial reasoning.'),
 'NY-6111859':('NY-4306330','Seferagic; same March 21, 2014 decision, November 30, 2012 order, parties, wet-floor facts and notice reasoning.'),
 'NY-6235219':('NY-4387315','Lingenfelter; same April 28, 2017 decision, May 9, 2016 order, parties, snowplowing contract and Espinal reasoning.'),
}
revised=[]
for p in sorted((OUT/'chunks').glob('C_[0-9][0-9][0-9].json')):
 rows=read_records(p);original=copy.deepcopy(rows);notes={}
 existing=OUT/'drafts'/f'{p.stem}.draft-v2.json'
 if existing.exists():
  assert rows==read_records(existing),'Selected records must match preserved revision'
  first={r['case_id']:r for r in read_records(OUT/'drafts'/f'{p.stem}.draft-v1.json')}
  for r in rows:
   if r!=first[r['case_id']]:
    assert r['run']['supersedes']==f'drafts/{p.stem}.draft-v1.json#{r["case_id"]}'
    revised.append({'case_id':r['case_id'],'reason':r['run']['review_note'].split('LLM self-audit revision v2: ',1)[1],'selected_chunk':p.relative_to(OUT).as_posix(),'supersedes':r['run']['supersedes'],'revision_draft':existing.relative_to(OUT).as_posix()})
  continue
 for r in rows:
  cid=r['case_id'];note=None
  if cid in duplicates:
   canonical,description=duplicates[cid]
   # Codebook requires uncertain subject scope to remain review, even if duplicate.
   r['eligibility']['binary_task']='review' if r['eligibility']['scope']=='uncertain' else 'exclude'
   r['eligibility']['reasons'].append('duplicate_or_related')
   r['outcome']['binary_label']=None
   r['quality']['needs_review']=r['eligibility']['binary_task']=='review'
   r['quality']['flags'].append('possible_duplicate_family')
   note=f'Duplicate source of earlier Batch B {canonical}: {description} Do not add this C record as a separate observation. Provisionally retain the earlier-batch ID, subject to team scope adjudication; preserve both annotations and group the family before splitting. This does not approve the B label or resolve any remaining scope ambiguity. An uncertain-scope record remains review under the current codebook even when duplicate status is established.'
  elif cid=='NY-4626915':
   r['eligibility'].update(scope='uncertain',binary_task='review',reasons=['property_unclear'],property_status='unclear',property_basis='insufficient')
   r['outcome']['binary_label']=None
   r['facts']['premises_type']='unclear'
   r['quality']['needs_review']=True
   r['quality']['notes']=''
   note='Plaintiff could not identify the location or cause of the fall outside the premises; witnesses assumed the location without seeing the fall. Exterior-step allegations do not establish that the actual fall occurred on private property. Review the property boundary; restaurant subtype cannot be inferred from defendant name alone. Current appeal remains affirmed.'
  elif cid=='NY-4389907':
   r['quality']['flags'].append('possible_duplicate_family')
   note='Duplicate-source partner NY-6235554 is the same Peña opinion (date, parties, order and substantive text). Retain this ID provisionally; partner excluded from binary sample. Team must confirm one canonical record and group this family.'
  elif cid=='NY-5944468':
   c=Case(cid.removeprefix('NY-'),p.stem);c.r=r
   eid=c.e(3,'Both of the Magees testified','Ramirez testified at his deposition that he never observed any shoes on the subject staircase.',status='testimony_or_record')
   c.material('party_testimony','Tenant Magees and owner Ramirez depositions concerning shoes near/on stairs.',[eid])
   note='Added expressly discussed owner and tenant depositions to the evidence inventory; no eligibility or outcome change.'
  elif cid=='NY-3150507':
   e=next(e for e in r['evidence'] if e['evidence_id']=='E006')
   assert e['quote'].endswith(' and water had ac')
   e['quote']=e['quote'].removesuffix(' and water had ac')
   note='Shortened E006 to the complete word leaked at the supplied passage boundary; retained exact source quotation and substantive meaning.'
  if note:
   r['run']['supersedes']=f'drafts/{p.stem}.draft-v1.json#{cid}'
   r['run']['annotated_at']=datetime.now(timezone.utc).isoformat(timespec='seconds')
   r['run']['review_note']+=' LLM self-audit revision v2: '+note
   r['quality']['notes']=(r['quality']['notes']+' '+note).strip()
   notes[cid]=note
 if not notes:continue
 assert original==read_records(OUT/'drafts'/f'{p.stem}.draft-v1.json'),'Refuse to overwrite prior revisions'
 new=OUT/'drafts'/f'{p.stem}.draft-v2.json'
 assert not new.exists(),'Preserve existing revisions'
 expected=json.loads((ROOT/f'batches/C/chunks/{p.stem}.expected.json').read_text(encoding='utf8'))['case_ids']
 report=validate(rows,SOURCE,expected);assert report['passed'],report['errors']
 dump(new,rows);dump(p,rows);dump(p.with_name(p.stem+'.validation.json'),report)
 revised.extend({'case_id':cid,'reason':note,'selected_chunk':p.relative_to(OUT).as_posix(),'supersedes':f'drafts/{p.stem}.draft-v1.json#{cid}','revision_draft':new.relative_to(OUT).as_posix()} for cid,note in notes.items())
rows=[r for p in sorted((OUT/'chunks').glob('C_[0-9][0-9][0-9].json')) for r in read_records(p)]
expected=json.loads((ROOT/'batches/C/manifest.json').read_text(encoding='utf8'))['case_ids']
report=validate(rows,SOURCE,expected);assert report['passed'],report['errors']
write_jsonl(OUT/'checkpoint.jsonl',rows);dump(OUT/'checkpoint.validation.json',report)
dump(OUT/'revisions.json',{'type':'LLM self-audit; no human review','date_local':'2026-11-03','changes':revised,'eligibility_or_binary_labels_changed':True})
print(f'{len(revised)} documented revisions; all v1 drafts preserved; 168 records valid.')
