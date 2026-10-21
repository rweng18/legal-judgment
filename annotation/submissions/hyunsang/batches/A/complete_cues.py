from assemble import *
# Explicit source-passage selections authored from the full semantic readings above.
chosen={7:[2,3,4,3,3],8:[3,2,9,3,6],9:[2,5,4,5,4],10:[3,4,4,2,2],11:[2,4,2,2,4],12:[3,2,4,2,3],13:[3,2,3,5,4],14:[3,4,2,2,6],15:[3,4,4,4,7],16:[3,3,3,1,2],17:[3,3,3,2,7],18:[3,2,4,3,2],19:[4,2,2,4,5],20:[3,3,3,3,3],21:[3,6,2,5,3],22:[3,4,4,3,1],23:[4,2,2,5,3],24:[2,3,2,1,2],25:[6,3,3,2,3],26:[3,2,4,3,3],27:[3,3,2,2,4],28:[2,3,2,5,5],29:[2,3,6,3,8],30:[3,6,2,2,2],31:[4,3,4,2,2],32:[2,2,2,5,3],33:[2,3,2,3,3],34:[4,10,5,2]}
log=[]
for n,pids in chosen.items():
 chunk=f'A_{n:03d}';path=BASE/f'chunks/{chunk}.json';rows=json.loads(path.read_text());assert len(rows)==len(pids)
 for r,pn in zip(rows,pids):
  pid=f'P{pn:03d}';assert 'legal_reasoning' in next(s['types'] for s in r['text_sections'] if s['passage_id']==pid)
  ptext=next(p['text'] for p in SOURCES[r['case_id']]['passages'] if p['passage_id']==pid)
  evidence=next(e for e in r['evidence'] if e['passage_id']==pid and e['quote']==ptext)
  if not any(cue['kind']=='indirect_reasoning' for cue in r['outcome_cues']):r['outcome_cues'].append(dict(kind='indirect_reasoning',evidence_ids=[evidence['evidence_id']]))
  # Literal repeated first-person rulings, only from passages manually classified current_outcome.
  direct_pids={e['passage_id'] for e in r['evidence'] if e['evidence_id'] in r['outcome']['disposition_evidence']}
  for section in r['text_sections']:
   if 'current_outcome' not in section['types'] or section['passage_id'] in direct_pids:continue
   text=next(p['text'] for p in SOURCES[r['case_id']]['passages'] if p['passage_id']==section['passage_id'])
   for phrase in ['We affirm.','We reverse.']:
    if text.count(phrase)==1:
     eid=f'E{max(int(e["evidence_id"][1:]) for e in r["evidence"])+1:03d}'
     r['evidence'].append(dict(evidence_id=eid,passage_id=section['passage_id'],quote=phrase,statement_status='current_disposition'))
     r['outcome_cues'].append(dict(kind='repeated_outcome',evidence_ids=[eid]))
  if r['case_id']=='NY-4306620':
   ev=next(e for e in r['evidence'] if e['evidence_id'] in r['outcome']['disposition_evidence'])
   correct='It is hereby ORDERED that the order so appealed from is unanimously reversed on the law without costs, the motion is granted and the complaint and all cross claims against defendant Global Industrial Services, Inc. are dismissed.'
   assert SOURCES[r['case_id']]['passages'][1]['text'].count(correct)==1;ev['quote']=correct
  if r['case_id']=='NY-4929051':
   quote='Order, same court and Justice, entered July 16, 2020, which, to the extent appealed from as limited by the briefs, granted, upon default, Findlay\'s motion for summary judgment dismissing the complaint as against it, unanimously reversed, on the law, without costs, and the motion denied.'
   assert SOURCES[r['case_id']]['passages'][1]['text'].count(quote)==1
   eid=f'E{max(int(e["evidence_id"][1:]) for e in r["evidence"])+1:03d}'
   r['evidence'].append(dict(evidence_id=eid,passage_id='P002',quote=quote,statement_status='current_disposition'))
   r['outcome']['disposition_evidence'].append(eid);r['outcome']['orders'][1]['evidence_ids'].append(eid)
   r['outcome_cues'][0]['evidence_ids'].append(eid)
 existing=list((BASE/'drafts').glob(chunk+'.draft-v*.json'));ver=max(int(p.stem.rsplit('v',1)[1]) for p in existing)+1
 for r in rows:
  r['run']['supersedes']=f'drafts/{chunk}.draft-v{ver-1}.json'
  r['run']['review_note']='Assistant outcome-cue completion and evidence refinement; semantic labels unchanged. Broad mixed evidence has unclear statement status; exact outcome quotations separate. Human review pending.'
 draft=BASE/f'drafts/{chunk}.draft-v{ver}.json';dump(draft,rows);dump(path,rows)
 expected=json.loads((ROOT/f'batches/A/chunks/{chunk}.expected.json').read_text())['case_ids'];v=validate(rows,SOURCES,expected);dump(BASE/f'chunks/{chunk}.validation.json',v);assert v['passed'],v['errors']
 log.append(dict(chunk=chunk,selected=draft.name,supersedes=rows[0]['run']['supersedes']))
dump(BASE/'cue_completion_log.json',dict(label_changes=False,revisions=log,method='Manually selected reasoning passages from full readings; literal repeated rulings only in authored current-outcome passages.'))
update();print('All 169 records saved; 28 cue-completed chunks validated.')
