"""Meaningful failure cases for schema, evidence and merge integrity.

All source/annotation examples here are synthetic, not real cases.
"""
import copy,hashlib,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common import ISSUES,ROOT,validate,dump

def example():
 text='SYNTHETIC EXAMPLE ONLY. Plaintiff slipped on water inside a store owned by defendant. The order denying summary judgment is affirmed. A factual dispute about constructive notice remains.'
 source={'case_id':'SYNTHETIC-ONLY','text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
         'passages':[{'passage_id':'P001','start':0,'end':len(text),'text':text}]}
 facts='Plaintiff slipped on water inside a store owned by defendant.'
 outcome='The order denying summary judgment is affirmed.'
 finding='A factual dispute about constructive notice remains.'
 r={'schema_version':'1.0.0','prompt_version':'1.0.0','case_id':source['case_id'],'text_sha256':source['text_sha256'],'input_chunk_id':'SYNTHETIC',
 'run':{'annotator_id':'synthetic_example','model_name':'synthetic_fixture_not_a_model_run','model_version':None,
        'annotated_at':'2026-10-16T12:00:00-04:00','review_status':'llm_draft','human_reviewer_id':None,'review_note':'Synthetic schema example only.','supersedes':None},
 'eligibility':{'scope':'in_scope','binary_task':'include','reasons':[],'property_status':'private','property_basis':'owned',
                'fall_type':'slip','merits':'substantive','property_evidence':['E001'],'incident_evidence':['E001'],'scope_evidence':['E002','E003']},
 'outcome':{'appellate_disposition':'affirmed','binary_label':0,'multiple_orders':False,'favors':'unclear','disposition_evidence':['E002'],
            'orders':[{'description':'Order denying summary judgment','appellant_role':'unclear','trial_court_action':'Denied summary judgment.',
                       'appellate_disposition':'affirmed','evidence_ids':['E002']}]},
 'facts':{'premises_type':'retail','location':'indoor_floor','hazards':['water'],'injured_role':'unclear','defendant_roles':['owner'],
          'accident_date':None,'factual_summary':'Plaintiff slipped on water inside a defendant-owned store.','evidence_ids':['E001']},
 'legal_issues':[{'topic':t,'discussion':'court_addressed' if t=='constructive_notice' else 'not_discussed',
                 'finding':'A factual dispute remains; notice is not conclusively established.' if t=='constructive_notice' else '',
                 'evidence_ids':['E003'] if t=='constructive_notice' else []} for t in ISSUES],
 'evidence_discussed':[],
 'text_sections':[{'passage_id':'P001','types':['metadata','facts','procedural_history','current_outcome','legal_reasoning']}],
 'outcome_cues':[{'kind':'current_disposition','evidence_ids':['E002']}],
 'quality':{'needs_review':False,'flags':[],'notes':'Synthetic demonstration, not a corpus case.'},
 'evidence':[{'evidence_id':'E001','passage_id':'P001','quote':facts,'statement_status':'allegation'},
             {'evidence_id':'E002','passage_id':'P001','quote':outcome,'statement_status':'current_disposition'},
             {'evidence_id':'E003','passage_id':'P001','quote':finding,'statement_status':'court_finding'}]}
 return source,r

class ValidationTests(unittest.TestCase):
 def setUp(self):self.s,self.r=example();self.sources={self.s['case_id']:self.s}
 def check(self,r):return validate([r],self.sources,[self.r['case_id']])
 def test_valid_and_offsets(self):
  v=self.check(self.r);self.assertTrue(v['passed'],v)
  for e,o in zip(self.r['evidence'],v['evidence_offsets'][0]['evidence_offsets']):self.assertEqual(self.s['text'][o['start']:o['end']],e['quote'])
 def test_fabricated_quote(self):
  self.r['evidence'][0]['quote']='This was never in the source.';self.assertFalse(self.check(self.r)['passed'])
 def test_wrong_source_hash(self):
  self.r['text_sha256']='bad';self.assertFalse(self.check(self.r)['passed'])
 def test_unknown_case(self):
  self.r['case_id']='invented';self.assertFalse(self.check(self.r)['passed'])
 def test_duplicate_and_missing(self):
  self.assertFalse(validate([self.r,self.r],self.sources,[self.r['case_id']])['passed'])
  self.assertFalse(validate([],self.sources,[self.r['case_id']])['passed'])
  self.assertTrue(validate([],self.sources,[self.r['case_id']],partial=True)['passed'])
 def test_modified_not_binary(self):
  self.r['outcome']['appellate_disposition']='modified';self.assertFalse(self.check(self.r)['passed'])
 def test_null_review_valid(self):
  self.r['eligibility'].update(scope='uncertain',binary_task='review',reasons=['property_unclear'],property_status='unclear',property_basis='insufficient')
  self.r['outcome']['binary_label']=None;self.r['quality'].update(needs_review=True,flags=['property_boundary'])
  self.assertTrue(self.check(self.r)['passed'])
 def test_false_is_not_binary_zero(self):
  self.r['outcome']['binary_label']=False;self.assertFalse(self.check(self.r)['passed'])
 def test_missing_topic_or_passage(self):
  self.r['legal_issues'].pop();self.assertFalse(self.check(self.r)['passed'])
  self.s,self.r=example();self.r['text_sections']=[];self.assertFalse(self.check(self.r)['passed'])
 def test_human_status_requires_person(self):
  self.r['run']['review_status']='human_reviewed';self.assertFalse(self.check(self.r)['passed'])
 def test_order_conflict(self):
  self.r['outcome']['orders'][0]['appellate_disposition']='reversed';self.assertFalse(self.check(self.r)['passed'])
 def test_evidence_reference(self):
  self.r['facts']['evidence_ids']=['NO_SUCH_QUOTE'];self.assertFalse(self.check(self.r)['passed'])
 def test_timestamp(self):
  self.r['run']['annotated_at']='sometime';self.assertFalse(self.check(self.r)['passed'])

if __name__=='__main__':unittest.main()
