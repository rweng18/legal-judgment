from assemble import *
from collections import Counter
rows=[json.loads(x) for x in (BASE/'checkpoint.jsonl').read_text().splitlines()]
counts=Counter(r['eligibility']['binary_task'] for r in rows)
source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
user='''`https://github.com/rweng18/legal-judgment`의 `annotation/AGENTS.md`와 공통 지침을 읽고, reviewer `hyunsang`으로 A 169건을 독립 라벨링해줘. 다른 reviewer의 제출물·요약·비교 결과는 읽지 마. 12건 캘리브레이션은 이미 제출했으니 반복하지 말고, A_001부터 묶음별로 전문 읽기 → 라벨링 → 초안 보존 → 검증 → 진행 상황 저장 순서로 진행해줘.

첨부한 텍스트를 참고하고, 우리가 "그래프 해석 답안 작성"에서 했던 작업을 반복하는걸로 알고 있어 맞는지 확인해주고 같이 작업해보자'''
(BASE/'prompts_used/session_scope.md').write_text('# Exact user instruction\n\n'+user+'\n\n# Execution provenance\n\nLocal assistant read the common instructions and source chunks directly in this conversation. No API model calls, no additional agents, no peer annotations or comparisons were read. Per-chunk prompt files preserve the applied shared templates with reviewer/chunk substitutions; they are not a claim of separate model calls. Actual model identity available in session: GPT-6; snapshot unavailable, recorded null. Original initial model drafts saved before validation/correction. No human review performed.\n\nThe attachment transcript was read from its supplied local path. Its 09:29–10:05 exchange confirms the same 12-case process extended to all A cases independently. The calibration phase was not repeated.\n\nPreviously discussed calibration examples appear in conversation context and are not fresh blinded examples. No previous automated labeling files were opened; labels here were generated from each current supplied opinion. Exposure to historical conversation cannot be undone and should be considered in later agreement analysis. No peer-comparison or group-consensus claim is made.\n')
(BASE/'human_review_log.md').write_text('# Human review status\n\nIndependent human review pending for every record. No human_reviewed or adjudicated status has been assigned. Local structural and quotation checks and assistant source-based corrections do not count as human review.\n')
head='''# Partial independent A checkpoint — hyunsang

This is not a completed 169-case submission. Completed chunks: A_001–A_017 (85 cases). Remaining: A_018–A_034 (84 cases). Next input: batches/A/chunks/A_018.md.

Every completed chunk was read in full, independently labeled, saved as draft-v1, validated, and merged into the partial checkpoint. No peer submissions, summaries or comparison results were read. No calibration rerun, training, external case research, API annotations or extra agents.

Schema/prompt: 1.0.0, initial version; DECISIONS.md contains no substantive team freeze. Model: GPT-6; snapshot null. All records llm_draft; human reviewer null. See prompts_used/session_scope.md for exposure caveat and exact user instructions.

'''
head+=f'Counts: {dict(counts)}. Included binary outcomes: {dict(Counter(r["outcome"]["binary_label"] for r in rows if r["eligibility"]["binary_task"]=="include"))}.\n\n'
head+='Validation: every selected chunk passes; checkpoint passes explicitly partial validation with 84 missing IDs, no duplicates/extras or errors. Passing validation is structural/quotation consistency only, not legal accuracy. Broad passage evidence in some records includes multiple statement types; prioritize semantic/statement-status checking during human review.\n\nSource commit: '+source_commit+'\n\nCorrections preserve draft-v1 and identify superseded files; see corrections.md. checkpoint.jsonl is the partial selected output; do not rename it annotations.jsonl until complete manifest coverage is validated.\n'
(BASE/'SUMMARY.md').write_text(head)
queue='| Case ID | Case | Decision | Outcome | Reason / attention |\n|---|---|---|---|---|\n'
for r in rows:
 s=SOURCES[r['case_id']];reason='; '.join(r['eligibility']['reasons'])
 if r['eligibility']['binary_task']!='include':reason+=' — '+r['quality']['notes']
 queue+=f'| {r["case_id"]} | {s["case_name"].replace("|","/")} | {r["eligibility"]["binary_task"]} | {r["outcome"]["appellate_disposition"]} | {reason.replace("|","/")} |\n'
(BASE/'case_review_table.md').write_text('# Checkpoint case table — all records require human review\n\n'+queue)
status=json.loads((BASE/'progress.json').read_text());status.update(status='partial',next_chunk='A_018',pending_cases=84,counts=dict(counts),source_commit=source_commit);dump(BASE/'progress.json',status)
freeze={str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(BASE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='checkpoint_hashes.json'}
dump(BASE/'checkpoint_hashes.json',dict(source_commit=source_commit,status='partial_85_of_169',files=freeze))
print(dict(records=len(rows),counts=dict(counts),pending=84,next='A_018'))
