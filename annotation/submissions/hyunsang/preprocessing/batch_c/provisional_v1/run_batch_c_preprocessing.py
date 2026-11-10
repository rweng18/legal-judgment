#!/usr/bin/env python3
"""Batch C provisional preprocessing (label-blind text rules, same B mask_v2).
Read current source annotations with git show; never modify teammates' files.
Run with Python 3.12 + pinned numpy/transformers from experiments/provisional_b.
"""
import csv, json, hashlib, os, sys, subprocess, pathlib, re, difflib, collections, statistics, math, datetime
from b_mask_v2 import mask, flags, n_words
ROOT=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path.home()/'Downloads/legal-judgment'
OUT=ROOT
assert (REPO/'.git').exists(), f'Repository missing at {REPO}'
assert (REPO/'experiments/provisional_b/lengths.py').exists()
assert (ROOT/'cases.jsonl').exists()

def git_show(ref,path):
    return subprocess.check_output(['git','-C',str(REPO),'show',f'{ref}:{path}'],text=True)

def parse_annotations(text,reviewer):
    rows=[json.loads(line) for line in text.splitlines() if line.strip()]
    lookup={r['case_id']:r for r in rows}
    assert len(rows)==168 and len(lookup)==168, (reviewer,len(rows),len(lookup))
    return lookup

# Load Becca+Hyunsang from main and Yinkui's separate annotation branch.
PATH='annotation/submissions/{}/batches/C/annotations.jsonl'
reviews={}
for reviewer in ('hyunsang','becca'):
    reviews[reviewer]=parse_annotations(git_show('origin/main',PATH.format(reviewer)),reviewer)
try:
    ytext=git_show('origin/annotations/yinkui-batch-c',PATH.format('yinkui'))
except subprocess.CalledProcessError:
    print('Fetching only Yinkui C branch (does not checkout or change local code)...',flush=True)
    subprocess.run(['git','-C',str(REPO),'fetch','origin','annotations/yinkui-batch-c:refs/remotes/origin/annotations/yinkui-batch-c'],check=True)
    ytext=git_show('origin/annotations/yinkui-batch-c',PATH.format('yinkui'))
reviews['yinkui']=parse_annotations(ytext,'yinkui')
ids=set(reviews['hyunsang'])
assert all(set(x)==ids for x in reviews.values()), '3 reviewer C case sets differ; stop for review.'
SOURCE={r['case_id']:r for r in (json.loads(line) for line in (ROOT/'cases.jsonl').open())}
assert len(SOURCE)==506 and ids.issubset(SOURCE), (len(SOURCE),len(ids-set(SOURCE)))

def dump(name,x): (OUT/name).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def csvout(name,rows,fields=None):
    rows=list(rows)
    if not fields:fields=list(dict.fromkeys(k for x in rows for k in x))
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def period(s):
    y=int(s[:4]);return 'train' if y<=2020 else 'validation' if y<=2022 else 'test'

# Reviewer labels are AUDIT ONLY, never passed to text cleaning or masking functions.
audit=[]
for k in sorted(ids):
    s=SOURCE[k]
    labels={name:reviews[name][k]['eligibility']['binary_task'] for name in reviews}
    assert all(reviews[name][k]['text_sha256']==s['text_sha256'] for name in reviews),f'Source SHA mismatch {k}'
    agree=len(set(labels.values()))==1
    audit.append(dict(case_id=k,case_name=s['case_name'],date_filed=s['date_filed'],period=period(s['date_filed']),source_url=s['source_url'],source_text_sha256=s['text_sha256'],**labels,agreement_status='unanimous' if agree else 'disagreement',unanimous_eligibility=next(iter(labels.values())) if agree else '',adjudication_status='pending_human_review',family_id_provisional=k,family_review_status='pending'))
csvout('C_three_reviewer_audit_168.csv',audit)

# Candidate duplicates/related family screen among all 506 opinions. Do not treat
# a candidate pair as established law/case identity; each needs human confirmation.
def normalized(s):return re.sub('[^a-z0-9]','',re.sub(r'^(?:in the matter of|matter of)\s+','',s.lower()))
by_date=collections.defaultdict(list)
for k,s in SOURCE.items():by_date[s['date_filed']].append(k)
by_hash=collections.defaultdict(list)
for k,s in SOURCE.items():by_hash[s['text_sha256']].append(k)
shingle_cache={}
def shingles(k):
    if k not in shingle_cache:
        words=re.findall(r'[a-z0-9]+',SOURCE[k]['text'].lower())
        shingle_cache[k]=set(tuple(words[i:i+5]) for i in range(max(0,len(words)-4)))
    return shingle_cache[k]
candidates={}
def add_pair(a,b,reason):
    if a==b:return
    a,b=sorted((a,b))
    if a not in ids and b not in ids:return
    candidates.setdefault((a,b),set()).add(reason)
