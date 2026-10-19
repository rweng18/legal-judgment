"""Serialize explicitly authored annotations after full reading; no label inference.

The evidence helper copies only manually selected exact spans from the canonical
source. All interpretations below were written before reading teammate outputs.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import ISSUES, read_records, dump, write_jsonl, validate

SOURCES = {r['case_id']: r for r in read_records(ROOT/'source/cases.jsonl')}
STAMP = datetime.now(timezone(timedelta(hours=-4))).isoformat(timespec='seconds')
RECORDS = []

def case(cid, chunk):
    s = SOURCES['NY-'+str(cid)]
    return {'schema_version':'1.0.0','prompt_version':'1.0.0',
      'case_id':s['case_id'],'text_sha256':s['text_sha256'],'input_chunk_id':chunk,
      'run':{'annotator_id':'yinkui','model_name':'GPT-6 (Codex; exact variant not exposed)',
       'model_version':None,'annotated_at':STAMP,'review_status':'llm_draft',
       'human_reviewer_id':None,'review_note':'Assistant draft for Yinkui. Full source read before teammate outputs. No independent human notes or human review supplied.', 'supersedes':None},
      'legal_issues':[{'topic':t,'discussion':'not_discussed','finding':'','evidence_ids':[]} for t in ISSUES],
      'evidence':[], 'evidence_discussed':[], 'outcome_cues':[],
      'quality':{'needs_review':False,'flags':[],'notes':''}}

def ev(r, p, start, end=None, status='court_finding'):
    text=SOURCES[r['case_id']]['passages'][p-1]['text']
    if end is None:
        quote=start
    else:
        a=text.index(start); b=text.index(end,a)+len(end); quote=text[a:b]
    assert text.count(quote)==1,(r['case_id'],p,quote)
    eid=f'E{len(r["evidence"])+1:03d}'
    r['evidence'].append({'evidence_id':eid,'passage_id':f'P{p:03d}','quote':quote,'statement_status':status})
    return eid

def eligibility(r, fall, prop, incident, merits, *, basis='owned', decision='include', reasons=None, note='', flags=None, property_status='private'):
    r['eligibility']={'scope':{'include':'in_scope','exclude':'out_of_scope','review':'uncertain'}[decision],
      'binary_task':decision,'reasons':reasons or [],'property_status':property_status,
      'property_basis':basis,'fall_type':fall,'merits':'substantive',
      'property_evidence':prop,'incident_evidence':incident,'scope_evidence':merits}
    r['quality']={'needs_review':decision=='review','flags':flags or [],'notes':note}

def outcome(r, disp, favors, appellant, description, trial, evidence):
    r['outcome']={'appellate_disposition':disp,'binary_label':({'affirmed':0,'reversed':1}.get(disp) if r['eligibility']['binary_task']=='include' else None),
      'multiple_orders':False,'favors':favors,'disposition_evidence':[evidence[-1]],
      'orders':[{'description':description,'appellant_role':appellant,'trial_court_action':trial,'appellate_disposition':disp,'evidence_ids':evidence}]}
    r['outcome_cues'].append({'kind':'current_disposition','evidence_ids':[evidence[-1]]})

def facts(r, premises, location, hazards, role, defendants, summary, evidence, date=None):
    r['facts']={'premises_type':premises,'location':location,'hazards':hazards,'injured_role':role,
      'defendant_roles':defendants,'accident_date':date,'factual_summary':summary,'evidence_ids':evidence}

def issue(r, topic, finding, refs, discussion='court_addressed'):
    obj=next(i for i in r['legal_issues'] if i['topic']==topic)
    obj.update(discussion=discussion,finding=finding,evidence_ids=refs)

def material(r, kind, description, refs):
    r['evidence_discussed'].append({'type':kind,'description':description,'evidence_ids':refs})

def sections(r, *types):
    assert len(types)==len(SOURCES[r['case_id']]['passages'])
    r['text_sections']=[{'passage_id':f'P{i:03d}','types':v.split()} for i,v in enumerate(types,1)]

def cue(r, kind, *refs):
    r['outcome_cues'].append({'kind':kind,'evidence_ids':list(refs)})

# CAL_001: Freiser
r=case(5960096,'CAL_001')
h=ev(r,1,'In an action to recover','which denied its motion for summary judgment dismissing the complaint.',status='procedural_history')
d=ev(r,1,'Ordered that the order is reversed','is granted.',status='current_disposition')
f=ev(r,1,'At approximately 12:00 p.m.','alleging that a wet and dangerous condition existed on the floor in the supermarket and caused her accident.',status='allegation')
n=ev(r,2,'The defendant established its prima facie entitlement','nor had actual or constructive notice of it.')
w=ev(r,2,'According to the employee,','the soles of the plaintiffs shoes were wet.',status='testimony_or_record')
p=ev(r,3,'Additionally, the store manager stated','did not give any additional description of the condition.',status='testimony_or_record')
a=ev(r,3,'Contrary to the Supreme Court’s determination,','earlier deposition testimony',status='court_finding')
z=ev(r,4,'Accordingly, the Supreme Court should have granted the defendant’s motion for summary judgment dismissing the complaint.',status='current_disposition')
eligibility(r,'slip',[f],[f],[n])
outcome(r,'reversed','defendant','defendant','September 23, 2010 order','Denied defendant summary judgment dismissing the complaint.',[h,d])
facts(r,'retail','indoor_floor',['water'],'unclear',['owner'],'Plaintiff allegedly slipped on water between the entrance and cash registers of a defendant-owned supermarket on a rainy day. Her later affidavit added mud, footprints and cart tracks.',[f,a],date='2007-08-10')
for t in ['creation_of_hazard','actual_notice','constructive_notice']:
    issue(r,t,'Defendant established prima facie that it neither created the water condition nor had actual or constructive notice; plaintiff did not raise a triable issue.',[n,w,p,a])
issue(r,'procedural_issue','Later affidavit describing muddy water and tracks was treated as an attempt to create a feigned issue inconsistent with deposition testimony.',[a])
material(r,'party_testimony','Plaintiff deposition gave no detail beyond water; later affidavit was rejected as creating a feigned issue.',[p,a])
material(r,'witness_testimony','Employee deposition/affidavit and manager affidavit supported absence of water shortly before the fall and lack of spill reports.',[n,w,p])
sections(r,'procedural_history current_outcome facts','legal_reasoning quoted_precedent facts','legal_reasoning facts','current_outcome legal_reasoning metadata')
cue(r,'repeated_outcome',z);cue(r,'indirect_reasoning',n,a);RECORDS.append(r)

# Jewett: one order with appeals/cross-appeal, all affirmed; merits and indemnity.
r=case(4310325,'CAL_001')
h=ev(r,1,'Appeals and cross appeal','for summary judgment.',status='procedural_history')
d=ev(r,1,'It is hereby ordered that the order so appealed from is unanimously affirmed without costs.',status='current_disposition')
f=ev(r,1,'Memorandum: Plaintiffs commenced','(Burgundy Room).',status='allegation')
a=ev(r,2,'According to plaintiffs,','an icy condition in the parking lot.',status='allegation')
l=ev(r,3,'We reject the contention of RMF Holding','determined by the trier of fact',status='court_finding')
c=ev(r,3,'We further conclude','may be liable as an out-of-possession landlord',status='court_finding')
n=ev(r,4,'Although those defendants demonstrated','noting the gaps in plaintiffs’ proof',status='court_finding')
b=ev(r,4,'Finally, we reject plaintiffs’ contention','plaintiffs failed to raise a triable issue of fact in opposition',status='court_finding')
eligibility(r,'slip',[f],[f],[n,b],note='One order, several appellants and cross-claims. All appealed portions affirmed; mixed practical beneficiaries do not make a mixed appellate disposition.')
outcome(r,'affirmed','both','both','July 2, 2010 omnibus order','Denied RMF Holding/Burgundy Room motions and cross-motions; granted BKV defendants summary judgment.',[h,d])
facts(r,'other','parking_lot',['snow_ice','water'],'unclear',['owner','tenant'],'Plaintiff allegedly slipped on ice in a privately owned plaza parking lot. Plaintiffs alleged that an adjacent restaurant downspout discharged water into the lot where it froze.',[f,a])
issue(r,'creation_of_hazard','Plaintiffs alleged artificial drainage from the restaurant downspout created the ice; the court did not conclusively find creation.',[a],'raised_only')
for t in ['actual_notice','constructive_notice']:
    issue(r,t,'BKV defendants established lack of actual or constructive knowledge of the icy condition and plaintiffs did not raise a triable issue.',[b])
issue(r,'out_of_possession_landlord','Triable issue whether RMF Holding retained control of roof/exterior/structural walls and could remain liable.',[c])
issue(r,'duty','Retained structural control and ambiguous lease scope prevented resolving landlord responsibility and contractual indemnification as a matter of law.',[l,c])
issue(r,'causation_identification','RMF Holding and Burgundy Room could not obtain summary judgment simply by pointing to plaintiff inability to identify the specific cause.',[n])
issue(r,'other','Lease and rider were ambiguous about the downspout and the scope of tenant indemnification; factfinder must resolve.',[l])
material(r,'other','Lease and rider considered together; ambiguous scope of leased premises and indemnification.',[l])
sections(r,'procedural_history current_outcome facts','facts procedural_history current_outcome','legal_reasoning','legal_reasoning metadata')
cue(r,'indirect_reasoning',n,b);RECORDS.append(r)

# Rodriguez: building ownership does not establish ownership of the curb ramp.
r=case(5992200,'CAL_001')
h=ev(r,1,'In an action to recover','insofar as asserted against them.',status='procedural_history')
d=ev(r,1,'Ordered that the order is affirmed insofar as appealed from, with costs.',status='current_disposition')
f=ev(r,1,'The plaintiff allegedly sustained','the City of New York.',status='allegation')
l=ev(r,2,'Although section 7-210','pursuant to that provision”',status='court_finding')
n=ev(r,2,'The Themelion defendants established','part of the pedestrian ramp',status='court_finding')
z=ev(r,2,'Accordingly, the Supreme Court properly granted','insofar as asserted against them.',status='current_disposition')
eligibility(r,'trip',[f,l],[f],[n],basis='insufficient',property_status='unclear',decision='review',reasons=['property_unclear'],flags=['property_boundary'],note='Private ownership is stated for the abutting building, not the accident ramp. Municipal-sidewalk liability context suggests a public boundary, but source does not expressly establish ramp title/control. No private-property inclusion without adjudication.')
outcome(r,'affirmed','defendant','plaintiff','March 21, 2011 order, limited appeal','Granted Themelion defendants summary judgment on claims against them.',[h,d])
facts(r,'unclear','sidewalk',['unclear'],'unclear',['owner','municipality'],'Plaintiff allegedly tripped on a pedestrian ramp in front of a privately owned Brooklyn building. The opinion does not identify the particular physical defect or establish private ownership of the ramp.',[f,l,n])
issue(r,'duty','Section 7-210 does not treat pedestrian ramps as sidewalks for imposing liability on abutting owners; defendants established fall area was a ramp.',[l,n])
issue(r,'code_violation','Court addressed the reach of Administrative Code section 7-210, not a proven construction-code violation.',[l,n])
sections(r,'procedural_history current_outcome facts','legal_reasoning quoted_precedent current_outcome','metadata')
cue(r,'repeated_outcome',z);cue(r,'indirect_reasoning',n);RECORDS.append(r)

# Germain: interior of defendants' commercial store; no claim of measured customer status.
r=case(4308801,'CAL_001')
h=ev(r,1,'Appeal from an order','dismissed the complaint.',status='procedural_history')
d=ev(r,1,'It is hereby ORDERED that the order so appealed from is unanimously affirmed without costs.',status='current_disposition')
f=ev(r,1,'Memorandum: Plaintiff commenced','carpeting at defendants’ store.',status='allegation')
a=ev(r,2,'The allegedly defective condition','estimated at her deposition that the height differential was one-half of an inch.',status='testimony_or_record')
x=ev(r,3,'Defendants’ expert engineer measured','three-eighths of an inch.',status='testimony_or_record')
n=ev(r,3,'Plaintiff’s friend testified','lifted up or pulled up in any way.”',status='testimony_or_record')
t=ev(r,3,'“After examining the photograph[]','the defect is too trivial to be actionable”',status='court_finding')
q=ev(r,4,'We further conclude','trap, snare or nuisance”',status='court_finding')
eligibility(r,'trip',[f,a],[f,a],[t,q],basis='controlled',note='The opinion places the fall inside defendants’ store and describes its entrance rugs. Private commercial interior/control is supported; title/lease allocation and plaintiff shopping purpose are not stated.')
outcome(r,'affirmed','defendant','plaintiff','May 17, 2011 order','Granted defendants summary judgment and dismissed complaint.',[h,d])
facts(r,'retail','entrance',['uneven_surface','obstruction'],'unclear',['other'],'Plaintiff allegedly tripped where duct tape joined permanent and seasonal entrance rugs inside defendants’ store. Testimony differed on the height differential and appearance of the tape.',[f,a,x,n])
issue(r,'trivial_defect','Considering dimensions, photograph and circumstances, defect was too trivial to be actionable; no triable trap/snare/nuisance issue.',[t,q])
issue(r,'expert_evidence','Defense engineer measured a five-sixteenths to three-eighths inch height differential; court assessed dimensions with other circumstances.',[x,t])
material(r,'party_testimony','Plaintiff described catching her foot at taped rug junction and lacked a pre-fall observation of the tape.',[a])
material(r,'witness_testimony','Friend estimated differential and testified tape remained secured, not lifted or bubbled.',[a,n])
material(r,'expert_evidence','Defense engineer measurement of rug height differential.',[x])
material(r,'photographs','Court examined photograph depicting defect dimensions/irregularity in triviality analysis.',[t])
sections(r,'metadata procedural_history current_outcome facts','legal_reasoning current_outcome facts','facts legal_reasoning quoted_precedent','legal_reasoning quoted_precedent metadata')
cue(r,'indirect_reasoning',t,q);RECORDS.append(r)

def save_chunk(chunk):
    if chunk not in sys.argv[1:]:return
    rows=[r for r in RECORDS if r['input_chunk_id']==chunk]
    expected=json.loads((ROOT/f'calibration/{chunk}.expected.json').read_text(encoding='utf8'))['case_ids']
    report=validate(rows,SOURCES,expected)
    if not report['passed']:raise ValueError(report['errors'])
    draft=HERE/f'calibration/drafts/{chunk}.draft-v1.json'
    if draft.exists():raise FileExistsError('Preserve existing independent draft: '+str(draft))
    dump(draft,rows);dump(HERE/f'calibration/{chunk}.json',rows)
    dump(HERE/f'calibration/{chunk}.validation.json',report)
    print(chunk, 'validated:',len(rows),'records')

save_chunk('CAL_001')

# CAL_002: Richardson, an edge-of-walkway fall rather than a described slip/trip.
r=case(2993705,'CAL_002')
h=ev(r,1,'In an action to recover','insofar as asserted against them.',status='procedural_history')
d=ev(r,1,'Ordered that the order is affirmed, with costs.',status='current_disposition')
f=ev(r,2,'On April 1, 2010,','This was the first rehearsal of the play at the venue.',status='allegation')
l=ev(r,3,'An owner of property or tenant in possession of real property has a duty to maintain the property in a reasonably safe condition',status='court_finding')
n=ev(r,3,'A defendant moving for summary judgment dismissing a premises liability cause of action','actual or constructive notice of its existence',status='court_finding')
a=ev(r,5,'Here, contrary to the appellants\' contention,','open and obvious and not inherently dangerous.',status='court_finding')
b=ev(r,6,'The evidence they submitted demonstrated','the other trenches within the venue were protected by permanent railings',status='testimony_or_record')
z=ev(r,6,'Accordingly, the Supreme Court properly denied','insofar as asserted against them.',status='current_disposition')
eligibility(r,'other_fall',[f,a],[f],[a,b],decision='exclude',reasons=['outside_slip_trip_scope'],note='Source describes stepping off an unguarded walkway edge into a trench, with no slipping or tripping mechanism. Excluded under current narrow slip/trip rule; potentially relevant to a separately approved broader premises-fall study.')
outcome(r,'affirmed','plaintiff','defendant','October 29, 2014 order','Denied defendants summary judgment dismissing amended complaint against them.',[h,d])
facts(r,'recreation','walkway',['hole','lighting','other'],'other',['owner','manager'],'During a rehearsal she was producing/directing, plaintiff walked toward the stage and her foot went off an unguarded walkway edge into a water-filled trench 15 inches below. The walkway area was dark; the stage was lit.',[f,b],date='2010-04-01')
issue(r,'duty','Defendants failed to show absence of a duty; they retained authority over railing removal and lighting.',[l,a])
issue(r,'creation_of_hazard','Court recited creation/notice burden and considered defendants design of the condition, removal of railings and control of lighting; no final liability finding.',[n,a,b])
for t in ['actual_notice','constructive_notice']:
    issue(r,t,'Court states creation/actual/constructive notice summary-judgment standard; no separate case-specific determination that notice was proved.',[n])
issue(r,'open_and_obvious','Defendants failed to establish unguarded, unilluminated trenches were open and obvious and not inherently dangerous.',[a,b])
material(r,'other','Motion evidence showed defendants controlled railings/lighting and left this trench unguarded; source does not identify the evidence medium.',[a,b])
sections(r,'metadata procedural_history current_outcome','facts procedural_history','current_outcome legal_reasoning','legal_reasoning quoted_precedent','legal_reasoning facts','facts legal_reasoning current_outcome metadata')
cue(r,'repeated_outcome',z);cue(r,'indirect_reasoning',a);RECORDS.append(r)

# Heck: lack of specific inspection evidence is not conclusive notice.
r=case(2757329,'CAL_002')
h=ev(r,1,'In an action to recover','which granted the defendant\'s motion for summary judgment dismissing the complaint.',status='procedural_history')
d=ev(r,1,'Ordered that the order is reversed','is denied.',status='current_disposition')
f=ev(r,1,'The plaintiff allegedly slipped','owned by the defendant.',status='allegation')
n=ev(r,2,'A real property owner','actual or constructive notice of it',status='court_finding')
b=ev(r,3,'Here, the defendant failed','last inspected before the time when the plaintiff allegedly fell',status='court_finding')
z=ev(r,3,'Accordingly, the Supreme Court should have denied the defendant\'s motion for summary judgment dismissing the complaint.',status='current_disposition')
eligibility(r,'slip',[f],[f],[b])
outcome(r,'reversed','plaintiff','plaintiff','February 10, 2014 order','Granted defendant summary judgment dismissing complaint.',[h,d])
facts(r,'residential','entrance',['snow_ice'],'unclear',['owner'],'Plaintiff allegedly slipped on ice in the laundry-room vestibule of a defendant-owned apartment complex. Her relationship to the complex and the accident date are not stated.',[f])
for t in ['duty','creation_of_hazard','actual_notice']:
    issue(r,t,'Court recites owner/control liability standard requiring creation or actual/constructive notice; no separate finding proving this element.',[n])
issue(r,'constructive_notice','General weekly inspection practice did not establish last inspection before the fall; defendant failed prima facie burden, not a conclusive finding of notice.',[b])
material(r,'party_testimony','Owner deposition described general visits, without an accident-specific last inspection.',[b])
sections(r,'metadata procedural_history current_outcome facts','legal_reasoning quoted_precedent','legal_reasoning facts current_outcome metadata')
cue(r,'repeated_outcome',z);cue(r,'indirect_reasoning',b);RECORDS.append(r)

# Ackerman: causation failure remains an eligible private-premises negligence appeal.
r=case(3206955,'CAL_002')
h=ev(r,1,'In an action to recover','which granted the defendants\' motion for summary judgment dismissing the complaint.',status='procedural_history')
d=ev(r,1,'Ordered that the order is affirmed, with costs.',status='current_disposition')
f=ev(r,1,'The plaintiff Toba Faigi Ackerman','the exterior cement front steps of the defendants\' home.',status='allegation')
n=ev(r,2,'The defendants established','she was unable to identify the cause of her fall',status='court_finding')
a=ev(r,2,'The injured plaintiff\'s affidavit,','avoid the consequences of her earlier deposition testimony',status='court_finding')
z=ev(r,2,'Accordingly, the Supreme Court properly granted the defendants\' motion for summary judgment dismissing the complaint.',status='current_disposition')
eligibility(r,'trip',[f],[f],[n],basis='controlled',note='Defendants’ home establishes private residential premises/control; precise legal title and plaintiff visitor/guest relationship not expressly stated. Steps describe location, not a proven stair defect.')
outcome(r,'affirmed','defendant','plaintiff','March 18, 2015 order','Granted defendants summary judgment dismissing complaint.',[h,d])
facts(r,'residential','stairs',['unclear'],'unclear',['other'],'Plaintiff allegedly tripped while ascending exterior cement front steps of defendants’ home. She could not identify what caused the fall; no specific hazard is established.',[f,n])
issue(r,'causation_identification','Defense established entitlement through plaintiff deposition inability to identify the cause; opposition failed to raise a triable issue.',[n,a])
issue(r,'procedural_issue','Opposition affidavit appeared to create feigned issues to avoid earlier deposition testimony.',[a])
material(r,'party_testimony','Plaintiff deposition and later opposition affidavit; latter rejected as feigned.',[n,a])
sections(r,'metadata procedural_history current_outcome facts','procedural_history legal_reasoning current_outcome','metadata')
cue(r,'repeated_outcome',z);cue(r,'indirect_reasoning',n,a);RECORDS.append(r)

# Maldonado: entrance/drain boundary not explicitly privately owned or controlled.
r=case(3193933,'CAL_002')
h=ev(r,1,'In an action to recover','all cross claims insofar as asserted against it.',status='procedural_history')
d=ev(r,1,'Ordered that the order is affirmed, with costs.',status='current_disposition')
f=ev(r,1,'The plaintiff allegedly was injured','near the front door entrance.',status='allegation')
a=ev(r,2,'A large planter,','at the time of the accident.',status='testimony_or_record')
t=ev(r,5,'Here, viewing the evidence','not actionable',status='court_finding')
u=ev(r,5,'In light of our determination,','the appellant\'s remaining contention.',status='court_finding')
z=ev(r,5,'Accordingly, the Supreme Court properly denied the appellant\'s motion for summary judgment.',status='current_disposition')
eligibility(r,'trip',[f,a],[f],[t],basis='insufficient',property_status='unclear',decision='review',reasons=['property_unclear'],flags=['property_boundary'],note='Condominium relationship, entrance drain and removed planter suggest private premises, but text only says in front of complex near front door. Exact accident-area ownership/control versus adjacent public approach not established; contractor identity alone insufficient.')
outcome(r,'affirmed','plaintiff','defendant','December 3, 2014 order','Denied Court Restoration summary judgment dismissing amended complaint and cross-claims against it.',[h,d])
facts(r,'residential','entrance',['hole','uneven_surface'],'unclear',['contractor'],'Plaintiff allegedly tripped on a depressed drain in front of her parents’ condominium complex near its front door. A planter normally blocking access had been removed during construction.',[f,a])
issue(r,'trivial_defect','Contractor motion evidence failed to establish drain defect trivial considering circumstances; plaintiff opposition sufficiency therefore not reached.',[t,u])
issue(r,'other','Appellant remaining contention was not addressed and its subject is unspecified in the opinion.',[u],'raised_only')
material(r,'party_testimony','Plaintiff deposition considered among movant evidence found insufficient to establish triviality.',[t])
material(r,'witness_testimony','Condominium superintendent deposition considered.',[t])
material(r,'photographs','Plaintiff photograph of drain on accident date considered.',[t])
sections(r,'metadata procedural_history current_outcome facts','facts procedural_history current_outcome legal_reasoning quoted_precedent','legal_reasoning quoted_precedent','legal_reasoning quoted_precedent','legal_reasoning current_outcome metadata')
cue(r,'repeated_outcome',z);cue(r,'indirect_reasoning',t);RECORDS.append(r)
save_chunk('CAL_002')

# CAL_003: Nieves
r=case(4546774,'CAL_003')
h=ev(r,1,'In an action to recover','The order denied the defendant\'s motion for summary judgment dismissing the complaint.',status='procedural_history')
d=ev(r,1,'Ordered that the order is affirmed, with costs.',status='current_disposition')
f=ev(r,1,'The plaintiff allegedly was injured','whose owners leased a portion of the building.',status='allegation')
a=ev(r,2,'The plaintiff asked to use the bathroom','water leaking from the area of the bathroom doorway.',status='testimony_or_record')
l=ev(r,2,'An out-of-possession landlord is not liable','a course of conduct"',status='court_finding')
n=ev(r,3,'Here, the plaintiff alleged','a safe and code-compliant manner"',status='party_argument')
b=ev(r,3,'The defendant failed to meet','injuries caused by a defective condition therein',status='court_finding')
z=ev(r,3,'Accordingly, we agree with the Supreme Court\'s determination','regardless of the sufficiency of the opposition papers',status='current_disposition')
eligibility(r,'slip',[f],[f,a],[b])
outcome(r,'affirmed','plaintiff','defendant','January 13, 2017 order','Denied defendant landlord summary judgment dismissing complaint.',[h,d])
facts(r,'retail','indoor_floor',['water','debris'],'unclear',['owner'],'Plaintiff was directed from a bodega to its basement bathroom and allegedly slipped on water and saturated cardboard. The building was defendant-owned, and bodega owners leased part of it.',[f,a])
for t in ['duty','out_of_possession_landlord']:
    issue(r,t,'Landlord failed to establish complete relinquishment of basement possession/control for purposes of statutory duty; no final finding of liability.',[l,b])
issue(r,'code_violation','Plaintiff invoked Administrative Code 28-301.1; court held landlord failed to show it could not be liable under that provision.',[n,b])
sections(r,'metadata procedural_history current_outcome facts','facts procedural_history legal_reasoning','legal_reasoning current_outcome metadata')
cue(r,'repeated_outcome',z);cue(r,'indirect_reasoning',b);RECORDS.append(r)

# Troina
r=case(4551400,'CAL_003')
h=ev(r,1,'In an action to recover','The order granted the defendants\' motion for summary judgment dismissing the complaint.',status='procedural_history')
d=ev(r,1,'Ordered that the order is reversed','is denied.',status='current_disposition')
f=ev(r,2,'Marie Troina','alleging negligent maintenance of the parking lot.',status='allegation')
a=ev(r,2,'After joinder of issue,','the allegedly dangerous condition.',status='party_argument')
n=ev(r,2,'The defendants failed to establish, prima facie,','the tire/wheel stop at issue was last inspected',status='court_finding')
z=ev(r,3,'Since the defendants failed','without regard to the sufficiency of the opposition papers',status='current_disposition')
eligibility(r,'trip',[f],[f],[n],basis='controlled',note='Restaurant parking lot and alleged ownership/operation/maintenance are expressly linked to named defendants. Preserve allegation status; individual ownership allocation is not decided.')
outcome(r,'reversed','plaintiff','plaintiff','June 13, 2017 order','Granted defendants summary judgment dismissing complaint.',[h,d])
facts(r,'restaurant','parking_lot',['wheel_stop'],'unclear',['other'],'Plaintiff alleges her foot caught under a wheel stop in a Dunkin’ Donuts parking lot. Defendants allegedly owned, operated and/or maintained the restaurant; exact individual roles are unresolved.',[f])
issue(r,'creation_of_hazard','Defendants sought judgment arguing no creation of dangerous condition; opinion resolves motion on constructive-notice burden instead.',[a],'raised_only')
issue(r,'actual_notice','Defendants argued no actual notice; court did not separately decide that issue.',[a],'raised_only')
issue(r,'constructive_notice','No evidence of last pre-accident inspection of wheel stop; defendants failed initial burden to establish lack of notice.',[n])
sections(r,'metadata procedural_history current_outcome','facts procedural_history legal_reasoning','legal_reasoning current_outcome metadata')
cue(r,'repeated_outcome',z);cue(r,'indirect_reasoning',n);RECORDS.append(r)

# Verges: merits present despite evidence preclusion; institutional title uncertain.
r=case(4795834,'CAL_003')
d=ev(r,1,'Order, Supreme Court, Bronx County','unanimously affirmed, without costs.',status='current_disposition')
f=ev(r,1,'Plaintiff Angel Verges was injured','he slipped and fell on a milky substance.',status='allegation')
a=ev(r,2,'Plaintiffs alleged','routinely left unaddressed by defendant.',status='allegation')
w=ev(r,2,'Defendant submitted affidavits','did not see any debris on the staircase.',status='testimony_or_record')
p=ev(r,2,'These affidavits failed','numerous court orders directing defendant to do so',status='court_finding')
n=ev(r,3,'Even assuming that defendant satisfied','was a recurring condition that was routinely left unaddressed',status='court_finding')
eligibility(r,'slip',[f,w],[f],[p,n],basis='insufficient',property_status='unclear',decision='review',reasons=['property_unclear'],flags=['institutional_ownership'],note='Defendant operates/manages the described homeless shelter, but private ownership/lease of accident premises is not explicit. Corporate identity and cleaning employees alone do not establish private premises. Substantive alternate recurring-condition holding means not procedural-only.')
outcome(r,'affirmed','plaintiff','defendant','December 11, 2018 order (on or about)','Denied Concourse Residential Hotel summary judgment dismissing complaint against it.',[d])
facts(r,'institutional','stairs',['other'],'unclear',['manager'],'Plaintiff allegedly slipped on a milky substance while descending an interior stairwell in defendant’s homeless shelter. Plaintiffs alleged that employees dragging garbage bags repeatedly left the substance there.',[f,a,w])
issue(r,'creation_of_hazard','Plaintiff wife and nonparty testimony supported a triable issue about employees creating the milky substance by dragging garbage bags.',[n])
issue(r,'recurring_condition','Alternatively, plaintiffs raised triable issues concerning a constantly present, recurring condition routinely left unaddressed.',[n])
issue(r,'constructive_notice','Recurring-condition evidence supports the alternate notice-related rationale; court found triable issues, not conclusively established notice.',[n])
issue(r,'procedural_issue','Manager/porter affidavits could not be considered because witnesses were identified only after motion, despite discovery requests and orders.',[p])
material(r,'witness_testimony','Manager/porter affidavits excluded for late identification; nonparty witness testimony supported recurrence.',[w,p,n])
material(r,'party_testimony','Co-plaintiff wife testimony supported recurring-condition alternative holding.',[n])
sections(r,'metadata procedural_history current_outcome facts','facts legal_reasoning','legal_reasoning facts metadata')
cue(r,'indirect_reasoning',p,n);RECORDS.append(r)

# Gartenberg: identify private-status evidence limitation, preserve clear affirmation.
r=case(4840329,'CAL_003')
d=ev(r,1,'Order, Supreme Court, New York County','unanimously affirmed, without costs.',status='current_disposition')
f=ev(r,1,'Plaintiff was injured','a restaurant operated by Driton.',status='allegation')
w=ev(r,2,'The conflicting testimony','raise credibility issues to be determined at trial',status='court_finding')
n=ev(r,2,'There is also a triable issue of fact','the bathroom was last cleaned and inspected prior to plaintiff\'s fall',status='court_finding')
x=ev(r,2,'The court also properly found','the defect on the platform was trivial as a matter of law',status='court_finding')
b=ev(r,3,'Finally, plaintiff raised an issue of fact','devote his personal skill and ability to his business',status='court_finding')
eligibility(r,'slip',[f],[f,w],[n,x],basis='insufficient',property_status='unclear',decision='review',reasons=['property_unclear'],flags=['factual_support_thin'],note='Opinion establishes restaurant operation and interior bathroom control, but not title/lease/private status of the premises. Under rule that a private operator alone does not prove private property, retain review. Team should clarify whether ordinary commercial interiors supply adequate private-status evidence. Caption shows cross-appeal; only one order and full affirmation are described.')
outcome(r,'affirmed','plaintiff','both','October 7, 2019 order (on or about), limited by briefs','Denied Driton summary judgment; challenged issues also included lost business profits.',[d])
facts(r,'restaurant','indoor_floor',['water','uneven_surface'],'unclear',['other'],'Plaintiff allegedly slipped in the men’s bathroom of a Driton-operated restaurant. Testimony conflicted about moisture, and experts disagreed about a chipped or repaired floor tile as a cause.',[f,w,x])
issue(r,'causation_identification','Conflicting moisture testimony and tile causation expert opinions left triable issues; not a finding of a single proven cause.',[w,x])
issue(r,'constructive_notice','General cleaning practice without a specific last cleaning/inspection left a triable notice issue.',[n])
issue(r,'trivial_defect','Conflicting expert opinions about tile causation left a triable issue on whether the platform defect was trivial.',[x])
issue(r,'expert_evidence','Conflicting expert opinions on chipped/repaired tile causation precluded resolving triviality.',[x])
issue(r,'other','Plaintiff raised a fact issue whether business lost profits directly resulted from injury-related inability to contribute personal skill.',[b])
material(r,'party_testimony','Plaintiff testimony about moisture conflicted with employee account.',[w])
material(r,'witness_testimony','Employee denied observing moisture; defense witnesses described general cleaning practice without accident-specific last inspection.',[w,n])
material(r,'expert_evidence','Conflicting opinions on tile contribution to accident.',[x])
sections(r,'metadata procedural_history current_outcome facts','facts legal_reasoning','legal_reasoning metadata')
cue(r,'indirect_reasoning',n,x,b);RECORDS.append(r)
save_chunk('CAL_003')
