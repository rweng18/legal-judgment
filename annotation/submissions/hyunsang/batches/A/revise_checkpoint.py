from assemble import *
changes={}
for chunk in ['A_001','A_002','A_009']:
 path=BASE/f'chunks/{chunk}.json';rows=json.loads(path.read_text());notes=[]
 if chunk=='A_001':
  r=rows[0];r['evidence'].append(dict(evidence_id='E006',passage_id='P002',quote='We affirm.',statement_status='current_disposition'))
  r['outcome_cues']=[dict(kind='current_disposition',evidence_ids=['E002']),dict(kind='repeated_outcome',evidence_ids=['E006']),dict(kind='indirect_reasoning',evidence_ids=['E004','E005'])]
  rows[2]['facts']['evidence_ids'].append('E003')
  notes=['Patricola repeated-outcome cue now cites exact We affirm rather than denial-of-entitlement reasoning.','Coreano factual snow-removal support additionally references E003.']
 if chunk=='A_002':
  r=rows[3];s=SOURCES[r['case_id']];quote=next(p['text'] for p in s['passages'] if p['passage_id']=='P002')
  r['evidence'].append(dict(evidence_id='E007',passage_id='P002',quote=quote,statement_status='court_finding'))
  next(i for i in r['legal_issues'] if i['topic']=='creation_of_hazard')['evidence_ids']=['E007']
  notes=['Mister creation-of-hazard burden rule linked directly to P002 rather than notice holding alone.']
 if chunk=='A_009':
  r=rows[2];r['facts']['injured_role']='unclear'
  r['quality']['notes']='Jump to avoid fall expressly stated; no actual slip/trip-and-fall. Employer/contracting relationship not specified, so injured_role unclear.'
  r['evidence_discussed']=[dict(type='other',description='No evidence establishing last staircase inspection submitted; inspection records specifically not identified.',evidence_ids=['E003','E004'])]
  notes=['Hanney working on mechanical system does not establish employee/contractor relationship; role corrected to unclear.','No last-inspection evidence does not specifically identify inspection records; evidence type corrected to other.']
 for r in rows:
  r['run']['supersedes']=f'drafts/{chunk}.draft-v1.json'
  r['run']['review_note']='Assistant source-based correction; no human review. See corrections.md.'
 draft=BASE/f'drafts/{chunk}.draft-v2.json';assert not draft.exists();dump(draft,rows);dump(path,rows)
 expected=json.loads((ROOT/f'batches/A/chunks/{chunk}.expected.json').read_text())['case_ids'];v=validate(rows,SOURCES,expected);dump(BASE/f'chunks/{chunk}.validation.json',v);assert v['passed'],v['errors'];changes[chunk]=notes
(BASE/'corrections.md').write_text('# Assistant corrections; human review pending\n\n'+''.join(f'## {c}\n\n'+''.join(f'- {s}\n' for s in ns)+'\n' for c,ns in changes.items()))
update()
