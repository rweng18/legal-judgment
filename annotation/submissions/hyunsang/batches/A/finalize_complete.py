from assemble import *
from collections import Counter
import zipfile
rows=[json.loads(x) for x in (BASE/'annotations.jsonl').read_text().splitlines()]
manifest=json.loads((ROOT/'batches/A/manifest.json').read_text());expected=manifest['case_ids']
assert len(rows)==169 and len({r['case_id'] for r in rows})==169 and set(expected)=={r['case_id'] for r in rows}
assert all(r['run']['review_status']=='llm_draft' and r['run']['human_reviewer_id'] is None for r in rows)
for i in range(1,35):
 chunk=f'A_{i:03d}';assert (BASE/f'drafts/{chunk}.draft-v1.json').is_file()
 selected=json.loads((BASE/f'chunks/{chunk}.json').read_text());assert all(r['input_chunk_id']==chunk for r in selected)
 assert json.loads((BASE/f'chunks/{chunk}.validation.json').read_text())['passed']
 # Evidence refinements must not change the substantive labels authored this turn.
 if i>=18:
  initial=json.loads((BASE/f'drafts/{chunk}.draft-v1.json').read_text())
  for old,new in zip(initial,selected):
   for k in ['eligibility','facts','legal_issues','evidence_discussed','text_sections','quality']:assert old[k]==new[k],(chunk,k)
   for k in ['appellate_disposition','binary_label','multiple_orders','favors']:assert old['outcome'][k]==new['outcome'][k]
counts=Counter(r['eligibility']['binary_task'] for r in rows);binary=Counter(r['outcome']['binary_label'] for r in rows if r['eligibility']['binary_task']=='include')
validation=json.loads((BASE/'annotations.validation.json').read_text());assert validation['passed'] and not validation['missing_ids'] and not validation['extra_ids'] and not validation['errors']
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
annotation_hash=hashlib.sha256((BASE/'annotations.jsonl').read_bytes()).hexdigest()
(BASE/'SUMMARY.md').write_text(f'''# hyunsang — complete independent A submission

169/169 source IDs, A_001–A_034. No pending chunks. Selected output: annotations.jsonl.

| Decision | Count |
|---|---:|
| Include | {counts['include']} |
| Exclude | {counts['exclude']} |
| Review | {counts['review']} |
| Total | 169 |

Included binary labels: affirmed 0 = {binary[0]}; reversed/vacated 1 = {binary[1]}. These are annotation counts, not classifier results.

Every supplied opinion passage was read in full before its chunk was labeled. Each original draft-v1 was saved before validation; revisions preserve earlier drafts and supersedes links. Every selected chunk passes, and the complete merged output passes without partial mode: 169 unique expected IDs; zero missing/extra IDs and validation errors; source hashes, evidence offsets, schema, topics, passage coverage and contradictions checked.

All 169 records are llm_draft. No human review or adjudication is claimed. The 24 review decisions retain null binary labels; all exclusions also retain null labels. Every record, including 132 inclusions, still requires the appropriate human checks before it can be called gold. The summary script's seeded audit IDs and proposed period counts are unperformed review candidates, not completed audits or approved evaluation splits.

Source snapshot: {commit}. Schema/prompt: initial 1.0.0; DECISIONS.md records no substantive team freeze. Actual session model name: GPT-6; unobservable snapshot version null. No API annotation calls, extra agents, training or external case research.

No peer submission, peer summary or comparison file was read. No peer comparison/consolidation was performed. The calibration phase was not rerun. Historical calibration discussions were visible in conversation context; they are not fresh blinded examples. NY-5992200 is specifically marked for that prior context exposure. Original exact user instructions and applied shared templates are in prompts_used/.

Evidence precision: exact narrow controlling-disposition quotations are separate from retained broad passage-level evidence. Broad passages may mix allegations, testimony, history and findings; their statement_status is therefore unclear rather than falsely calling the entire passage a court finding. Human review must check which exact words support each substantive field; genuine quotation matching alone does not prove the interpretation. Explicitly selected indirect-reasoning cues and literal repeated rulings are retained for diagnostic masking audit, not automatic model inputs.

Three assistant-evidence-refinement attempts encountered validation failures while narrowing quotations; failed intermediate drafts were preserved. The selected final files all pass. No eligibility/outcome label was changed by quotation or cue refinement. Earlier source-based corrections are documented in corrections.md. Broad evidence and the conservative private-boundary / mechanism decisions deserve human attention.

The family note for Coreano identifies related but distinct appellate decisions. Two-order decisions and ancillary appellate motions are described in their records; do not treat family membership as independent cases for future splits.

Output SHA-256: {annotation_hash}.

GitHub has not been updated by this run. This is the reviewer's independent draft submission for later authorized upload and team review.
''')
(BASE/'human_review_log.md').write_text('# Human review pending\n\nAll 169 records remain llm_draft, with human_reviewer_id null. No person has independently reviewed these annotations during this run. Assistant source reading, correction and validation are not human review. The 24 eligibility review flags are distinct from the human-review requirement applying to all records. Suggested audit IDs in annotations.summary.json have not been audited.\n')
for name,selection in [('case_review_table.md',rows),('review_queue.md',[r for r in rows if r['eligibility']['binary_task']=='review']),('exclusions.md',[r for r in rows if r['eligibility']['binary_task']=='exclude'])]:
 text='# '+name.replace('_',' ').replace('.md','')+'\n\n| ID | Case | Decision | Outcome | Reasons / notes |\n|---|---|---|---|---|\n'
 for r in selection:
  note='; '.join(r['eligibility']['reasons'])+' '+r['quality']['notes']
  text+='| '+' | '.join(str(v).replace('|','/').replace('\n',' ') for v in [r['case_id'],SOURCES[r['case_id']]['case_name'],r['eligibility']['binary_task'],r['outcome']['appellate_disposition'],note])+' |\n'
 (BASE/name).write_text(text)