for keys in list(by_hash.values()):
    for i,a in enumerate(keys):
        for b in keys[i+1:]:add_pair(a,b,'same_source_hash')
for keys in by_date.values():
    for i,a in enumerate(keys):
        for b in keys[i+1:]:
            na,nb=normalized(SOURCE[a]['case_name']),normalized(SOURCE[b]['case_name'])
            if na==nb or difflib.SequenceMatcher(None,na,nb).ratio()>=.89:add_pair(a,b,'same_day_similar_caption')
family_rows=[];strong=[]
for (a,b),reasons in sorted(candidates.items()):
    sa,sb=shingles(a),shingles(b)
    sim=len(sa&sb)/max(1,len(sa|sb))
    same_hash=SOURCE[a]['text_sha256']==SOURCE[b]['text_sha256']
    strong_candidate=same_hash or (SOURCE[a]['date_filed']==SOURCE[b]['date_filed'] and sim>=.65)
    if strong_candidate:strong.append((a,b))
    family_rows.append({'a':a,'b':b,'same_day':SOURCE[a]['date_filed']==SOURCE[b]['date_filed'],'source_hash_equal':same_hash,'similarity_5gram_jaccard':round(sim,4),'candidate_reason':';'.join(sorted(reasons)),'assessment':'strong_source_duplicate_candidate' if strong_candidate else 'weak_caption_candidate','review_status':'needs_team_family_confirmation','period_a':period(SOURCE[a]['date_filed']),'period_b':period(SOURCE[b]['date_filed'])})
csvout('case_family_review_C_candidates.csv',family_rows,fields=['a','b','same_day','source_hash_equal','similarity_5gram_jaccard','candidate_reason','assessment','review_status','period_a','period_b'])
parent={k:k for k in SOURCE}
def find(k):
    while parent[k]!=k:parent[k]=parent[parent[k]];k=parent[k]
    return k
def union(a,b):
    x,y=find(a),find(b)
    if x!=y:parent[max(x,y)]=min(x,y)
for a,b in strong:union(a,b)
members=collections.defaultdict(list)
for k in SOURCE:members[find(k)].append(k)
cross={family for family,group in members.items() if len({period(SOURCE[k]['date_filed']) for k in group})>1}
manifest=[]
for r in audit:
    k=r['case_id'];f=find(k);manifest.append({'case_id':k,'period':r['period'],'family_id_PROVISIONAL':f,'family_members':';'.join(sorted(members[f])),'family_cross_period_PROVISIONAL':f in cross,'family_review_status':'NOT_APPROVED'})
csvout('case_family_manifest_C_168_PROVISIONAL.csv',manifest)

def full_clean(text):
    # Same FULL cleaning implementation as A/B prototype, imported from local repo.
    sys.path.insert(0,str(REPO/'experiments/provisional_a'))
    from preprocessing import clean_text
    return clean_text(text)

# Only unanimous-include cases in train/validation; cross-period candidate groups
# withheld pending family resolution, even from this provisional development set.
dev=[];qc=[];logs=[];clean_audit=[]
for r in audit:
    if r['unanimous_eligibility']!='include' or r['period']=='test':continue
    k=r['case_id'];f=find(k)
    if f in cross:continue
    full,full_removed=full_clean(SOURCE[k]['text'])
    masked,removed,pieces=mask(full)
    ff,loss,cues=flags(full,masked,removed,pieces)
    if not full.strip() or not masked.strip():
        raise RuntimeError(f'Empty FULL or MASKED for {k}; manual intervention required')
    dev.append({'case_id':k,'batch':'C','date_filed':r['date_filed'],'period':r['period'],'texts':{'FULL':full,'MASKED':masked}})
    qc.append({'case_id':k,'period':r['period'],'full_words':n_words(full),'masked_words_v2':n_words(masked),'removed_words':n_words(full)-n_words(masked),'removed_pct_v2':round(loss,2),'sentences_detected':len(pieces),'removed_sentence_count_v2':len(removed),'max_removed_sentence_words':max([x['words'] for x in removed],default=0),'flags':';'.join(ff),'residual_cues':' | '.join(cues),'family_id_PROVISIONAL':f,'text_review_status':'AUTOMATED_QC_ONLY'})
    logs.append({'case_id':k,'period':r['period'],'mask_version':'mask_v2_abbreviation_boundary_pre_review','removed':removed,'input_full_sha256':hashlib.sha256(full.encode()).hexdigest(),'output_masked_sha256':hashlib.sha256(masked.encode()).hexdigest()})
    clean_audit.append({'case_id':k,'full_clean_removals':full_removed})
dev.sort(key=lambda x:x['case_id']);qc.sort(key=lambda x:x['case_id']);logs.sort(key=lambda x:x['case_id'])
assert len({r['case_id'] for r in dev})==len(dev)
assert all(r['period'] in ('train','validation') and r['batch']=='C' and r['texts']['FULL'] and r['texts']['MASKED'] for r in dev)
assert all(r['case_id'] in ids for r in dev)
with (OUT/'C_development_v2_PROVISIONAL.jsonl').open('w') as f:
    for r in dev:f.write(json.dumps(r,ensure_ascii=False)+'\n')
