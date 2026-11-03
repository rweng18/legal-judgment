"""Apply explicit source-read audit corrections, preserving all initial drafts.

No automated relabeling. These eight selections were made after rereading the
relevant frozen source opinions. This is an LLM self-audit, not human review.
"""
import copy,json
from datetime import datetime,timezone
from support import OUT,ROOT,SOURCE
from common import read_records,validate,dump,write_jsonl

changes={
 'NY-5937355':('facts','injured_role','other','Rink participant supported; paying customer status not explicitly stated.'),
 'NY-6473777':('facts','premises_type','unclear','Complex of buildings and employee break room stated; housing-related entity names do not establish residential use of incident building.'),
 'NY-2800524':('facts','injured_role','other','Working with coworkers stated, but independent-contractor relationship not established.'),
 'NY-4851628':('facts','premises_type','unclear','Building use not stated; housing-development entity name alone insufficient for residential subtype.'),
 'NY-4623671':('facts','defendant_roles',['owner'],'Owned and maintained supported; distinct management role not explicitly established.'),
 'NY-9483767':('facts','premises_type','unclear','Car-service sublease supported, but exact building use not expressly office.'),
}
revised=[]
for p in sorted((OUT/'chunks').glob('B_[0-9][0-9][0-9].json')):
 rows=read_records(p); original=copy.deepcopy(rows); notes={}
 for r in rows:
  cid=r['case_id']; note=None
  if cid in changes:
   parent,field,value,note=changes[cid]
   r[parent][field]=value
  elif cid=='NY-6207337':
   r['quality']['flags'].append('possible_duplicate_family')
   note='Duplicate-source partner NY-4304440 has same Alvarado decision, date, lower order and substantive text. This record provisionally retained; partner excluded from binary sample. Team must confirm canonical ID and group across all rounds.'
  elif cid=='NY-3177536':
   item=next(e for e in r['evidence_discussed'] if 'Branch manager' in e['description'])
   assert item['type']=='party_testimony'
   item['type']='witness_testimony'
   note='Corporate branch manager is a witness, not an individually named party in supplied caption.'
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
 expected=json.loads((ROOT/f'batches/B/chunks/{p.stem}.expected.json').read_text(encoding='utf8'))['case_ids']
 report=validate(rows,SOURCE,expected);assert report['passed'],report['errors']
 dump(new,rows);dump(p,rows);dump(p.with_name(p.stem+'.validation.json'),report)
 revised.extend({'case_id':cid,'reason':note,'selected_chunk':str(p.relative_to(OUT)).replace('\\','/'),'supersedes':f'drafts/{p.stem}.draft-v1.json#{cid}','revision_draft':str(new.relative_to(OUT)).replace('\\','/')} for cid,note in notes.items())
rows=[r for p in sorted((OUT/'chunks').glob('B_[0-9][0-9][0-9].json')) for r in read_records(p)]
expected=json.loads((ROOT/'batches/B/manifest.json').read_text(encoding='utf8'))['case_ids']
report=validate(rows,SOURCE,expected);assert report['passed'],report['errors']
write_jsonl(OUT/'checkpoint.jsonl',rows);dump(OUT/'checkpoint.validation.json',report)
dump(OUT/'revisions.json',{'type':'LLM self-audit; no human review','date_local':'2026-11-03','changes':revised,'eligibility_or_binary_labels_changed':False})
print(f'{len(revised)} documented revisions; all v1 drafts preserved; 169 records valid.')