# Keep the initial checkpoint hash inventory as an explicitly historical file.
old=BASE/'checkpoint_hashes.json'
if old.exists() and not (BASE/'checkpoint_85_hashes.json').exists():old.rename(BASE/'checkpoint_85_hashes.json')
dump(BASE/'progress.json',dict(status='complete_llm_draft',expected_cases=169,completed_cases=169,pending_cases=0,completed_chunks=[f'A_{i:03d}' for i in range(1,35)],pending_ids=[],next_chunk=None,counts=dict(counts),included_binary_counts=dict(binary),validation_passed=True,human_reviewed_cases=0,peer_outputs_read=False,source_commit=commit,annotations_sha256=annotation_hash))
scope=BASE/'prompts_used/session_scope.md';scope.write_text(scope.read_text()+'\n## Continuation instruction\n\nExact user instruction: 나머지도 해줘\n\nA_018–A_034 completed in continuation. Evidence/cue refinements preserved drafts and semantic labels. No separate model API calls or peer exposures.\n')
freeze={str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(BASE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='independent_freeze.json'}
dump(BASE/'independent_freeze.json',dict(status='complete_independent_llm_draft',source_commit=commit,annotations_sha256=annotation_hash,case_count=169,peer_outputs_read=False,human_reviewed_count=0,files=freeze))
output=ROOT.parent/'hyunsang_A_169_independent.zip'
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
 for folder in [BASE,ROOT/'docs',ROOT/'schema',ROOT/'prompts',ROOT/'scripts',ROOT/'batches/A']:
  for p in sorted(folder.rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts:z.write(p,Path('annotation')/p.relative_to(ROOT))
 for p in [ROOT/'AGENTS.md',ROOT/'README.md']:z.write(p,Path('annotation')/p.relative_to(ROOT))
 source=''.join(json.dumps(SOURCES[cid],ensure_ascii=False)+'\n' for cid in expected)
 z.writestr('annotation/source/cases.jsonl',source)
 z.writestr('READ_ME_FIRST.md',(BASE/'SUMMARY.md').read_text())
with zipfile.ZipFile(output) as z:
 assert z.testzip() is None
 assert all('/becca/' not in n and '/yinkui/' not in n and '/comparison/' not in n for n in z.namelist())
print(json.dumps(dict(output=str(output),bytes=output.stat().st_size,records=169,counts=dict(counts),binary=dict(binary),validation_passed=True),ensure_ascii=False))
