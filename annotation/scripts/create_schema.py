"""Generate the versioned schema. Normal annotation does not need this command."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ISSUES=['duty','creation_of_hazard','actual_notice','constructive_notice','recurring_condition',
        'open_and_obvious','trivial_defect','storm_in_progress','causation_identification',
        'assumption_of_risk','comparative_fault','out_of_possession_landlord','contractor_duty',
        'code_violation','expert_evidence','spoliation','procedural_issue','labor_law','other']
DISPOSITIONS=['affirmed','reversed','vacated','modified','mixed','appeal_dismissed','remand_only','other','unclear']
def obj(properties):return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}
def arr(item,minItems=0):return {'type':'array','items':item,'minItems':minItems}
def enum(*values):return {'enum':list(values)}
S={'type':'string'};NONEMPTY={'type':'string','minLength':1};BOOL={'type':'boolean'}
NULLSTR={'type':['string','null']};REFS=arr(NONEMPTY)
SCHEMA=obj({
 'schema_version':{'const':'1.0.0'},'prompt_version':NONEMPTY,'case_id':NONEMPTY,'text_sha256':NONEMPTY,'input_chunk_id':NONEMPTY,
 'run':obj({'annotator_id':NONEMPTY,'model_name':NONEMPTY,'model_version':NULLSTR,'annotated_at':NONEMPTY,
            'review_status':enum('llm_draft','human_reviewed','adjudicated'),'human_reviewer_id':NULLSTR,
            'review_note':S,'supersedes':NULLSTR}),
 'eligibility':obj({'scope':enum('in_scope','out_of_scope','uncertain'),
                    'binary_task':enum('include','exclude','review'),
                    'reasons':arr(enum('public_property','property_unclear','no_person_fall','outside_slip_trip_scope',
                                      'procedural_only','third_party_only','mixed_procedural_merits','mixed_outcome',
                                      'dismissed_appeal','outcome_unclear','text_problem','duplicate_or_related','other')),
                    'property_status':enum('private','public','unclear'),
                    'property_basis':enum('owned','leased','controlled','insufficient','other'),
                    'fall_type':enum('slip','trip','slip_or_trip','other_fall','nonfall','unclear'),
                    'merits':enum('substantive','procedural_only','third_party_only','mixed_unclear'),
                    'property_evidence':REFS,'incident_evidence':REFS,'scope_evidence':REFS}),
 'outcome':obj({'appellate_disposition':enum(*DISPOSITIONS),'binary_label':enum(None,0,1),
                'multiple_orders':BOOL,'favors':enum('plaintiff','defendant','both','unclear','not_applicable'),
                'disposition_evidence':REFS,
                'orders':arr(obj({'description':S,'appellant_role':enum('plaintiff','defendant','both','third_party','other','unclear'),
                                  'trial_court_action':S,'appellate_disposition':enum(*DISPOSITIONS),'evidence_ids':REFS}),1)}),
 'facts':obj({'premises_type':enum('residential','retail','restaurant','office','industrial','religious_nonprofit',
                                  'recreation','institutional','parking_only','other','unclear'),
              'location':enum('indoor_floor','stairs','entrance','walkway','parking_lot','sidewalk','road',
                              'loading_dock','other','unclear'),
              'hazards':arr(enum('snow_ice','water','grease','debris','uneven_surface','hole','obstruction','wheel_stop',
                                 'stairs_handrail','lighting','other','unclear'),1),
              'injured_role':enum('customer','tenant','employee','contractor','guest','visitor','other','unclear'),
              'defendant_roles':arr(enum('owner','tenant','manager','contractor','municipality','other','unclear'),1),
              'accident_date':NULLSTR,'factual_summary':S,'evidence_ids':REFS}),
 'legal_issues':arr(obj({'topic':enum(*ISSUES),'discussion':enum('not_discussed','raised_only','court_addressed','unclear'),
                        'finding':S,'evidence_ids':REFS}),len(ISSUES)),
 'evidence_discussed':arr(obj({'type':enum('party_testimony','witness_testimony','photographs','inspection_records',
                                          'maintenance_records','expert_evidence','weather_records','surveillance','other'),
                              'description':S,'evidence_ids':REFS})),
 'text_sections':arr(obj({'passage_id':NONEMPTY,'types':arr(enum('facts','procedural_history','legal_reasoning',
                          'current_outcome','quoted_precedent','metadata','separate_opinion','unclear'),1)}),1),
 'outcome_cues':arr(obj({'kind':enum('current_disposition','repeated_outcome','indirect_reasoning'),'evidence_ids':REFS})),
 'quality':obj({'needs_review':BOOL,'flags':arr(enum('property_boundary','institutional_ownership','procedural_overlap',
                         'multiple_parties_orders','outcome_ambiguity','text_incomplete','ocr_or_formatting',
                         'possible_duplicate_family','factual_support_thin','other')),'notes':S}),
 'evidence':arr(obj({'evidence_id':NONEMPTY,'passage_id':NONEMPTY,'quote':NONEMPTY,
                     'statement_status':enum('allegation','party_argument','testimony_or_record','court_finding',
                                             'procedural_history','current_disposition','unclear')}))})
SCHEMA.update({'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:ny-fall:annotation:1.0.0',
               'title':'NY slip/trip case annotation v1.0.0','description':'One record per case. Unknowns are explicit. No gold status without human review.'})
if __name__=='__main__':
 (ROOT/'schema').mkdir(exist_ok=True)
 (ROOT/'schema'/'annotation.schema.json').write_text(json.dumps(SCHEMA,indent=2)+'\n',encoding='utf8')

