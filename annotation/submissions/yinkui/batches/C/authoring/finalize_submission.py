"""Package manually authored C records, checking coverage and revision lineage.

Does not infer labels, consult peers, train models, or claim human adjudication.
"""
import hashlib,json,sys,subprocess,shutil
from collections import Counter
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import read_records,validate,dump,write_jsonl

def sha(p):return hashlib.sha256(p.read_text(encoding='utf8').encode('utf8')).hexdigest()
source={r['case_id']:r for r in read_records(ROOT/'source/cases.jsonl')}
expected=json.loads((ROOT/'batches/C/manifest.json').read_text(encoding='utf8'))['case_ids']
files=[OUT/f'chunks/C_{i:03d}.json' for i in range(1,35)]
rows=[];selected=[]
for p in files:
 records=read_records(p)
 v1=OUT/'drafts'/f'{p.stem}.draft-v1.json'
 v2=OUT/'drafts'/f'{p.stem}.draft-v2.json'
 assert v1.exists()
 chosen=v2 if v2.exists() else v1
 assert records==read_records(chosen)
 original={r['case_id']:r for r in read_records(v1)}
 for r in records:
  if r!=original[r['case_id']]:
   assert r['run']['supersedes']==f'drafts/{p.stem}.draft-v1.json#{r["case_id"]}'
   assert 'LLM self-audit revision v2:' in r['run']['review_note']
 rows.extend(records)
 selected.append({'chunk':p.stem,'selected_draft':str(chosen.relative_to(OUT)).replace('\\','/'),'records':len(records)})
