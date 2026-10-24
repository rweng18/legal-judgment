import copy,unittest
import numpy as np
from preprocessing import clean_text,mask_text,random_remove,words
from train import metrics,validate_development
from common import HERE,read,records,output

class PipelineTests(unittest.TestCase):
    def test_current_outcomes_removed_history_preserved(self):
        full='The Supreme Court denied the motion in 2018. Ordered that the order is reversed, with costs. Notice was disputed (see Smith v Jones, 12 AD3d 15 [2017], affirmed 30 NY3d 10 [2018]). We reverse. Accordingly, the Supreme Court should have granted the motion.'
        masked,removed=mask_text(full)
        self.assertEqual(len(removed),3)
        self.assertIn('denied the motion in 2018',masked)
        self.assertIn('affirmed 30 NY3d',masked)
        self.assertIn('Notice was disputed',masked)
    def test_both_classes(self):
        for word in ['affirmed','reversed','vacated']:
            masked,removed=mask_text(f'Ordered that the order is {word}. The plaintiff slipped on a wet floor.')
            self.assertNotIn(word,masked);self.assertEqual(len(removed),1)
    def test_metadata_and_dissent_boundary(self):
        text='Slip Op Appellate Division. In an action for injuries, the plaintiff appeals. The dissent argues otherwise. Concur—Smith, J.P., Jones and Lee, JJ. Ordered that the order is affirmed.'
        full,_=clean_text(text)
        self.assertNotIn('Slip Op',full);self.assertNotIn('Jones and Lee',full)
        self.assertIn('The dissent argues otherwise',full);self.assertIn('Ordered that',full)
        full,_=clean_text('The majority finds notice. Smith, J. (dissenting) I would reverse.')
        self.assertNotIn('I would reverse',full)
    def test_random_budget_and_reproducibility(self):
        text='A wet floor caused an accident. The court considered the evidence. Ordered that the order is affirmed.'
        for budget in [0,1,8,len(words(text))-1]:
            a,log=random_remove(text,budget,11,'case');b,_=random_remove(text,budget,11,'case')
            self.assertEqual(a,b);self.assertEqual(len(words(a)),len(words(text))-budget)
            self.assertEqual(len(log['removed_word_indices']),budget)
    def test_metric_class_order(self):
        m=metrics([0,0,1,1],[0,0,0,0])
        self.assertEqual(m['confusion_matrix'],[[2,0],[2,0]])
        self.assertEqual(m['balanced_accuracy'],.5)
        self.assertAlmostEqual(m['macro_f1'],1/3)
    def test_explicit_family_hint(self):
        from prepare import family_groups
        source={'a':{'case_name':'Alpha','text':'first text'},'b':{'case_name':'Beta','text':'different text'}}
        groups,edges,_=family_groups(source,['a','b'],[{'case_ids':['a','b']}])
        self.assertEqual(groups['a'],groups['b'])
        self.assertTrue(any(e['basis']=='explicit_family_hint' for e in edges))
    def test_no_test_or_family_overlap(self):
        rows=[{'case_id':'a','family_id':'a','period':'train','eligibility':'include','label':0,'calibration_exposure':False},
              {'case_id':'b','family_id':'b','period':'validation','eligibility':'include','label':1,'calibration_exposure':False}]
        validate_development(rows)
        for field,value in [('period','test'),('family_id','a'),('calibration_exposure',True)]:
            bad=copy.deepcopy(rows);bad[1][field]=value
            with self.assertRaises(AssertionError):validate_development(bad)
    def test_saved_data_invariants(self):
        out=output(read(HERE/'config.json'));rows=records(out/'dataset_development.jsonl')
        validate_development(rows)
        for r in rows:
            for name,text in r['texts'].items():
                if name.startswith('RANDOM_'):self.assertEqual(len(words(text)),len(words(r['texts']['MASKED'])))
        sample=read(out/'mask_audit_sample.json')['case_ids']
        counts={(s,k):sum(r['case_id'] in sample and r['period']==s and r['label']==k for r in rows) for s in ['train','validation'] for k in [0,1]}
        self.assertEqual(set(counts.values()),{2})
    def test_saved_metrics_recompute_and_same_ids(self):
        out=output(read(HERE/'config.json'))
        if not (out/'metrics.json').exists():self.skipTest('Training has not finished')
        pred=records(out/'validation_predictions.jsonl');ids={r['case_id'] for r in records(out/'dataset_development.jsonl') if r['period']=='validation'}
        for r in read(out/'metrics.json')['grid']:
            p=[x for x in pred if (x['model'],x['variant'],x['C'])==(r['model'],r['variant'],r['C'])]
            self.assertEqual({x['case_id'] for x in p},ids)
            m=metrics([x['true_label'] for x in p],[x['predicted_label'] for x in p])
            for k,v in m.items():self.assertEqual(v,r[k])
    def test_training_only_vocabulary(self):
        import joblib
        out=output(read(HERE/'config.json'));p=out/'models/TFIDF_LR_FULL_C1.joblib'
        if not p.exists():self.skipTest('Training has not finished')
        model=joblib.load(p);vectorizer=model[0];rows=records(out/'dataset_development.jsonl')
        analyzer=vectorizer.build_analyzer();trainterms=set();valterms=set()
        for r in rows:(trainterms if r['period']=='train' else valterms).update(analyzer(r['texts']['FULL']))
        self.assertTrue(set(vectorizer.vocabulary_)<=trainterms)
        self.assertFalse(set(vectorizer.vocabulary_)&(valterms-trainterms))

if __name__=='__main__':unittest.main(verbosity=2)
