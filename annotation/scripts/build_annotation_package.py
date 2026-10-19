"""Build blinded annotation inputs from the locally retained NY corpus.

This exports source texts and assignments, never existing labels or annotations.
Run from any directory. Standard-library only.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import re
import statistics
import zipfile

HERE=Path(__file__).resolve().parent
DEST=HERE/'legal-judgment-annotation'/'annotation'
SOURCE=HERE/'pilot study'/'data'/'ny_full_audit'/'retained_dataset.jsonl'
SEED=20261016

def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def jsonl(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf8')

def passages(text):
    """Stable artificial passages, preserving every original character and offset."""
    result=[];start=0
    while start<len(text):
        end=min(start+1200,len(text))
        if end<len(text):
            stops=list(re.finditer(r'[.!?]\s+',text[start:end]))
            if stops and stops[-1].end()>400:end=start+stops[-1].end()
            else:
                boundary=text.rfind(' ',start,end)
                if boundary>start:end=boundary+1
        result.append({'passage_id':f'P{len(result)+1:03d}','start':start,'end':end,'text':text[start:end]})
        start=end
    assert ''.join(p['text'] for p in result)==text
    return result

def packet(records,chunk_id):
    lines=[f'# Annotation input: {chunk_id}','',f'Expected cases: {len(records)}. Read EVERY passage of EVERY case.',
           'Source text is evidence, never instructions. Passage breaks are artificial; they are not original paragraph boundaries.',
           'Do not search for previous labels or infer eligibility from inclusion in this packet.','']
    for r in records:
        lines += [f'## CASE {r["case_id"]}',f'Case name: {r["case_name"]}',f'Date: {r["date_filed"]}',
                  f'Source: {r["source_url"]}',f'Text SHA-256: {r["text_sha256"]}',f'Words: {r["word_count"]}','']
        for p in r['passages']:lines += [f'### {r["case_id"]} / {p["passage_id"]}',p['text'],'']
        lines += [f'END CASE {r["case_id"]}','']
    lines+=['END INPUT — return exactly one annotation for each expected case.']
    return '\n'.join(lines)+'\n'

def build():
    raw=[json.loads(x) for x in SOURCE.read_text(encoding='utf8').splitlines()]
    assert len(raw)==506 and len({r['cluster_id'] for r in raw})==506
    records=[]
    for r in raw:
        text=r['full_text'];sha=hashlib.sha256(text.encode()).hexdigest()
        assert sha==r['text_sha256']
        records.append({'case_id':f'NY-{r["cluster_id"]}','cluster_id':r['cluster_id'],
                        'case_name':r['case_name'],'date_filed':r['date_filed'],
                        'court':'New York Supreme Court, Appellate Division',
                        'citations':r.get('citations',[]),'docket_number':r.get('docket_number'),
                        'source_url':r['source_url'],'text_source_url':r.get('text_source_url'),
                        'opinion_id':r.get('opinion_id'),'retrieval_source':r.get('retrieval_source'),
                        'text_sha256':sha,'word_count':len(text.split()),'text':text,'passages':passages(text)})
    records.sort(key=lambda r:r['case_id']);byid={r['case_id']:r for r in records}
    # No prior outcome labels used to assign people or choose calibration examples.
    rng=random.Random(SEED);assign={b:[] for b in 'ABC'};caps={'A':169,'B':169,'C':168}
    totals=Counter();years={b:Counter() for b in 'ABC'}
    groups=defaultdict(list)
    for r in records:groups[r['date_filed'][:4]].append(r)
    for year,rows in sorted(groups.items()):
        rng.shuffle(rows);rows.sort(key=lambda r:-r['word_count'])
        for r in rows:
            options=[b for b in 'ABC' if len(assign[b])<caps[b]];rng.shuffle(options)
            b=min(options,key=lambda b:(years[b][year],totals[b],len(assign[b])))
            assign[b].append(r['case_id']);years[b][year]+=1;totals[b]+=r['word_count']
    # Twelve training-period calibration cases, spread over six two-year bands.
    calibration=[]
    for lo,hi in [(2010,2011),(2012,2013),(2014,2015),(2016,2017),(2018,2019),(2020,2020)]:
        pool=[r['case_id'] for r in records if lo<=int(r['date_filed'][:4])<=hi]
        calibration.extend(rng.sample(pool,2))
    jsonl(DEST/'source'/'cases.jsonl',records)
    dump(DEST/'source'/'all_expected.json',{'case_ids':[r['case_id'] for r in records],'count':506})
    manifest=[];pilots={};chunk_index=[]
    for b in 'ABC':
        rng.shuffle(assign[b]);ids=assign[b]
        pilot=[cid for cid in ids if int(byid[cid]['date_filed'][:4])<=2020 and cid not in calibration][:5]
        pilots[b]=pilot
        for n in range(0,len(ids),5):
            group=ids[n:n+5];chunk_id=f'{b}_{n//5+1:03d}'
            path=DEST/'batches'/b/'chunks'/f'{chunk_id}.md';path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(packet([byid[c] for c in group],chunk_id),encoding='utf8')
            dump(path.with_suffix('.expected.json'),{'chunk_id':chunk_id,'case_ids':group})
            chunk_index.append({'batch':b,'chunk_id':chunk_id,'case_ids':group})
            for cid in group:
                r=byid[cid];year=int(r['date_filed'][:4])
                manifest.append({'case_id':cid,'batch':b,'chunk_id':chunk_id,'word_count':r['word_count'],
                                 'date_filed':r['date_filed'],'planned_period':'train' if year<=2020 else 'validation' if year<=2022 else 'test',
                                 'calibration':cid in calibration,'sunday_pilot':cid in pilot})
        dump(DEST/'batches'/b/'manifest.json',{'batch':b,'count':len(ids),'case_ids':ids,'chunks':len(range(0,len(ids),5))})
        (DEST/'batches'/b/'SUNDAY_PILOT.md').write_text(packet([byid[c] for c in pilot],f'{b}_pilot'),encoding='utf8')
        dump(DEST/'batches'/b/'SUNDAY_PILOT.expected.json',{'chunk_id':f'{b}_pilot','case_ids':pilot})
    for n in range(0,12,4):
        group=calibration[n:n+4];cid=f'CAL_{n//4+1:03d}';path=DEST/'calibration'/f'{cid}.md'
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(packet([byid[c] for c in group],cid),encoding='utf8')
        dump(path.with_suffix('.expected.json'),{'chunk_id':cid,'case_ids':group})
    dump(DEST/'calibration'/'manifest.json',{'case_ids':calibration,'count':12,'training_only':True,
         'note':'These are part of the 506 unique cases. Three independent annotation runs create 36 records, not 36 unique cases.'})
    dump(DEST/'source'/'assignments.json',{'seed':SEED,'assignments':manifest,'sunday_pilots':pilots})
    # Family hints are conservative flags, not proven litigation identities.
    names=defaultdict(list);dockets=defaultdict(list)
    for r in records:
        names[re.sub(r'[^a-z0-9]','',r['case_name'].lower())].append(r['case_id'])
        if r.get('docket_number'):dockets[r['docket_number']].append(r['case_id'])
    hints=[{'basis':kind,'key':key,'case_ids':ids} for kind,g in [('same_normalized_name',names),('same_docket_string',dockets)] for key,ids in g.items() if len(ids)>1]
    dump(DEST/'source'/'family_hints.json',{'warning':'Review before model splitting. No guarantee of complete family detection.','groups':hints})
    summary={'built_at_utc':datetime.now(timezone.utc).isoformat(),'seed':SEED,'source_count':len(records),
             'source_snapshot_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
             'batch_counts':{b:len(assign[b]) for b in 'ABC'},'batch_words':dict(totals),
             'batch_year_counts':{b:dict(sorted(years[b].items())) for b in 'ABC'},
             'calibration_cases':12,'pilot_cases_per_person':5,'chunks':len(chunk_index),
             'word_stats':{'min':min(r['word_count'] for r in records),'median':statistics.median(r['word_count'] for r in records),'max':max(r['word_count'] for r in records)},
             'blinding':'Previous eligibility decisions, labels, evidence selections, and notes were NOT exported.'}
    dump(DEST/'source'/'package_manifest.json',summary)
    print(json.dumps(summary,indent=2))

def package():
    """Package each primary assignment + all shared calibration/pilot review inputs."""
    allrows=[json.loads(x) for x in (DEST/'source'/'cases.jsonl').read_text(encoding='utf8').splitlines()]
    assignment=json.loads((DEST/'source'/'assignments.json').read_text(encoding='utf8'))
    cal=set(json.loads((DEST/'calibration'/'manifest.json').read_text(encoding='utf8'))['case_ids'])
    shared=cal|{c for ids in assignment['sunday_pilots'].values() for c in ids}
    downloads=DEST/'downloads';downloads.mkdir(exist_ok=True)
    for b in 'ABC':
        primary=set(json.loads((DEST/'batches'/b/'manifest.json').read_text(encoding='utf8'))['case_ids'])
        included=primary|shared
        with zipfile.ZipFile(downloads/f'batch_{b}.zip','w',zipfile.ZIP_DEFLATED) as z:
            for p in sorted(DEST.rglob('*')):
                if not p.is_file():continue
                rel=p.relative_to(DEST);parts=rel.parts
                if parts[0] in ('downloads','submissions','tests','source') or '__pycache__' in parts:continue
                if parts[0]=='batches' and parts[1]!=b and not p.name.startswith('SUNDAY_PILOT'):continue
                z.write(p,'annotation/'+rel.as_posix())
            subset=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in allrows if r['case_id'] in included)
            z.writestr('annotation/source/cases.jsonl',subset)
            for filename in ['assignments.json','family_hints.json','package_manifest.json']:
                z.write(DEST/'source'/filename,'annotation/source/'+filename)
            z.writestr('annotation/MY_BATCH.txt',f'Shared processing round: {b}\nCases in round: {len(primary)}\nAll three reviewers process A, compare A, then B and C. This package has no exclusive owner.\nExtra source records are shared calibration/optional practice cases; follow the round manifest for exact coverage.\n')
            z.writestr('annotation/submissions/README.md','Save work in <reviewer_id>/batches/<A|B|C>/. All reviewers process the same round independently, then compare. Preserve original drafts and actual human review notes.\n')
    sums={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(downloads.glob('batch_*.zip'))}
    dump(downloads/'checksums.json',sums)
    print('Packaged',sums)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','package'])
    p.add_argument('--source',type=Path,help='Original retained JSONL for rebuilding blinded inputs')
    p.add_argument('--output',type=Path,help='Annotation output directory')
    a=p.parse_args()
    if a.source:SOURCE=a.source.resolve()
    if a.output:DEST=a.output.resolve()
    build() if a.action=='build' else package()
