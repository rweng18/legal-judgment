"""Package manually authored B records, checking coverage and revision lineage.

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
expected=json.loads((ROOT/'batches/B/manifest.json').read_text(encoding='utf8'))['case_ids']
files=[OUT/f'chunks/B_{i:03d}.json' for i in range(1,35)]
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
assert len(rows)==len({r['case_id'] for r in rows})==169
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
summary={'annotated_cases':169,'expected_cases':169,'eligibility':elig,'included_class_counts':classes,'review_status':{'llm_draft':169},'human_review_completed':False,'cross_comparison_performed':False,'prior_calibration_exposure_ids':overlap,'pending_case_ids':[],'note':'Complete independent LLM draft, not adjudicated data or classifier evaluation. Counts remain provisional.'}
dump(OUT/'annotations.summary.json',summary)
inputs=['AGENTS.md','README.md','docs/CODEBOOK.md','docs/CHATGPT_WORKFLOW.md','docs/QUALITY_CONTROL.md','docs/DECISIONS.md','schema/annotation.schema.json','prompts/ANNOTATE_CHUNK.md','batches/B/manifest.json','source/cases.jsonl']+[f'batches/B/chunks/B_{i:03d}.md' for i in range(1,35)]
provenance={'reviewer_id':'yinkui','round':'B','publication_date_local':'2026-11-03','timezone':'America/New_York','packaging_workspace_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT.parent,text=True).strip(),'schema_version':'1.0.0','prompt_version':'1.0.0','model_name':sorted({r['run']['model_name'] for r in rows}),'model_version':None,'annotation_time_min':min(r['run']['annotated_at'] for r in rows),'annotation_time_max':max(r['run']['annotated_at'] for r in rows),'method':'Interactive Codex read every supplied passage and manually authored each semantic field and exact evidence selection. Scripts serialized, validated, and packaged those selections. No external model API or subagents. Eight source-read self-audit corrections preserved in v2 drafts with explicit supersedes links.','peer_batch_B_labels_read':False,'cross_comparison_performed':False,'calibration_exposure_ids':overlap,'calibration_exposure_rule':'Previously compared calibration cases are not fresh blinded labels; keep training-only.','team_substantive_freeze_pending_in_decision_log':True,'human_review_completed':False,'input_sha256':{p:sha(ROOT/p) for p in inputs},'hash_normalization':'UTF-8 text with universal newlines normalized to LF before SHA-256; canonical source case text_sha256 values unchanged.'}
dump(OUT/'provenance.json',provenance)
dump(OUT/'run_manifest.json',{'reviewer_id':'yinkui','round':'B','completed_chunks':selected,'completed_case_ids':sorted(expected),'pending_case_ids':[],'validation_passed':True,'all_llm_drafts':True})
promptdir=OUT/'prompts_used';promptdir.mkdir(exist_ok=True)
shutil.copyfile(ROOT/'prompts/ANNOTATE_CHUNK.md',promptdir/'ANNOTATE_CHUNK_v1.0.0.md')
(promptdir/'README.md').write_text('''# Prompt provenance

The adjacent prompt is a verbatim copy of the repository template followed as guidance during interactive Codex annotation. It is not an invented API-call transcript. The user authorized completing Yinkui's Batch B using the same procedure as A, then finishing and pushing it on November 3, 2026.

Input instruction/source hashes are in `../provenance.json`. Actual selected fields and quotations are recorded in per-chunk authoring scripts. No external annotation API, subagent, or peer B labels were used. Prior calibration exposure is disclosed per affected record and in provenance.
''',encoding='utf8')
(OUT/'human_review_log.md').write_text('''# Human review status

Pending for all 169 Batch B records. Every selected record is `llm_draft` with null human reviewer ID. Prior human approval of Batch A does not approve Batch B.

The eight revisions in `revisions.json` are LLM self-audit corrections, not independent human review. Validation checks schema, quotes, hashes, references, IDs and passage coverage; it cannot establish semantic correctness.

After all independent B submissions are frozen, compare them and have Hayden/team review the original opinions. Record actual reviewer, date, evidence, eligibility and label decisions in a new reviewed version; retain the original drafts. Audit unanimous inclusions/exclusions as well as disagreements. No reviewed or adjudicated status is claimed here.
''',encoding='utf8')
queue=[]
for r in rows:
 if r['eligibility']['binary_task']!='include' or r['quality']['flags']:
  queue.append({'case_id':r['case_id'],'case_name':source[r['case_id']]['case_name'],'decision':r['eligibility']['binary_task'],'reasons':r['eligibility']['reasons'],'flags':r['quality']['flags'],'notes':r['quality']['notes'],'source_url':source[r['case_id']]['source_url']})
dump(OUT/'review_queue.json',{'status':'Prioritized human-review queue, not completed adjudication','all_records_need_human_review':True,'priority_cases':queue})
qtable=['| Case | Decision | Reasons / flags | Notes |','|---|---|---|---|']
for q in queue:
 qtable.append('| '+' | '.join([q['case_id'],q['decision'],', '.join(q['reasons']+q['flags']),q['notes'].replace('|','/').replace('\n',' ')])+' |')
(OUT/'review_queue.md').write_text('# Prioritized Batch B review\n\nAll 169 records still require human review. This queue prioritizes uncertain eligibility, exclusions, case families, partial source text and multiple-party/order structure. A flag does not necessarily exclude a case.\n\n'+'\n'.join(qtable)+'\n',encoding='utf8')
table=['| Case ID | Case | Decision | Disposition | Binary | Notes |','|---|---|---|---|---|---|']
for r in rows:
 note='; '.join(r['eligibility']['reasons'])+'; '+r['quality']['notes']
 if r['case_id'] in overlap:note+='; calibration exposure: training-only'
 vals=[r['case_id'],source[r['case_id']]['case_name'],r['eligibility']['binary_task'],r['outcome']['appellate_disposition'],str(r['outcome']['binary_label']) if r['outcome']['binary_label'] is not None else 'null',note.strip('; ')]
 table.append('| '+' | '.join(v.replace('|','/').replace('\n',' ') for v in vals)+' |')
(OUT/'case_table.md').write_text('# Case-level audit\n\n'+'\n'.join(table)+'\n',encoding='utf8')
families=[{'case_ids':['NY-6207337','NY-4304440'],'relation':'Duplicate-source versions of Alvarado v Wegmans, December 23, 2015; same January 5 lower order and substantive opinion.','provisional_handling':'Retain NY-6207337; exclude NY-4304440 as duplicate, but preserve both annotation records. Confirm canonical selection in team review.'},{'case_ids':['NY-4855957'],'relation':'Gould caption says Appeal No. 2.','provisional_handling':'Search other round source metadata for companion before splitting; no peer labels consulted.'},{'case_ids':['NY-4665270'],'relation':'Hartnett common memorandum expressly affirms appeals Nos. 1 and 2.','provisional_handling':'Group companion source if present; do not count shared litigation as independent.'},{'case_ids':['NY-10128971'],'relation':'Carmona cites companion 231 AD3d 702 (2024) decided herewith.','provisional_handling':'Currently excluded public tree well; retain family warning for broader analyses.'}]
dump(OUT/'case_family_notes.json',{'status':'Source-read observations, not exhaustive cross-round deduplication','families':families})
text=f'''# Yinkui — Batch B annotation submission

Completed November 3, 2026: **169/169 cases across all 34 chunks**. Full validation passed with no missing/extra IDs or structural/evidence errors. All records are **LLM drafts pending human review**, not gold labels.

| Provisional decision | Cases |
|---|---:|
| Include in binary task | {elig.get('include',0)} |
| Review eligibility | {elig.get('review',0)} |
| Exclude from binary task | {elig.get('exclude',0)} |

The included cases contain **{classes.get('0',0)} affirmed (0)** and **{classes.get('1',0)} reversed/vacated (1)**. Excluded/review cases have null binary labels. These are draft annotation counts, not the final study sample or model performance.

## Files for teammates

- [annotations.jsonl](annotations.jsonl): complete submission, one record per case including exclusions/reviews.
- [case_table.md](case_table.md): readable table of all 169 decisions and notes.
- [review_queue.md](review_queue.md) / [review_queue.json](review_queue.json): prioritized scope/exclusion/family review; all records still need human review.
- [annotations.validation.json](annotations.validation.json): schema, exact quotation offsets, source hashes, references, all-passages coverage and expected IDs.
- [annotations.summary.json](annotations.summary.json): machine-readable counts.
- [case_family_notes.json](case_family_notes.json): known duplicate/companion warnings.
- [revisions.json](revisions.json): eight LLM self-audit corrections; original v1 drafts retained, v2 records explicitly identify predecessors. No eligibility or binary label changed in this audit.
- `drafts/`, `chunks/`, `authoring/`: original drafts, selected records, per-chunk checks and actual manual semantic selections.
- [run_manifest.json](run_manifest.json), [provenance.json](provenance.json), [independent_freeze.json](independent_freeze.json), `prompts_used/`: completion, versions, input/output hashes and exposure record.
- [human_review_log.md](human_review_log.md): pending; no fabricated human sign-off.

## Procedure and interpretation

Same full-reading, codebook 1.0.0 and schema procedure as Yinkui's A pass. Every supplied passage was read, with exact quotes for scope, disposition, issues and factual features. No peer B annotations or external case facts were consulted, and no annotation API or subagents were used. The repository decision log still contains no substantive codebook freeze; disputed boundaries remain explicitly unresolved.

Prior calibration exposure in B: {', '.join(overlap) if overlap else 'none'}. Affected records disclose this exposure. Keep them training-only and report them separately from fresh independent agreement.

Labels describe the **current appellate disposition**, not plaintiff success or prediction of an unseen lawsuit. A whole appealed order may be affirmed even when different parties obtained different relief below. Outcome beneficiaries and trial actions are recorded separately.

The 15 unresolved cases primarily concern private/public boundaries, unspecified fall mechanisms, and procedural-versus-merits scope. The 11 exclusions include public sites, nonqualifying incidents, procedural/insurance decisions and one duplicate-source observation. These remain in the audit file. Langgood has a complete majority disposition/reasoning but an announced dissent absent from the supplied snapshot; its inclusion carries a text-completeness flag.

One known duplicate pair is Alvarado: NY-6207337 retained provisionally and NY-4304440 excluded as duplicate. Check the family notes and all rounds before splitting. This is not an exhaustive cross-round family audit.

## Next steps

1. Freeze the other two independent B submissions before cross-comparison. Do not overwrite anyone's original draft.
2. Compare the three B files; review disagreements against original opinions, plus a sample of unanimous inclusions and exclusions. Hayden can lead actual human adjudication.
3. Resolve scope and labels, verify useful features and evidence, and record reviewer/date/reason in the consolidated B decision log. Do not automatically treat majority agreement as human gold.
4. Only after review, add eligible B cases to the study with one record per unique case and related cases grouped across splits. Reuse A's evaluation/masking procedure and maintain calibration cases in training only.

Do not concatenate three reviewer files as if they contained different cases. Annotation summaries, legal findings, selected outcome evidence and outcome cues may reveal labels; they are **not automatically approved predictive features or test masking spans**. The published opinion's reasoning may itself reveal the disposition. Preserve the full/masked/random-removal controls when modeling resumes.

## Revalidate (from repository root)

```sh
python annotation/scripts/validate_annotations.py annotation/submissions/yinkui/batches/B/annotations.jsonl --expected annotation/batches/B/manifest.json --report annotation/submissions/yinkui/batches/B/annotations.validation.json
```

Expected warnings are `LLM draft: not human gold` for all 169 and unresolved-review warnings for 15. The validator does not assess legal correctness. `authoring/finalize_submission.py` packages selected records without inferring labels. Per-chunk authoring and audit-revision scripts intentionally refuse draft overwrites; do not rerun them to replace existing annotations.
'''
(OUT/'SUMMARY.md').write_text(text,encoding='utf8')
(OUT/'README.md').write_text(text,encoding='utf8')
freeze={'reviewer_id':'yinkui','round':'B','frozen_date_local':'2026-11-03','complete_records':169,'independence':'No peer B production labels read; prior calibration exposure logged.','human_review_completed':False,'hash_normalization':provenance['hash_normalization'],'sha256':{str(p.relative_to(OUT)).replace('\\','/'):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='independent_freeze.json' and '__pycache__' not in p.parts and p.suffix!='.pyc'}}
dump(OUT/'independent_freeze.json',freeze)
print(json.dumps(summary,indent=2))
print(f'Full validation passed; {len(queue)} priority review records; v1/v2 lineage and all 169 checkpoint records match.')
