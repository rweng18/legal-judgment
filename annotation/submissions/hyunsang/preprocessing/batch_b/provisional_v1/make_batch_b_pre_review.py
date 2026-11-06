"""Rebuild provisional Batch B pre-review preprocessing QC from saved source-derived inputs.
Never promotes LLM labels to human reviewed; no test text enters development outputs.
"""
import csv, json, re, hashlib, statistics, math, collections, pathlib, itertools, difflib, zipfile
R=pathlib.Path(__file__).resolve().parent
OUT=R; OUT.mkdir(exist_ok=True)
SOURCE={r['case_id']:r for r in map(json.loads,open(R/'inputs/cases.jsonl',encoding='utf8'))}
AUD=list(csv.DictReader(open(R/'inputs/B_three_reviewer_audit_169.csv',encoding='utf8')))
OLD={r['case_id']:r for r in map(json.loads,open(R/'inputs/B_development_baseline_PROVISIONAL.jsonl',encoding='utf8'))}
assert len(AUD)==169 and len(OLD)==112 and len(SOURCE)==506

def dump(path,data): (OUT/path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def csvout(path,rows,columns=None):
 rows=list(rows);columns=columns or list(dict.fromkeys(k for row in rows for k in row))
 with (OUT/path).open('w',encoding='utf8',newline='') as f:
  w=csv.DictWriter(f,columns,extrasaction='ignore');w.writeheader();w.writerows(rows)
def period(s):
 y=int(s[:4]);return 'train' if y<=2020 else 'validation' if y<=2022 else 'test'

def caption(t):
 t=re.sub(r'^(?:in the matter of|matter of)\s+','',t.lower())
 return re.sub('[^a-z0-9]','',t)
def n_words(s):return len(s.split())

# Reevaluate family candidates across complete 506-item source pool. Candidate edges only,
# never treat shared retailer/caption or bare docket as conclusive.
old_pairs=list(csv.DictReader(open(R/'inputs/case_family_candidates.csv',encoding='utf8')))
pairs=[];strong=[];unresolved=[]
for p in old_pairs:
 a,b=p['a'],p['b'];sa,sb=SOURCE[a],SOURCE[b]
 na,nb=caption(sa['case_name']),caption(sb['case_name'])
 ratio=difflib.SequenceMatcher(None,na,nb).ratio()
 exact_title=(na==nb)
 exact_date=sa['date_filed']==sb['date_filed']
 same_hash=sa['text_sha256']==sb['text_sha256']
 da=re.sub('[^a-z0-9]','',str(sa.get('docket_number') or '').lower());db=re.sub('[^a-z0-9]','',str(sb.get('docket_number') or '').lower())
 same_docket=bool(da and db and da==db)
 # Consistent abbreviations/caption normalization, same decision day, high text overlap:
 # strong *provisional* association, not confirmed legal family identity.
 plaintiff_a=na.split('v')[0] if 'v' in na else na
 plaintiff_b=nb.split('v')[0] if 'v' in nb else nb
 # The public source has caption formats such as 'MANN, FRANCINE v.' versus 'Mann v.'.
 # Match a recognizable first-party surname plus same date and >=0.65 text overlap.
 shared_party=bool(len(plaintiff_a)>=4 and len(plaintiff_b)>=4 and (plaintiff_a.startswith(plaintiff_b) or plaintiff_b.startswith(plaintiff_a)))
 confidence='strong_source_duplicate_candidate' if (same_hash or (exact_date and (ratio>=0.93 or shared_party) and float(p['similarity_5gram'] or 0)>=.65)) else 'weak_caption_candidate'
 action='PROVISIONALLY_GROUP_FOR_SPLIT_QC' if confidence.startswith('strong') else 'DO_NOT_GROUP_WITHOUT_MORE_EVIDENCE'
 row={**p,'caption_similarity':round(ratio,4),'same_clean_caption':exact_title,'same_decision_date':exact_date,'same_source_hash':same_hash,'matching_docket':same_docket,'assessment':confidence,'proposed_action':action,'review_status':'needs_team_family_confirmation'}
 pairs.append(row)
 if action.startswith('PROVISIONALLY'):strong.append((a,b))
 else:unresolved.append((a,b))
csvout('case_family_review_7pairs.csv',pairs)
parent={k:k for k in SOURCE}
def find(x):
 while parent[x]!=x: parent[x]=parent[parent[x]];x=parent[x]
 return x
def union(a,b):
 x,y=find(a),find(b)
 if x!=y:parent[max(x,y)]=min(x,y)
for a,b in strong:union(a,b)
family={k:find(k) for k in SOURCE}
members=collections.defaultdict(list)
for k,v in family.items():members[v].append(k)
cross={f for f,ids in members.items() if len({period(SOURCE[k]['date_filed']) for k in ids})>1}
family_audit=[]
for a in AUD:
 k=a['case_id'];f=family[k]
 family_audit.append({'case_id':k,'period':period(SOURCE[k]['date_filed']),'case_name':SOURCE[k]['case_name'],'family_id_PROVISIONAL':f,'family_members':';'.join(sorted(members[f])),'family_cross_period_PROVISIONAL':f in cross,'family_review_status':'NOT_APPROVED'})
csvout('case_family_manifest_B_169_PROVISIONAL.csv',family_audit)
# Explicit named warning checks
warnings={name:[{'case_id':k,'name':s['case_name'],'in_batch_B':k in {r['case_id'] for r in AUD},'period':period(s['date_filed'])} for k,s in SOURCE.items() if name.lower() in s['case_name'].lower()] for name in ('Coreano','Sodhi')}
dump('named_family_warnings.json',warnings)

# The A prototype's masking is sentence-based and label independent. The critical
# correction is to stop treating periods inside legal citations/abbreviations as
# sentence endings and to stop keeping a 300+-word "sentence" together simply
# because bracket/parenthesis nesting was encountered. We protect common legal
# abbreviations and then split on sentence-ending punctuation in the normalized FULL.
ABBR=['v','vs','inc','corp','co','ltd','llc','j','jj','p.j','a.j','j.p','st','no','nos','dr','mr','mrs','ms','jr','sr','dept','assn','assoc','univ','auth','ctr','hous','ins','mt','ave','approx','id','cf','e.g','i.e','rd','dev','mgt','auth','dist','n.y','l.p']
ABBR_RE=re.compile(r'(?<!\w)('+ '|'.join(re.escape(x) for x in sorted(ABBR,key=len,reverse=True))+r')\.(?=\W|$)',re.I)
SENT_END=re.compile(r'(?<=[.!?])\s+(?=[“”"\'\u2018\u2019\[]*[A-Z])')
CUES=re.compile(r'\b(?:it is hereby )?ordered that\b|\bwe\s+(?:(?:therefore|accordingly|now|unanimously)\s+)?(?:affirm|reverse|vacate)\b|\b(?:order|judgment)\s+(?:must|should)\s+be\s+(?:affirmed|reversed|vacated)\b',re.I)

def split_legal(text):
 # Protect periods inside abbreviations, then recover the original spelling.
 protected=ABBR_RE.sub(lambda m:m.group().replace('.','\ue000'),text)
 # Protect decimals and legal citation markers like AD3d (no period there).
 protected=re.sub(r'(?<=\d)\.(?=\d)', '\ue000', protected)
 pieces=[];start=0
 for match in SENT_END.finditer(protected):
  end=match.start();piece=protected[start:end].replace('\ue000','.').strip()
  if piece:pieces.append(piece)
  start=match.end()
 tail=protected[start:].replace('\ue000','.').strip()
 if tail:pieces.append(tail)
 return pieces

def remove_parentheticals(s):
 for _ in range(10):
  nexts=re.sub(r'\([^()]*\)',' ',s)
  if nexts==s:break
  s=nexts
 return s

def outcome_rule(sent):
 s=remove_parentheticals(sent)
 if re.search(r'\b(?:it is hereby )?ordered that\b',s,re.I):return 'operative_order'
 if re.match(r'^(?:Orders?|Order and judgment|Judgment),',s,re.I) and re.search(r'\b(?:affirmed|reversed|vacated|modified)\b',s,re.I):return 'opening_disposition'
 if re.search(r'\bwe\s+(?:(?:therefore|accordingly|now|unanimously)\s+)?(?:affirm|reverse|vacate)\b',s,re.I):return 'we_current_disposition'
 if re.search(r'\b(?:order|judgment)\s+(?:must|should)\s+be\s+(?:affirmed|reversed|vacated)\b',s,re.I):return 'required_disposition'
 if re.search(r'\b(?:Supreme Court|motion court|court below)\s+(?:properly|correctly|erred|should have)\b',s,re.I):return 'express_review_of_appealed_ruling'
 if re.search(r'\bwe (?:agree|disagree) with (?:the )?Supreme Court',s,re.I):return 'express_agreement_with_appealed_ruling'
 if re.search(r'\b(?:summary judgment|motion|complaint|cross motion)\b.{0,100}\b(?:was|were|is|are|should have been)\s+(?:properly\s+)?(?:granted|denied|dismissed)\b',s,re.I) and re.match(r'^(?:Accordingly|Thus|Therefore|Summary judgment (?:was|should))',s,re.I):return 'repeated_current_result'
 return None

def mask(s):
 pieces=split_legal(s);kept=[];removed=[]
 for idx,part in enumerate(pieces):
  rule=outcome_rule(part)
  if rule:removed.append({'sentence_index':idx,'reason':rule,'sentence':part,'words':n_words(part)})
  else:kept.append(part)
 return ' '.join(kept),removed,pieces

def flags(full,masked,removed,pieces):
 loss=100*(n_words(full)-n_words(masked))/n_words(full)
 found=list(CUES.finditer(masked));x=[]
 if not masked.strip():x.append('EMPTY_MASKED')
 if n_words(masked)<60:x.append('SHORT_MASKED_LT60')
 if loss>=35:x.append('MASK_LOSS_GE35PCT')
 if any(d['words']>80 for d in removed):x.append('REMOVED_SENTENCE_GT80WORDS')
 if any(n_words(p)>180 for p in pieces):x.append('LONG_SEGMENT_GT180WORDS')
 if found:x.append('POSSIBLE_RESIDUAL_CUE')
 return x,loss,[m.group(0) for m in found[:5]]

rows=[];develop=[];logs=[];origqc=[]
for k,r in sorted(OLD.items()):
 full=r['texts']['FULL'];old=r['texts']['MASKED']
 masked,removed,pieces=mask(full)
 ff,loss,cue=flags(full,masked,removed,pieces)
 if k in {r['case_id'] for r in family_audit if r['family_cross_period_PROVISIONAL']}:ff.append('CROSS_PERIOD_FAMILY')
 rows.append({'case_id':k,'period':r['period'],'full_words':n_words(full),'masked_words_v1':n_words(old),'masked_words_v2':n_words(masked),'removed_words_v2':n_words(full)-n_words(masked),'removed_pct_v1':round(100*(n_words(full)-n_words(old))/n_words(full),2),'removed_pct_v2':round(loss,2),'sentences_detected':len(pieces),'removed_sentence_count_v2':len(removed),'max_removed_sentence_words':max([x['words'] for x in removed],default=0),'flags':';'.join(ff),'residual_cues':' | '.join(cue),'family_id_PROVISIONAL':family[k],'text_review_status':'AUTOMATED_QC_ONLY'})
 develop.append({**r,'texts':{'FULL':full,'MASKED':masked}})
 logs.append({'case_id':k,'period':r['period'],'mask_version':'mask_v2_abbreviation_boundary_pre_review','removed':removed,'input_full_sha256':hashlib.sha256(full.encode()).hexdigest(),'output_masked_sha256':hashlib.sha256(masked.encode()).hexdigest()})
 if k in ('NY-6079805','NY-6110053','NY-5939702'):origqc.append({'case_id':k,'old_removed_pct':round(100*(n_words(full)-n_words(old))/n_words(full),2),'new_removed_pct':round(loss,2),'notes':'Check legal reasoning preservation and residual direct cues; no label used for rule tuning.'})
csvout('B_masking_qc_112_v2.csv',rows)
csvout('B_masking_review_queue_v2.csv',[x for x in rows if x['flags']])
dump('masking_changes_3_known_problems.json',origqc)
with (OUT/'masking_removal_logs_v2.jsonl').open('w',encoding='utf8') as f:
 for r in logs:f.write(json.dumps(r,ensure_ascii=False)+'\n')
with (OUT/'B_development_v2_PROVISIONAL.jsonl').open('w',encoding='utf8') as f:
 for r in develop:f.write(json.dumps(r,ensure_ascii=False)+'\n')

# Deterministic QC contract: no labels in text, identical cases across variants,
# test texts never included, no empty texts, all original development cases retained.
assert len(develop)==112 and len({r['case_id'] for r in develop})==112
assert all(r['period'] in ('train','validation') and r['texts']['FULL'].strip() and r['texts']['MASKED'].strip() for r in develop)
assert all(set(r['texts'])=={'FULL','MASKED'} for r in develop)
assert all(r['case_id'] in SOURCE and r['date_filed']==SOURCE[r['case_id']]['date_filed'] for r in develop)
assert all(r['case_id'] not in set(k for k,x in SOURCE.items() if period(x['date_filed'])=='test') for r in develop)

# Paired word stats. This does NOT masquerade as LEGAL-BERT tokens.
def stat(vals):
 vals=sorted(vals);return {'min':vals[0],'median':statistics.median(vals),'mean':round(statistics.mean(vals),3),'p90':round(vals[min(len(vals)-1,math.ceil(.90*len(vals))-1)],3),'max':vals[-1]}
word_summary={}
for split in ['train','validation']:
 sub=[x for x in rows if x['period']==split]
 word_summary[split]={'cases':len(sub),'FULL_words':stat([x['full_words'] for x in sub]),'MASKED_words':stat([x['masked_words_v2'] for x in sub]),'words_removed':stat([x['removed_words_v2'] for x in sub]),'removed_pct':stat([x['removed_pct_v2'] for x in sub])}
dump('word_length_summary_v2.json',word_summary)

# Rerunnable tokenizer runner, using Rebecca's exact project implementation.
(OUT/'run_exact_legalbert_lengths.py').write_text('''"""Run from checked-out legal-judgment/experiments/provisional_b directory.
Usage: python /path/to/run_exact_legalbert_lengths.py /path/to/our_package
Requires numpy==2.3.4 transformers==4.57.1 and network/cache for pinned LEGAL-BERT.
"""
import sys, pathlib
package=pathlib.Path(sys.argv[1]).resolve()
repo=pathlib.Path.cwd()
assert (repo/'lengths.py').is_file() and (repo/'encoder_settings.json').is_file(), 'Run from legal-judgment/experiments/provisional_b'
from data import development_texts
from encoder import SETTINGS,load_tokenizer
assert SETTINGS['revision']=='15b570cbf88259610b082a167dacc190124f60f6'
import subprocess
subprocess.run([sys.executable,'lengths.py',str(package/'B_development_v2_PROVISIONAL.jsonl'),str(package/'B_v2_exact_token_lengths')],check=True)
print('Exact lengths generated:',package/'B_v2_exact_token_lengths')
''',encoding='utf8')

# Notebook without external libraries; uses standard python csv/json and matplotlib if available.
nb={'cells':[{'cell_type':'markdown','metadata':{},'source':['# Batch B preprocessing QC (provisional, not reviewed)\n','All results based on three-reviewer unanimous include candidates; NOT final gold or frozen B+C.']},
{'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':['import csv, json, pathlib, statistics\n','ROOT=pathlib.Path.cwd()\n','rows=list(csv.DictReader((ROOT/"B_masking_qc_112_v2.csv").open()))\n','family=list(csv.DictReader((ROOT/"case_family_review_7pairs.csv").open()))\n','summary=json.loads((ROOT/"word_length_summary_v2.json").read_text())\n','print("Development cases:",len(rows),"Family candidate pairs:",len(family))\n','print(json.dumps(summary,indent=2))']},
{'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':['flagged=[r for r in rows if r["flags"]]\n','print("Masking issues requiring source QA:",len(flagged))\n','for r in flagged: print(r["case_id"],r["period"],r["flags"],r["removed_pct_v2"])']},
{'cell_type':'markdown','metadata':{},'source':['## Frozen release gate\n','Do not mark `reviewed` until human adjudication. Once the B+C manifest, masks and family assignments are approved, rerun Rebecca\'s exact tokenizer on the frozen development file, check SHA-256 digests and provide release + audit bundle.']}],
'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},'nbformat':4,'nbformat_minor':5}
dump('Batch_B_QC_stats.ipynb',nb)

# Artifacts + decisions independent from human labeling.
report={'case_count':169,'source_count':506,'candidate_pairs':len(pairs),'strong_family_candidates':len(strong),'weak_family_candidates':len(unresolved),'strong_candidate_cross_period_B':sorted({r['case_id'] for r in family_audit if r['family_cross_period_PROVISIONAL']}),'development_case_count':len(rows),'train':sum(r['period']=='train' for r in rows),'validation':sum(r['period']=='validation' for r in rows),'revised_masking_flags':sum(bool(r['flags']) for r in rows),'revised_large_loss_cases':[r['case_id'] for r in rows if float(r['removed_pct_v2'])>=35],'revised_residual_cue_cases':[r['case_id'] for r in rows if 'POSSIBLE_RESIDUAL_CUE' in r['flags']],'original_problems':origqc,'human_review':'NOT_DONE','family_confirmed':'NOT_DONE','exact_legalbert_tokenization':'NOT_DONE_REQUIRES_PINNED_TOKENIZER','status':'PROVISIONAL_ENGINEERING_QC'}
dump('RUN_SUMMARY.json',report)
(OUT/'README.md').write_text('''# Batch B — PRE-REVIEW PREPROCESSING PACKAGE (engineering draft)\n\nFive tasks: (1) case-family screen: 7 candidate pairs, 5 strong from matching caption/date/high text overlap; (2) revised label-blind sentence masking; (3) FULL/MASKED quality flags and removal logs; (4) exact LEGAL-BERT tokenizer runner prepared, **NOT executed** in this runtime; (5) reproducible machine-readable data, Python generator, QC notebook and checksum support.\n\n## Sources\n- 506 source opinions and source metadata from the project, no external case lookup\n- 169 case Batch B 3-reviewer comparison table\n- 112 B unanimous-include *development-only* (97 train, 15 validation) source-derived FULL texts\n- pre-review FULL cleaning inherited from the A prototype; MASKED rules revised in the local QC generator\n\n## NOT completed / blockers\n- No human annotation adjudication, family confirmation, or final label release. The 30 B disagreements remain outside the exploratory modeling subset.\n- No exact LEGAL-BERT tokenizer result (network access to pinned checkpoint unavailable).\n- No proof of leakage-free masking: new text flags need a separate legal-content audit. Only training examples should inform further rule changes.\n- This package covers provisional B development only; final release requires reviewed B+C and 2023–24 metadata-only test cases.\n\n## Generate exact tokenizer lengths on Mac\n1. `cd ~/Developer/legal-judgment/experiments/provisional_b` (or actual clone path).\n2. `python3 -m venv .venv && source .venv/bin/activate`\n3. `python -m pip install "numpy==2.3.4" "transformers==4.57.1"`\n4. `python /absolute/path/to/Batch_B_PRE_REVIEW_READY/run_exact_legalbert_lengths.py /absolute/path/to/Batch_B_PRE_REVIEW_READY`\nThe output will be `B_v2_exact_token_lengths/case_lengths.csv` and `length_summary.json`. On later frozen B+C release, regenerate with **that** frozen development.jsonl.\n\n## Reproduce QC\nKeep the files `/mnt/data/cases.jsonl`, `/mnt/data/Batch_B_three_reviewer_comparison_PRELIMINARY/B_three_reviewer_audit_169.csv`, and `/mnt/data/Batch_B_processing_QC_2026_11_06/B_development_for_lengths_PROVISIONAL.jsonl` in the positions expected by `make_batch_b_pre_review.py` or edit its ROOT and input paths. The notebook uses only its package files and standard Python.\n''',encoding='utf8')
# checksums for handoff
checksums={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.is_file()}
dump('file_checksums_sha256.json',checksums)
with zipfile.ZipFile(R.parent/'Batch_B_PRE_REVIEW_READY_v3.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
 for f in OUT.iterdir():
  if f.is_file():z.write(f,arcname='Batch_B_PRE_REVIEW_READY/'+f.name)
 
 for file in (R/'inputs').iterdir(): z.write(file,arcname='Batch_B_PRE_REVIEW_READY/inputs/'+file.name)
print(json.dumps(report,ensure_ascii=False,indent=2))