with (OUT/'masking_removal_logs_v2.jsonl').open('w') as f:
    for r in logs:f.write(json.dumps(r,ensure_ascii=False)+'\n')
with (OUT/'full_clean_removal_audit.jsonl').open('w') as f:
    for r in clean_audit:f.write(json.dumps(r,ensure_ascii=False)+'\n')
csvout('C_masking_qc_v2.csv',qc)
csvout('C_masking_review_queue_v2.csv',[r for r in qc if r['flags']],fields=list(qc[0]) if qc else ['case_id','flags'])

def stat(a):
    if not a:return None
    a=sorted(a)
    return {'min':a[0],'median':statistics.median(a),'mean':round(statistics.mean(a),3),'p90':a[min(len(a)-1,math.ceil(.90*len(a))-1)],'max':a[-1]}
word_summary={}
for sp in ('train','validation'):
    subset=[r for r in qc if r['period']==sp]
    word_summary[sp]={'cases':len(subset),'FULL_words':stat([r['full_words'] for r in subset]),'MASKED_words':stat([r['masked_words_v2'] for r in subset]),'words_removed_pct':stat([r['removed_pct_v2'] for r in subset])}
dump('word_length_summary_v2.json',word_summary)
counts=collections.Counter(r['unanimous_eligibility'] if r['unanimous_eligibility'] else 'disagreement' for r in audit)
report={'batch':'C','candidate_count':168,'source_pool':506,'agreement':dict(counts),'development_cases':len(dev),'train':sum(r['period']=='train' for r in dev),'validation':sum(r['period']=='validation' for r in dev),'excluded_cross_period_family_ids':sorted(cross & {find(k) for k in ids}),'family_candidate_pairs':len(family_rows),'strong_candidate_pairs':len(strong),'qc_flagged_cases':sum(bool(r['flags']) for r in qc),'qc_large_mask_loss_cases':[r['case_id'] for r in qc if r['removed_pct_v2']>=35],'status':'PROVISIONAL_PRE_HUMAN_REVIEW','encoder_status':'pending'}
dump('RUN_SUMMARY.json',report)

# Repeat Rebecca's exact pinned LEGAL-BERT tokenizer length protocol.
output=OUT/'C_v2_exact_token_lengths'
if output.exists():raise FileExistsError(f'{output} already exists. Refusing to overwrite exact length results.')
print('Generating exact LEGAL-BERT tokenizer lengths...',flush=True)
env=dict(os.environ,PYTHONPATH=str(REPO/'experiments/provisional_b'))
subprocess.run([sys.executable,str(REPO/'experiments/provisional_b/lengths.py'),str(OUT/'C_development_v2_PROVISIONAL.jsonl'),str(output)],cwd=str(REPO/'experiments/provisional_b'),env=env,check=True)
assert (output/'case_lengths.csv').exists() and (output/'length_summary.json').exists()
report['encoder_status']='complete'
dump('RUN_SUMMARY.json',report)
(OUT/'SUBMISSION_README.md').write_text(f"""# Batch C provisional preprocessing — engineering handoff

**PRE-REVIEW / NOT HUMAN GOLD / NOT FROZEN.** Generated using local GitHub reviewer submissions and the 506-case source snapshot. This package is not human-adjudicated data.

- Batch C candidates: 168, counts: {json.dumps(dict(counts),sort_keys=True)}
- Unanimous-inclusion development only: **{len(dev)}** cases ({report['train']} train, {report['validation']} validation). No 2023–2024 test texts.
- Case-family screen: {len(family_rows)} candidate pairs; {len(strong)} strong source-duplicate candidates, **NOT legal confirmations**. Cross-period candidates withheld pending review.
- FULL: `experiments/provisional_a/preprocessing.py:clean_text` (team code).
- MASKED: same label-independent revised `mask_v2` used in Batch B; per-case removal logs and automatic QC included.
- Exact lengths: `experiments/provisional_b/lengths.py`, pinned LEGAL-BERT tokenizer (510 content tokens/chunk, no overlap). `C_v2_exact_token_lengths/` holds statistics.
- Input snapshot `cases.jsonl` (506 candidates) and reviewer decisions are AUDIT material, never model features.
- Remaining: human review/adjudication, family and masking QC confirmation, frozen B+C release, hashes/splits checked again.

Generated source provenance: GitHub `origin/main` for hyunsang/becca C, `origin/annotations/yinkui-batch-c` for yinkui C.
""")
checks={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.is_file() and p.name!='file_checksums_sha256.json'}
dump('file_checksums_sha256.json',checks)
print('DONE: '+json.dumps(report,ensure_ascii=False,indent=2))
