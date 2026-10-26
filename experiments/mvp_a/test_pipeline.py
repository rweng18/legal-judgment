"""Check scientific integrity and rejection paths without retraining models."""
import copy
import tempfile
import unittest
from pathlib import Path
import nbformat
import pipeline as p


class ReviewedMVPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = p.modeling_rows()
        cls.manifest = p.rows(p.OUT / 'case_manifest.jsonl')
        cls.base = p.read(p.BECCA / 'data/mvp_split_v1/split_manifest.json')
        cls.exports = {v: p.rows(p.BECCA / 'data' / path)
                       for v, path in p.model_inputs.VARIANTS.items()}

    def test_selection_and_review_provenance(self):
        self.assertEqual(len(self.manifest), 120)
        self.assertEqual(len(self.data), 102)
        self.assertEqual(sum(r['status'] == 'assigned' for r in self.manifest), 119)
        self.assertEqual({r['case_id'] for r in self.manifest if r['status'] == 'pending'}, {'NY-4655053'})
        self.assertTrue(all(r['review_status'] == 'team_reviewed' for r in self.manifest))
        self.assertEqual(p.read(p.HERE / 'team_review_confirmation.json')['date'], '2026-10-25')

    def test_preserve_original_assignments_and_texts(self):
        current = {r['case_id']: r for r in self.manifest}
        development = {r['case_id']: r for r in self.data}
        for old in self.base['cases']:
            new = current[old['case_id']]
            self.assertEqual(new['period'], {'development':'validation'}.get(old['split'], old['split']))
            self.assertEqual((new['status'], new['label']), (old['status'], old['target']))
        for variant, records in self.exports.items():
            for row in records:
                if row['case_id'] in development:
                    self.assertEqual(row['text'], development[row['case_id']]['texts'][variant])

    def test_family_and_calibration_boundaries(self):
        splits = {s: {r['family_id'] for r in self.manifest if r['period'] == s}
                  for s in ['train', 'validation', 'test']}
        for a in splits:
            for b in splits:
                if a != b: self.assertFalse(splits[a] & splits[b])
        self.assertTrue(all(not r['calibration_exposure'] or r['period'] == 'train' for r in self.manifest))

    def test_no_test_features_or_predictions(self):
        reserved = {r['case_id'] for r in self.manifest if r['period'] == 'test'}
        self.assertEqual(len(reserved), 17)
        self.assertFalse(reserved & {r['case_id'] for r in self.data})
        self.assertFalse(reserved & {r['case_id'] for r in p.rows(p.OUT / 'validation_predictions.jsonl')})
        for variant in ['FULL', 'MASKED']:
            cache = p.read(p.OUT / 'encoder_cache' / f'{variant}.json')
            self.assertEqual(cache['case_ids'], [r['case_id'] for r in self.data])
            self.assertFalse(reserved & set(cache['case_ids']))

    def test_reject_annotation_metadata_in_features(self):
        changed = copy.deepcopy(self.exports)
        changed['FULL'][0]['outcome'] = 'affirmed'
        with self.assertRaisesRegex(ValueError, 'allowed fields'):
            p.model_inputs.validate_records(changed, self.base)

    def test_reject_missing_or_duplicate_records(self):
        for mutate in [lambda x: x.pop(), lambda x: x.append(copy.deepcopy(x[0]))]:
            changed = copy.deepcopy(self.exports)
            mutate(changed['FULL'])
            with self.assertRaises(ValueError):
                p.model_inputs.validate_records(changed, self.base)

    def test_masking_regressions_and_audit_coverage(self):
        self.assertEqual(p.verify_masked_v2.check_rules(), 33)
        ids = set(p.read(p.OUT / 'mask_audit_sample.json')['case_ids'])
        audit = p.read(p.OUT / 'masking_audit_review.json')
        self.assertEqual(ids, set(audit['reviewed_case_ids']))
        self.assertTrue(audit['performed_before_model_fit'])
        for split in ['train', 'validation']:
            for label in [0, 1]:
                self.assertEqual(sum(r['case_id'] in ids and r['period'] == split and r['label'] == label for r in self.data), 2)

    def test_random_controls_exact_and_reproducible(self):
        for row in self.data:
            full = row['texts']['FULL']
            budget = len(full.split()) - len(row['texts']['MASKED'].split())
            for seed in p.CONTROL_SEEDS:
                text, log = p.random_control(full, budget, seed, row['case_id'])
                self.assertEqual(text, row['texts'][f'RANDOM_{seed}'])
                self.assertEqual(len(log['removed_word_indices']), budget)
                self.assertEqual(len(text.split()), row['word_counts']['MASKED'])
        self.assertEqual(p.random_control('First sentence. Second sentence.', 0, 11, 'synthetic')[0], 'First sentence. Second sentence.')

    def test_metric_orientation_and_macro_average(self):
        # True rows: [[2,1],[1,0]], so recalls are 2/3 and 0.
        score = p.score([0, 0, 0, 1], [0, 0, 1, 0])
        self.assertEqual(score['confusion_matrix'], [[2, 1], [1, 0]])
        self.assertAlmostEqual(score['accuracy'], .5)
        self.assertAlmostEqual(score['balanced_accuracy'], 1/3)
        self.assertAlmostEqual(score['macro_f1'], 1/3)
        self.assertEqual(score['class_counts'], {'0': 3, '1': 1})

    def test_canonical_hash_and_immutable_output(self):
        cache = p.HERE / '.cache'
        cache.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as tmp:
            path = Path(tmp) / 'test.txt'
            path.write_bytes(b'alpha\r\nbeta\r\n')
            first = p.file_hash(path)
            path.write_bytes(b'alpha\nbeta\n')
            self.assertEqual(first, p.file_hash(path))
            target = Path(tmp) / 'frozen.json'
            p.write_json(target, {'label': 0}, True)
            with self.assertRaisesRegex(AssertionError, 'Frozen artifact changed'):
                p.write_json(target, {'label': 1}, True)
            self.assertEqual(p.read(target), {'label': 0})

    def test_all_saved_results_and_training_features(self):
        self.assertEqual(p.validate_results()['model_C_conditions'], 34)

    def test_delivered_notebook_executed(self):
        notebook = nbformat.read(p.HERE / 'Team_11_MVP.ipynb', as_version=4)
        code = [c for c in notebook.cells if c.cell_type == 'code']
        self.assertEqual(len(code), 14)
        self.assertEqual([c.execution_count for c in code], list(range(1, 15)))
        self.assertFalse(any(o.output_type == 'error' for c in code for o in c.outputs))


if __name__ == '__main__':
    unittest.main(verbosity=2)
