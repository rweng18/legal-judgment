"""Validate the delivered source/assignment package, never semantic labels."""
import hashlib,json,zipfile
from collections import Counter
from common import ROOT,read_records,dump
def main():
 sources=read_records(ROOT/'source'/'cases.jsonl');ids={r['case_id'] for r in sources}
 assert len(sources)==len(ids)==506
 assert len({r['text_sha256'] for r in sources})==506
 forbidden={'binary_label','label_status','screen_version','status','reason','evidence','appeal_context','note',
            'automated_status_before_review','automated_reason_before_review'}
 for r in sources:
  assert not forbidden.intersection(r)
  assert r['text_sha256']==hashlib.sha256(r['text'].encode()).hexdigest()
  assert r['word_count']==len(r['text'].split())
  assert ''.join(p['text'] for p in r['passages'])==r['text']
  assert all(r['text'][p['start']:p['end']]==p['text'] for p in r['passages'])
 assignments=json.loads((ROOT/'source'/'assignments.json').read_text(encoding='utf8'))['assignments']
 assert Counter(r['case_id'] for r in assignments)==Counter(ids)
 assert Counter(r['batch'] for r in assignments)=={'A':169,'B':169,'C':168}
 for b in 'ABC':
  expected=json.loads((ROOT/'batches'/b/'manifest.json').read_text(encoding='utf8'))['case_ids']
  chunkids=[]
  for p in (ROOT/'batches'/b/'chunks').glob('*.expected.json'):
   d=json.loads(p.read_text(encoding='utf8'));chunkids+=d['case_ids']
   packet=p.with_name(p.name.replace('.expected.json','.md')).read_text(encoding='utf8')
   for cid in d['case_ids']:assert f'END CASE {cid}' in packet
  assert Counter(chunkids)==Counter(expected)
 cal=json.loads((ROOT/'calibration'/'manifest.json').read_text(encoding='utf8'))['case_ids']
 byid={r['case_id']:r for r in sources}
 assert len(cal)==len(set(cal))==12 and all(byid[c]['date_filed'][:4]<='2020' for c in cal)
 pilots=[c for b in 'ABC' for c in json.loads((ROOT/'batches'/b/'SUNDAY_PILOT.expected.json').read_text(encoding='utf8'))['case_ids']]
 assert len(pilots)==len(set(pilots))==15 and not set(cal).intersection(pilots)
 assert all(byid[c]['date_filed'][:4]<='2020' for c in pilots)
 zipped={}
 for b in 'ABC':
  path=ROOT/'downloads'/f'batch_{b}.zip'
  if not path.exists():continue
  with zipfile.ZipFile(path) as z:
   assert z.testzip() is None
   package_rows=[json.loads(s) for s in z.read('annotation/source/cases.jsonl').decode('utf8').splitlines()]
   needed=set(json.loads((ROOT/'batches'/b/'manifest.json').read_text(encoding='utf8'))['case_ids'])|set(cal)|set(pilots)
   assert {r['case_id'] for r in package_rows}==needed
   assert all(r==byid[r['case_id']] for r in package_rows)
   for name in ['README.md','AGENTS.md','schema/annotation.schema.json','docs/CODEBOOK.md','scripts/validate_annotations.py']:
    assert 'annotation/'+name in z.namelist()
   zipped[b]={'source_records_including_shared':len(package_rows),'bytes':path.stat().st_size,
              'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 report={'passed':True,'source_count':506,'batch_counts':dict(Counter(r['batch'] for r in assignments)),
         'calibration_unique':12,'pilot_unique':15,'no_calibration_pilot_overlap':True,'no_previous_labels_in_sources':True,
         'source_hashes_and_offsets_valid':True,'archives':zipped,
         'note':'Package integrity only. No completed annotations or gold labels.'}
 dump(ROOT/'source'/'package_validation.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()

