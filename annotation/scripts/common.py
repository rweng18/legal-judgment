"""Standard-library schema, provenance and consistency checks."""
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ISSUES=['duty','creation_of_hazard','actual_notice','constructive_notice','recurring_condition','open_and_obvious',
        'trivial_defect','storm_in_progress','causation_identification','assumption_of_risk','comparative_fault',
        'out_of_possession_landlord','contractor_duty','code_violation','expert_evidence','spoliation',
        'procedural_issue','labor_law','other']

def read_records(path):
    text=Path(path).read_text(encoding='utf-8-sig').strip()
    if not text:return []
    if text.startswith('['):
        rows=json.loads(text)
    else:
        try:
            value=json.loads(text)
            rows=[value] if isinstance(value,dict) else value
        except json.JSONDecodeError:
            rows=[json.loads(line) for line in text.splitlines() if line.strip()]
    if not isinstance(rows,list) or not all(isinstance(r,dict) for r in rows):raise ValueError('Expected JSON objects or an array of objects.')
    return rows

def dump(path,obj):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def write_jsonl(path,rows):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf8')

def type_matches(value,t):
    return {'object':isinstance(value,dict),'array':isinstance(value,list),'string':isinstance(value,str),
            'boolean':type(value) is bool,'integer':type(value) is int,'number':type(value) in (int,float),'null':value is None}[t]

def schema_errors(value,schema,path='$'):
    errors=[]
    if 'const' in schema and (value!=schema['const'] or type(value)!=type(schema['const'])):errors.append(f'{path}: wrong constant')
    if 'enum' in schema and not any(value==v and type(value)==type(v) for v in schema['enum']):errors.append(f'{path}: value outside allowed enum')
    if 'type' in schema:
        kinds=schema['type'] if isinstance(schema['type'],list) else [schema['type']]
        if not any(type_matches(value,t) for t in kinds):return errors+[f'{path}: wrong type; expected {kinds}']
    if isinstance(value,dict):
        for key in schema.get('required',[]):
            if key not in value:errors.append(f'{path}.{key}: required')
        props=schema.get('properties',{})
        for key,v in value.items():
            if key in props:errors+=schema_errors(v,props[key],f'{path}.{key}')
            elif schema.get('additionalProperties') is False:errors.append(f'{path}.{key}: unexpected property')
    if isinstance(value,list):
        if len(value)<schema.get('minItems',0):errors.append(f'{path}: too few items')
        if 'items' in schema:
            for i,v in enumerate(value):errors+=schema_errors(v,schema['items'],f'{path}[{i}]')
    if isinstance(value,str) and len(value)<schema.get('minLength',0):errors.append(f'{path}: empty string')
    return errors

