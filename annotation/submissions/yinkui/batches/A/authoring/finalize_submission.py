"""Validate and package the selected, manually authored records; never infer labels."""
import hashlib,json,sys,subprocess,shutil
from pathlib import Path
from collections import Counter
OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import read_records,validate,dump,write_jsonl

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
source={r['case_id']:r for r in read_records(ROOT/'source/cases.jsonl')}
expected=json.loads((ROOT/'batches/A/manifest.json').read_text(encoding='utf8'))['case_ids']
files=[OUT/f'chunks/A_{i:03d}.json' for i in range(1,35)]
assert all(p.is_file() for p in files)
rows=[r for p in files for r in read_records(p)]
check=validate(rows,source,expected)
assert check['passed'],check['errors']
assert len(rows)==len(set(r['case_id'] for r in rows))==169
assert all(r['run']['review_status']=='llm_draft' and r['run']['human_reviewer_id'] is None for r in rows)
assert all(read_records(p)==read_records(OUT/'drafts'/f'{p.stem}.draft-v1.json') for p in files)
assert {r['case_id']:r for r in rows}=={r['case_id']:r for r in read_records(OUT/'checkpoint.jsonl')}
rows=sorted(rows,key=lambda r:r['case_id'])
write_jsonl(OUT/'annotations.jsonl',rows)
dump(OUT/'annotations.validation.json',check)
elig=dict(Counter(r['eligibility']['binary_task'] for r in rows))
classes=dict(Counter(str(r['outcome']['binary_label']) for r in rows if r['eligibility']['binary_task']=='include'))
cal=set(json.loads((ROOT/'calibration/manifest.json').read_text(encoding='utf8'))['case_ids'])
overlap=sorted(cal.intersection(expected))
assert all('Calibration overlap:' in r['run']['review_note'] for r in rows if r['case_id'] in overlap)
summary={'annotated_cases':169,'expected_cases':169,'eligibility':elig,'included_class_counts':classes,'review_status':{'llm_draft':169},'human_review_completed':False,'cross_comparison_performed':False,'prior_calibration_exposure_ids':overlap,'pending_case_ids':[],'note':'Complete independent LLM draft, not an adjudicated dataset or classifier evaluation. Eligibility and class counts remain provisional.'}
dump(OUT/'annotations.summary.json',summary)
inputs=['AGENTS.md','README.md','docs/CODEBOOK.md','docs/CHATGPT_WORKFLOW.md','docs/QUALITY_CONTROL.md','docs/DECISIONS.md','schema/annotation.schema.json','prompts/ANNOTATE_CHUNK.md','batches/A/manifest.json','source/cases.jsonl']
inputs += [f'batches/A/chunks/A_{i:03d}.md' for i in range(1,35)]
provenance={'reviewer_id':'yinkui','round':'A','publication_date_local':'2026-10-21','timezone':'America/New_York','annotation_base_commit':'b8a54a2','packaging_base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT.parent,text=True).strip(),'schema_version':'1.0.0','prompt_version':'1.0.0','model_name':sorted(set(r['run']['model_name'] for r in rows)),'model_version':None,'annotation_time_min':min(r['run']['annotated_at'] for r in rows),'annotation_time_max':max(r['run']['annotated_at'] for r in rows),'method':'Interactive Codex read every supplied passage and authored semantic values and exact evidence selections in per-chunk Python scripts. Helper code serialized and validated those choices. No external model API or subagents used.','peer_batch_A_labels_read':False,'peer_directory_structure_checked':True,'calibration_exposure_ids':overlap,'calibration_exposure_rule':'Previously compared calibration cases are not fresh blinded labels; keep training-only in subsequent experiments.','team_substantive_freeze_pending':True,'human_review_completed':False,'input_sha256':{p:sha(ROOT/p) for p in inputs}}
dump(OUT/'provenance.json',provenance)
promptdir=OUT/'prompts_used';promptdir.mkdir(exist_ok=True)
shutil.copyfile(ROOT/'prompts/ANNOTATE_CHUNK.md',promptdir/'ANNOTATE_CHUNK_v1.0.0.md')
(promptdir/'README.md').write_text('''# Prompt provenance

`ANNOTATE_CHUNK_v1.0.0.md` is a verbatim copy of the repository template used as annotation guidance. It is not an invented transcript of an external model call. The work took place interactively in Codex, with the user authorizing Yinkui’s independent A pass and later completion of the remaining 34 cases before upload.

The instructions, codebook, schema and all 34 source chunks are referenced with hashes in `../provenance.json`. The per-chunk authoring files record the actual selected values and exact quotations. No separate API prompts or responses were generated. No peer production labels were consulted. Earlier calibration exposure is explicitly logged.
''',encoding='utf8')
(OUT/'human_review_log.md').write_text('''# Human review status

Pending. All 169 records are `llm_draft` with null human reviewer IDs. No human eligibility check, adjudication or consensus is claimed. Automated validation checks structure, exact evidence, IDs and coverage; it does not establish semantic correctness.

Before modeling, reviewers should resolve uncertain property/mechanism/procedural boundaries, verify labels and evidence, audit unanimous inclusions/exclusions, and record actual decisions in the shared review log. Preserve these independent drafts when making corrections.
''',encoding='utf8')
table=['| Case ID | Decision | Appellate disposition | Binary | Review notes |','|---|---|---|---|---|']
for r in rows:
 note='; '.join(r['eligibility']['reasons'])
 if r['quality']['notes']:note+='; '+r['quality']['notes']
 if r['case_id'] in overlap:note+='; calibration exposure: training-only'
 table.append('| '+ ' | '.join([r['case_id'],r['eligibility']['binary_task'],r['outcome']['appellate_disposition'],str(r['outcome']['binary_label']) if r['outcome']['binary_label'] is not None else 'null',note.strip('; ').replace('|','/').replace('\n',' ')])+' |')
(OUT/'case_table.md').write_text('# Case-level submission audit\n\n'+'\n'.join(table)+'\n',encoding='utf8')
(OUT/'SUMMARY.md').write_text(f'''# Yinkui — partition A independent annotation submission

Completed October 21, 2026: **169/169 unique cases**, all 34 chunks, no missing IDs. All records are **LLM drafts**, pending human review and team adjudication.

| Provisional eligibility | Cases |
|---|---:|
| Include in binary task | {elig.get('include',0)} |
| Review unresolved eligibility | {elig.get('review',0)} |
| Exclude from binary task | {elig.get('exclude',0)} |

Among currently included cases: **{classes.get('0',0)} affirmed (0)** and **{classes.get('1',0)} reversed/vacated (1)**. These are annotation counts, not final sample counts or model metrics.

## Files

- [annotations.jsonl](annotations.jsonl): one record per case, including excluded and unresolved cases.
- [annotations.validation.json](annotations.validation.json): full-manifest validation; passed with no missing/extra IDs or validation errors. LLM-draft and unresolved-review warnings are expected.
- [case_table.md](case_table.md): every case, provisional decision, outcome and uncertainty notes.
- [annotations.summary.json](annotations.summary.json), [progress.json](progress.json): machine-readable counts and completion status.
- `chunks/` and `drafts/`: 34 selected chunks and preserved original drafts; no draft overwrites.
- `authoring/`: semantic selections made after reading each full opinion, plus serialization/validation helpers.
- [provenance.json](provenance.json), `prompts_used/`, [independent_freeze.json](independent_freeze.json): instructions, source/output hashes and exposure record.
- [human_review_log.md](human_review_log.md): explicitly pending, not a fabricated review.

## Independence and remaining review

No peer batch-A annotations were read or cross-compared. Repository directory listings were inspected to match the reviewer-folder layout. The source, codebook and schema were preserved. Initial version 1.0.0 is used; the shared decision log still says substantive team freeze is pending.

Previously annotated/compared calibration cases in this submission: {', '.join(overlap)}. Their records disclose this exposure. Keep them training-only and separate them when reporting fresh independent agreement.

Resolve property-boundary, institution-ownership, unclear fall mechanism and procedural-versus-merits cases before claiming a final eligible sample. The original 506-candidate prescreen is not proof of eligibility. Some decisions use only the phrase “defendant’s building”; these remain review cases where private ownership or context is insufficient. Jury-instruction and product/service-liability boundaries also require a team decision.

Check companion opinions before splitting: Coreano expressly cites a decision issued together, and Sodhi discusses companion appeals. Preserve both records in the audit but group related litigation for evaluation; do not count multiple opinions as independent evidence without checking.

Next: freeze the other reviewers’ A submissions, compare the independent files, and record human adjudication. Use one resolved record per case for an A-only MVP. Do not concatenate reviewer outputs into a larger case dataset or use outcome/issue/evidence annotations as ordinary predictive inputs.

## Revalidate

From the repository root:

```sh
python annotation/scripts/validate_annotations.py annotation/submissions/yinkui/batches/A/annotations.jsonl --expected annotation/batches/A/manifest.json --report annotation/submissions/yinkui/batches/A/annotations.validation.json
```

`authoring/finalize_submission.py` packages existing selected chunks and validates them; it does not infer labels. Original per-chunk authoring scripts refuse to overwrite existing drafts.
''',encoding='utf8')
freeze={'reviewer_id':'yinkui','round':'A','frozen_date_local':'2026-10-21','complete_records':169,'independence':'No peer production labels read; calibration exposure logged in provenance.','human_review_completed':False,'sha256':{str(p.relative_to(OUT)).replace('\\','/'):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='independent_freeze.json' and '__pycache__' not in p.parts and p.suffix!='.pyc'}}
dump(OUT/'independent_freeze.json',freeze)
print(json.dumps(summary,indent=2))
print('Full validation passed; drafts preserved; all 169 checkpoint records match selected chunks.')