report=validate(rows,source,expected)
assert report['passed'],report['errors']
assert len(rows)==len({r['case_id'] for r in rows})==168
assert all(r['run']['review_status']=='llm_draft' and r['run']['human_reviewer_id'] is None for r in rows)
assert {r['case_id']:r for r in rows}=={r['case_id']:r for r in read_records(OUT/'checkpoint.jsonl')}
rows.sort(key=lambda r:r['case_id'])
report=validate(rows,source,expected)
assert report['passed'],report['errors']
write_jsonl(OUT/'annotations.jsonl',rows);dump(OUT/'annotations.validation.json',report)
elig=dict(Counter(r['eligibility']['binary_task'] for r in rows))
classes=dict(Counter(str(r['outcome']['binary_label']) for r in rows if r['eligibility']['binary_task']=='include'))
cal=set(json.loads((ROOT/'calibration/manifest.json').read_text(encoding='utf8'))['case_ids'])
overlap=sorted(cal.intersection(expected))
assert all('Calibration overlap:' in r['run']['review_note'] for r in rows if r['case_id'] in overlap)
summary={'annotated_cases':168,'expected_cases':168,'eligibility':elig,'included_class_counts':classes,'review_status':{'llm_draft':168},'human_review_completed':False,'cross_comparison_performed':False,'prior_calibration_exposure_ids':overlap,'pending_case_ids':[],'note':'Complete independent LLM draft, not adjudicated data or classifier evaluation. Counts remain provisional.'}
dump(OUT/'annotations.summary.json',summary)
inputs=['AGENTS.md','README.md','docs/CODEBOOK.md','docs/CHATGPT_WORKFLOW.md','docs/QUALITY_CONTROL.md','docs/DECISIONS.md','schema/annotation.schema.json','prompts/ANNOTATE_CHUNK.md','batches/C/manifest.json','source/cases.jsonl']+[f'batches/C/chunks/C_{i:03d}.md' for i in range(1,35)]
provenance={'reviewer_id':'yinkui','round':'C','publication_date_local':'2026-11-03','timezone':'America/New_York','packaging_workspace_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT.parent,text=True).strip(),'schema_version':'1.0.0','prompt_version':'1.0.0','model_name':sorted({r['run']['model_name'] for r in rows}),'model_version':None,'annotation_time_min':min(r['run']['annotated_at'] for r in rows),'annotation_time_max':max(r['run']['annotated_at'] for r in rows),'method':'Interactive Codex read every supplied passage and manually authored each semantic field and exact evidence selection. Scripts serialized, validated, and packaged those selections. No external model API or subagents. Seven source-read self-audit corrections preserved in v2 drafts with explicit supersedes links.','peer_batch_C_labels_read':False,'cross_comparison_performed':False,'calibration_exposure_ids':overlap,'calibration_exposure_rule':'Previously compared calibration cases are not fresh blinded labels; keep training-only.','team_substantive_freeze_pending_in_decision_log':True,'human_review_completed':False,'input_sha256':{p:sha(ROOT/p) for p in inputs},'hash_normalization':'UTF-8 text with universal newlines normalized to LF before SHA-256; canonical source case text_sha256 values unchanged.'}
dump(OUT/'provenance.json',provenance)
dump(OUT/'run_manifest.json',{'reviewer_id':'yinkui','round':'C','completed_chunks':selected,'completed_case_ids':sorted(expected),'pending_case_ids':[],'validation_passed':True,'all_llm_drafts':True})
promptdir=OUT/'prompts_used';promptdir.mkdir(exist_ok=True)
shutil.copyfile(ROOT/'prompts/ANNOTATE_CHUNK.md',promptdir/'ANNOTATE_CHUNK_v1.0.0.md')
(promptdir/'README.md').write_text('''# Prompt provenance

The adjacent prompt is a verbatim copy of the repository template followed as guidance during interactive Codex annotation. It is not an invented API-call transcript. The user authorized completing Yinkui's Batch C using the same procedure as A, then authorized continuing and finishing Batch C on November 3, 2026.

Input instruction/source hashes are in `../provenance.json`. Actual selected fields and quotations are recorded in per-chunk authoring scripts. No external annotation API, subagent, or peer C labels were used. Prior calibration exposure is disclosed per affected record and in provenance.
''',encoding='utf8')
(OUT/'human_review_log.md').write_text('''# Human review status

Pending for all 168 Batch C records. Every selected record is `llm_draft` with null human reviewer ID. Prior human approval of Batch A does not approve Batch C.

The seven revisions in `revisions.json` are LLM self-audit corrections, not independent human review. Validation checks schema, quotes, hashes, references, IDs and passage coverage; it cannot establish semantic correctness.

After all independent C submissions are frozen, compare them and have Hayden/team review the original opinions. Record actual reviewer, date, evidence, eligibility and label decisions in a new reviewed version; retain the original drafts. Audit unanimous inclusions/exclusions as well as disagreements. No reviewed or adjudicated status is claimed here.
''',encoding='utf8')
queue=[]
for r in rows:
 if r['eligibility']['binary_task']!='include' or r['quality']['flags']:
  queue.append({'case_id':r['case_id'],'case_name':source[r['case_id']]['case_name'],'decision':r['eligibility']['binary_task'],'reasons':r['eligibility']['reasons'],'flags':r['quality']['flags'],'notes':r['quality']['notes'],'source_url':source[r['case_id']]['source_url']})
dump(OUT/'review_queue.json',{'status':'Prioritized human-review queue, not completed adjudication','all_records_need_human_review':True,'priority_cases':queue})
qtable=['| Case | Decision | Reasons / flags | Notes |','|---|---|---|---|']
for q in queue:
 qtable.append('| '+' | '.join([q['case_id'],q['decision'],', '.join(q['reasons']+q['flags']),q['notes'].replace('|','/').replace('\n',' ')])+' |')
(OUT/'review_queue.md').write_text('# Prioritized Batch C review\n\nAll 168 records still require human review. This queue prioritizes uncertain eligibility, exclusions, case families, partial source text and multiple-party/order structure. A flag does not necessarily exclude a case.\n\n'+'\n'.join(qtable)+'\n',encoding='utf8')
table=['| Case ID | Case | Decision | Disposition | Binary | Notes |','|---|---|---|---|---|---|']
for r in rows:
 note='; '.join(r['eligibility']['reasons'])+'; '+r['quality']['notes']
 if r['case_id'] in overlap:note+='; calibration exposure: training-only'
 vals=[r['case_id'],source[r['case_id']]['case_name'],r['eligibility']['binary_task'],r['outcome']['appellate_disposition'],str(r['outcome']['binary_label']) if r['outcome']['binary_label'] is not None else 'null',note.strip('; ')]
 table.append('| '+' | '.join(v.replace('|','/').replace('\n',' ') for v in vals)+' |')
(OUT/'case_table.md').write_text('# Case-level audit\n\n'+'\n'.join(table)+'\n',encoding='utf8')
families=[{'case_ids': ['NY-4389907', 'NY-6235554'], 'relation': 'Duplicate-source versions of Peña; same decision date, parties, appealed order and substantive opinion.', 'provisional_handling': 'Retain NY-4389907; exclude NY-6235554. Confirm canonical selection during team review.'}, {'case_ids': ['NY-4304286', 'NY-6207931'], 'relation': 'Wintermute duplicate versions; December 31, 2015 decision, same May 9, 2014 judgment and evidentiary new-trial reasoning.', 'provisional_handling': 'Prefer earlier B ID NY-4304286 subject to team eligibility review. C NY-6207931 remains review because merits/procedural scope is uncertain; regardless of scope resolution do not count it as a separate observation.'}, {'case_ids': ['NY-4306330', 'NY-6111859'], 'relation': 'Seferagic duplicate versions; March 21, 2014 decision, same November 30, 2012 order, parties and wet-floor notice reasoning.', 'provisional_handling': 'Prefer earlier B ID NY-4306330 subject to adjudication; exclude C NY-6111859 as duplicate.'}, {'case_ids': ['NY-4387315', 'NY-6235219'], 'relation': 'Lingenfelter duplicate versions; April 28, 2017 decision, same May 9, 2016 order and snowplowing-contract reasoning.', 'provisional_handling': 'Prefer earlier B ID NY-4387315 subject to adjudication; exclude C NY-6235219 as duplicate.'}, {'case_ids': ['NY-4552386'], 'relation': 'Rozier source is Appeal No. 2 (judgment affirmed); memorandum also addresses Appeal No. 1 dismissed as subsumed.', 'provisional_handling': 'Link companion appeal if present before splitting. Do not miscode this Appeal No. 2 as mixed. Property ownership remains review.'}]
dump(OUT/'case_family_notes.json',{'status':'Source-read observations, not exhaustive cross-round deduplication','families':families})
text=f'''# Yinkui — Batch C annotation submission

Completed November 3, 2026: **168/168 cases across all 34 chunks**. Full validation passed with no missing/extra IDs or structural/evidence errors. All records are **LLM drafts pending human review**, not gold labels.

| Provisional decision | Cases |
|---|---:|
| Include in binary task | {elig.get('include',0)} |
| Review eligibility | {elig.get('review',0)} |
| Exclude from binary task | {elig.get('exclude',0)} |

The included cases contain **{classes.get('0',0)} affirmed (0)** and **{classes.get('1',0)} reversed/vacated (1)**. Excluded/review cases have null binary labels. These are draft annotation counts, not the final study sample or model performance.

## Files for teammates

- [annotations.jsonl](annotations.jsonl): complete submission, one record per case including exclusions/reviews.
- [case_table.md](case_table.md): readable table of all 168 decisions and notes.
- [review_queue.md](review_queue.md) / [review_queue.json](review_queue.json): prioritized scope/exclusion/family review; all records still need human review.
- [annotations.validation.json](annotations.validation.json): schema, exact quotation offsets, source hashes, references, all-passages coverage and expected IDs.
- [annotations.summary.json](annotations.summary.json): machine-readable counts.
- [case_family_notes.json](case_family_notes.json): known duplicate/companion warnings.
- [revisions.json](revisions.json): seven LLM self-audit corrections; original v1 drafts retained, v2 records explicitly identify predecessors. The audit changed one inclusion to scope review and removed two duplicate inclusions; all changes are documented.
- `drafts/`, `chunks/`, `authoring/`: original drafts, selected records, per-chunk checks and actual manual semantic selections.
- [run_manifest.json](run_manifest.json), [provenance.json](provenance.json), [independent_freeze.json](independent_freeze.json), `prompts_used/`: completion, versions, input/output hashes and exposure record.
- [human_review_log.md](human_review_log.md): pending; no fabricated human sign-off.

## Procedure and interpretation

Same full-reading, codebook 1.0.0 and schema procedure as Yinkui's A pass. Every supplied passage was read, with exact quotes for scope, disposition, issues and factual features. No peer C annotations or external case facts were consulted, and no annotation API or subagents were used. The repository decision log still contains no substantive codebook freeze; disputed boundaries remain explicitly unresolved.

Prior calibration exposure in C: {', '.join(overlap) if overlap else 'none'}. Affected records disclose this exposure. Keep them training-only and report them separately from fresh independent agreement.

Labels describe the **current appellate disposition**, not plaintiff success or prediction of an unseen lawsuit. A whole appealed order may be affirmed even when different parties obtained different relief below. Outcome beneficiaries and trial actions are recorded separately.

The {elig.get("review",0)} unresolved cases primarily concern private/public boundaries, unspecified fall mechanisms, and procedural-versus-merits scope. The {elig.get("exclude",0)} exclusions include public sites, nonqualifying incidents, procedural/insurance decisions and three duplicate-source records. Gautier has a complete majority disposition/reasoning but an announced dissent absent from the supplied snapshot; its inclusion carries a text-completeness flag. All excluded and unresolved records remain in the audit file.

Four duplicate pairs were confirmed from original source opinions. Peña appears twice in C: provisionally retain NY-4389907 and exclude NY-6235554. Seferagic NY-6111859 and Lingenfelter NY-6235219 duplicate earlier B sources and are excluded here. Wintermute NY-6207931 also duplicates B but stays in review because its subject scope is uncertain; the codebook requires uncertain scope to remain review. None of these four C duplicate records belongs in a distinct training/evaluation sample. Retaining an earlier B ID does not approve its eligibility or label. See case_family_notes.json for canonical IDs and the Rozier companion-appeal warning. This is not an exhaustive cross-round family audit.

## Next steps

1. Freeze the other two independent C submissions before cross-comparison. Do not overwrite anyone's original draft.
2. Compare the three C files; review disagreements against original opinions, plus a sample of unanimous inclusions and exclusions. Hayden can lead actual human adjudication.
3. Resolve scope and labels, verify useful features and evidence, and record reviewer/date/reason in the consolidated C decision log. Do not automatically treat majority agreement as human gold.
4. Only after review, add eligible C cases to the study with one record per unique case and related cases grouped across splits. Reuse A's evaluation/masking procedure and maintain calibration cases in training only.

Do not concatenate three reviewer files as if they contained different cases. Annotation summaries, legal findings, selected outcome evidence and outcome cues may reveal labels; they are **not automatically approved predictive features or test masking spans**. The published opinion's reasoning may itself reveal the disposition. Preserve the full/masked/random-removal controls when modeling resumes.

## Revalidate (from repository root)

```sh
python annotation/scripts/validate_annotations.py annotation/submissions/yinkui/batches/C/annotations.jsonl --expected annotation/batches/C/manifest.json --report annotation/submissions/yinkui/batches/C/annotations.validation.json
```

Expected warnings are `LLM draft: not human gold` for all 168 and unresolved-review warnings for {elig.get("review",0)}. The validator does not assess legal correctness. `authoring/finalize_submission.py` packages selected records without inferring labels. Per-chunk authoring and audit-revision scripts intentionally refuse draft overwrites; do not rerun them to replace existing annotations.
'''
(OUT/'SUMMARY.md').write_text(text,encoding='utf8')
(OUT/'README.md').write_text(text,encoding='utf8')
freeze={'reviewer_id':'yinkui','round':'C','frozen_date_local':'2026-11-03','complete_records':168,'independence':'No peer C production labels read; prior calibration exposure logged.','human_review_completed':False,'hash_normalization':provenance['hash_normalization'],'sha256':{str(p.relative_to(OUT)).replace('\\','/'):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='independent_freeze.json' and '__pycache__' not in p.parts and p.suffix!='.pyc'}}
dump(OUT/'independent_freeze.json',freeze)
print(json.dumps(summary,indent=2))
print(f'Full validation passed; {len(queue)} priority review records; v1/v2 lineage and all 168 checkpoint records match.')