def check_record(r,source):
    errors=[];warnings=[];offsets=[]
    if source is None:return ['Unknown case ID'],warnings,offsets
    if r['text_sha256']!=source['text_sha256']:errors.append('Source hash mismatch')
    if hashlib.sha256(source['text'].encode()).hexdigest()!=source['text_sha256']:errors.append('Corrupted canonical source')
    passages={p['passage_id']:p for p in source['passages']};ev={}
    for e in r['evidence']:
        eid=e['evidence_id'];pid=e['passage_id']
        if eid in ev:errors.append(f'Duplicate evidence ID {eid}')
        ev[eid]=e
        if pid not in passages:errors.append(f'Unknown passage {pid}');continue
        p=passages[pid];quote=e['quote'];local=p['text'].find(quote)
        if local<0:errors.append(f'{eid}: quotation does not occur exactly in {pid}');continue
        if p['text'].find(quote,local+1)>=0:errors.append(f'{eid}: quotation ambiguous within passage; use a longer quote');continue
        offsets.append({'evidence_id':eid,'passage_id':pid,'start':p['start']+local,'end':p['start']+local+len(quote)})
    def refs(node):
        if isinstance(node,dict):
            for k,v in node.items():
                if k in ('evidence_ids','property_evidence','incident_evidence','scope_evidence','disposition_evidence'):
                    for eid in v:
                        if eid not in ev:errors.append(f'Unknown evidence reference {eid}')
                else:refs(v)
        elif isinstance(node,list):
            for item in node:refs(item)
    refs(r)
    e=r['eligibility'];o=r['outcome'];q=r['quality'];run=r['run']
    try:
        if datetime.fromisoformat(run['annotated_at'].replace('Z','+00:00')).tzinfo is None:errors.append('annotated_at requires a timezone')
    except ValueError:errors.append('annotated_at must be an ISO datetime with timezone')
    if e['binary_task']=='include':
        if e['scope']!='in_scope' or e['property_status']!='private' or e['property_basis']=='insufficient':errors.append('Included case lacks in-scope/private support')
        if e['fall_type'] not in ('slip','trip','slip_or_trip') or e['merits']!='substantive':errors.append('Included case lacks slip/trip substantive merits')
        label={'affirmed':0,'reversed':1,'vacated':1}.get(o['appellate_disposition'])
        if label is None or o['binary_label']!=label:errors.append('Included case has inconsistent disposition/binary label')
        if e['reasons'] or q['needs_review']:errors.append('Include conflicts with exclusion/review flags')
        for key in ('property_evidence','incident_evidence','scope_evidence'):
            if not e[key]:errors.append(f'Included case missing {key}')
        if not o['disposition_evidence']:errors.append('Included case missing disposition evidence')
        if not any(ev.get(x,{}).get('statement_status')=='current_disposition' for x in o['disposition_evidence']):errors.append('Disposition evidence needs a current_disposition statement')
        for order in o['orders']:
            if {'affirmed':0,'reversed':1,'vacated':1}.get(order['appellate_disposition'])!=label:errors.append('Included whole disposition conflicts with a per-order outcome')
            if not order['evidence_ids']:errors.append('Included order needs supporting evidence')
    else:
        if o['binary_label'] is not None:errors.append('Excluded/review cases must have null binary label')
        if not e['reasons']:errors.append('Excluded/review case needs a reason')
    if e['binary_task']=='review' and not q['needs_review']:errors.append('Review case must set needs_review=true')
    if e['scope']=='uncertain' and e['binary_task']!='review':errors.append('Uncertain scope must remain in review')
    if o['appellate_disposition'] in ('mixed','modified','appeal_dismissed','remand_only','other','unclear') and o['binary_label'] is not None:errors.append('Nonbinary disposition has binary label')
    if o['multiple_orders']!=(len(o['orders'])>1):errors.append('multiple_orders does not match orders list')
    topics=[i['topic'] for i in r['legal_issues']]
    if Counter(topics)!=Counter(ISSUES):errors.append('legal_issues must contain each of the 19 topics exactly once')
    for issue in r['legal_issues']:
        if issue['discussion'] in ('raised_only','court_addressed') and (not issue['evidence_ids'] or not issue['finding'].strip()):errors.append(f'{issue["topic"]}: discussed issue needs finding and evidence')
        if issue['discussion']=='not_discussed' and (issue['finding'] or issue['evidence_ids']):errors.append(f'{issue["topic"]}: not_discussed must have empty finding/evidence')
    for item in r['evidence_discussed']:
        if not item['evidence_ids']:errors.append('Evidence type needs supporting quotation')
    for item in r['outcome_cues']:
        if not item['evidence_ids']:errors.append('Outcome cue needs supporting quotation')
    section_ids=[s['passage_id'] for s in r['text_sections']]
    if Counter(section_ids)!=Counter(list(passages)):errors.append('text_sections must cover every passage exactly once')
    if e['binary_task']=='include' and not r['facts']['evidence_ids']:errors.append('Included case needs factual evidence')
    if run['review_status']!='llm_draft' and (not run['human_reviewer_id'] or not run['review_note'].strip()):errors.append('Human/adjudicated status requires human identity and review note')
    if run['review_status']=='llm_draft' and run['human_reviewer_id'] is not None:errors.append('LLM draft must not claim human review')
    if run['review_status']=='llm_draft':warnings.append('LLM draft: not human gold')
    if q['needs_review']:warnings.append('Unresolved review flag')
    return errors,warnings,offsets

def validate(rows,sources,expected=None,partial=False):
    schema=json.loads((ROOT/'schema'/'annotation.schema.json').read_text(encoding='utf8'))
    errors=[];warnings=[];offsets=[];seen=set()
    for i,r in enumerate(rows):
        cid=r.get('case_id',f'row-{i}')
        if cid in seen:errors.append(f'{cid}: duplicate case ID in submission')
        seen.add(cid);se=schema_errors(r,schema)
        if se:errors += [f'{cid}: {x}' for x in se];continue
        es,ws,os=check_record(r,sources.get(cid));errors += [f'{cid}: {x}' for x in es]
        warnings += [f'{cid}: {x}' for x in ws];offsets.append({'case_id':cid,'evidence_offsets':os})
    missing=sorted(set(expected or [])-seen);extra=sorted(seen-set(expected or seen))
    if missing and not partial:errors.append(f'Missing case IDs: {missing}')
    if extra:errors.append(f'Unexpected case IDs: {extra}')
    return {'passed':not errors,'records':len(rows),'missing_ids':missing,'extra_ids':extra,'errors':errors,
            'warnings':warnings,'evidence_offsets':offsets,
            'limitation':'Structural and quotation checks only; a valid quotation does not establish semantic correctness.'}

