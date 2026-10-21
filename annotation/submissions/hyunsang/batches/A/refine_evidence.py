"""Mechanical quotation refinement only; preserves every semantic label.
All source opinions were semantically read before their chunk was authored.
Do not use this to generate or infer outcome/eligibility/fact/issue labels.
"""
from assemble import *
import re
log=[];miss=[];preview=[]
for path in sorted((BASE/'chunks').glob('A_???.json')):
 rows=json.loads(path.read_text());changed=False
 for r in rows:
  original_semantics={k:r[k] for k in ['eligibility','facts','legal_issues','evidence_discussed','text_sections','quality']}
  src={p['passage_id']:p['text'] for p in SOURCES[r['case_id']]['passages']}
  old_evidence={e['evidence_id']:e for e in r['evidence']}
  narrow={}
  for eid in r['outcome']['disposition_evidence']:
   e=old_evidence[eid];quote=e['quote']
   # Only refine a complete-passage citation already explicitly chosen as current disposition.
   if quote!=src[e['passage_id']]:continue
   candidate=None
   m=re.search(r'(?i)\b(?:It is hereby )?Ordered that\b.*?\.(?=\s+[A-Z]|\s*$)',quote)
   if m:candidate=m.group(0)
   if candidate is None:
    m=re.search(r'\bunanimously (?:affirmed|reversed|vacated|modified)\b.*?\.(?=\s+[A-Z]|\s*$)',quote)
    if m:candidate=m.group(0)
   if candidate is None:
    m=re.search(r'\b(?:affirmed|reversed|vacated|modified), (?:on the law, )?(?:without|with) costs[^.]*\.',quote)
    if m:candidate=m.group(0)
   if candidate is None:
    m=re.search(r'(?i)\bwe (?:affirm|reverse)\.',quote)
    if m:candidate=m.group(0)
   if candidate is None:
    miss.append((r['case_id'],e['passage_id']));continue
   assert src[e['passage_id']].count(candidate)==1
   new_id=f'E{max(int(x[1:]) for x in [v["evidence_id"] for v in r["evidence"]])+1:03d}'
   r['evidence'].append(dict(evidence_id=new_id,passage_id=e['passage_id'],quote=candidate,statement_status='current_disposition'))
   narrow[eid]=new_id;preview.append((r['case_id'],candidate))
  # Broad evidence can contain testimony, allegations and findings together; do not falsely call all of it a court finding.
  for e in r['evidence']:
   if e['quote']==src[e['passage_id']] and e['evidence_id'] not in narrow.values():
    
    if e['statement_status']!='unclear':e['statement_status']='unclear';changed=True
  if narrow:
   r['outcome']['disposition_evidence']=[narrow.get(eid,eid) for eid in r['outcome']['disposition_evidence']]
   for cue in r['outcome_cues']:
    if cue['kind']=='current_disposition':cue['evidence_ids']=[narrow.get(eid,eid) for eid in cue['evidence_ids']]
   for order in r['outcome']['orders']:
    order['evidence_ids']+= [narrow[eid] for eid in order['evidence_ids'] if eid in narrow]
   changed=True
  # Exact hand-authored short quotes keep their original semantic statement status.
  assert all(r[k]==v for k,v in original_semantics.items())
 if not changed:continue
 existing=sorted((BASE/'drafts').glob(path.stem+'.draft-v*.json'))
 version=max(int(p.stem.rsplit('v',1)[1]) for p in existing)+1
 predecessor=f'drafts/{path.stem}.draft-v{version-1}.json'
 for r in rows:
  r['run']['supersedes']=predecessor
  r['run']['review_note']='Assistant quotation-precision revision; labels unchanged. Mixed passage-level evidence has unclear statement_status; exact controlling-disposition quote is separate. Human review pending. Earlier substantive corrections remain documented in corrections.md.'
 draft=BASE/f'drafts/{path.stem}.draft-v{version}.json';dump(draft,rows);dump(path,rows)
 expected=json.loads((ROOT/f'batches/A/chunks/{path.stem}.expected.json').read_text())['case_ids']
 v=validate(rows,SOURCES,expected);dump(BASE/f'chunks/{path.stem}.validation.json',v);assert v['passed'],v['errors']
 log.append(dict(chunk=path.stem,selected=draft.name,supersedes=predecessor))
dump(BASE/'evidence_refinement_log.json',dict(label_changes=False,revisions=log,narrow_dispositions_added=len(preview),unrefined_passages=miss,limitation='Mixed full-passage evidence is retained as unclear statement status; human semantic review remains pending.'))
update()
print('revised chunks',len(log),'narrow quotes',len(preview),'unrefined',miss)
for cid,quote in preview:print(cid,quote)
