"""Manifest coverage and disagreement checks with synthetic data only."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import compare_calibration as compare

class CompareManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='.test-compare-',dir=ROOT/'tests')
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        source=json.loads((ROOT/'examples/SYNTHETIC_SOURCE.json').read_text(encoding='utf8'))
        annotation=json.loads((ROOT/'examples/SYNTHETIC_ANNOTATION.json').read_text(encoding='utf8'))
        self.rows=[];sources=[]
        for i in range(2):
            s=copy.deepcopy(source);r=copy.deepcopy(annotation)
            s['case_id']=r['case_id']=f'SYNTHETIC-TEST-{i}'
            sources.append(s);self.rows.append(r)
        self.write('source/cases.jsonl',sources)
        self.write('calibration/manifest.json',{'case_ids':['SYNTHETIC-TEST-0']})
        self.write('batches/A/manifest.json',{'case_ids':[r['case_id'] for r in self.rows]})
        self.files=[self.root/f'{name}.json' for name in ('one','two','three')]
        self.out=self.root/'comparison.json'

    def write(self,name,obj):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(obj),encoding='utf8')

    def run_compare(self,*args):
        argv=['compare_calibration.py',*map(str,self.files),'--output',str(self.out),*map(str,args)]
        with patch.object(compare,'ROOT',self.root),patch.object(sys,'argv',argv),contextlib.redirect_stdout(io.StringIO()):
            compare.main()
        return json.loads(self.out.read_text(encoding='utf8'))

    def test_default_still_uses_calibration_manifest(self):
        for p in self.files:self.write(p.name,self.rows[:1])
        result=self.run_compare()
        self.assertEqual(result['cases'],1)
        self.assertEqual(result['disagreements'],[])

    def test_custom_manifest_counts_cases_and_finds_disagreement(self):
        for p in self.files:self.write(p.name,self.rows)
        changed=copy.deepcopy(self.rows)
        changed[1]['eligibility'].update(scope='uncertain',binary_task='review',reasons=['property_unclear'],property_status='unclear',property_basis='insufficient')
        changed[1]['outcome']['binary_label']=None
        changed[1]['quality'].update(needs_review=True,notes='Synthetic uncertainty test')
        self.write(self.files[2].name,changed)
        result=self.run_compare('--expected',self.root/'batches/A/manifest.json')
        self.assertEqual(result['cases'],2)
        self.assertEqual([r['case_id'] for r in result['disagreements']],['SYNTHETIC-TEST-1'])
        rows=[r for r in result['pairwise'] if r['field']=='outcome.binary_label']
        self.assertEqual([r['agreement'] for r in rows],[1.0,0.5,0.5])

    def test_missing_batch_case_is_rejected(self):
        for p in self.files:self.write(p.name,self.rows)
        self.write(self.files[2].name,self.rows[:1])
        with self.assertRaisesRegex(ValueError,'Missing case IDs'):
            self.run_compare('--expected',self.root/'batches/A/manifest.json')

if __name__=='__main__':unittest.main()
