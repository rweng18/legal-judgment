"""Checks for combined-release integrity, source preservation and split leakage."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from prepare import HERE, ROOT, PRE, A, Families, digest, keyed, load_release, verify_rows


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.folder = HERE / 'inputs/abc_provisional_v1'
        self.manifest = [json.loads(l) for l in (self.folder / 'manifest.jsonl').read_text().splitlines()]
        self.texts = [json.loads(l) for l in (self.folder / 'development.jsonl').read_text().splitlines()]

    def test_exact_sources_and_review_status_preserved(self):
        release, joined = load_release(self.folder / 'release.json')
        self.assertEqual(len(joined), 321)
        for name, checksum in release['source_sha256'].items():
            self.assertEqual(digest((ROOT / name).read_bytes()), checksum, name)
        meta = keyed(self.manifest)
        for batch, path in [('A', ROOT / A / 'outputs/development_cases.jsonl'),
                            *[(b, ROOT / PRE / f'batch_{b.lower()}/provisional_v1/{b}_development_v2_PROVISIONAL.jsonl') for b in 'BC']]:
            original = keyed([json.loads(l) for l in path.read_text().splitlines()])
            combined = {r['case_id']: r for r in self.texts if r['batch'] == batch}
            self.assertEqual(set(original), set(combined))
            for k in combined:
                self.assertEqual(combined[k]['texts'], {v: original[k]['texts'][v] for v in ('FULL', 'MASKED')})
                self.assertEqual(meta[k]['source_review_status'], 'team_reviewed' if batch == 'A' else 'pending_human_review')
        for row in map(json.loads, (self.folder / 'C_label_provenance.jsonl').read_text().splitlines()):
            self.assertEqual({v['label'] for v in row['votes'].values()}, {meta[row['case_id']]['label']})

    def test_cross_batch_family_union_and_split_leakage(self):
        groups = Families(['a', 'b', 'c'])
        groups.union(['a', 'b'], 'batch_B')
        groups.union(['b', 'c'], 'batch_C')
        self.assertEqual(groups.find('a'), groups.find('c'))
        changed = copy.deepcopy(self.manifest)
        train = next(r for r in changed if r['modeling_status'] == 'included_development' and r['period'] == 'train')
        validation = next(r for r in changed if r['modeling_status'] == 'included_development' and r['period'] == 'validation')
        validation['family_id'] = train['family_id']
        with self.assertRaisesRegex(ValueError, 'crosses chronological'):
            verify_rows(changed, self.texts)

    def test_calibration_and_reserved_test_guards(self):
        changed = copy.deepcopy(self.manifest)
        next(r for r in changed if r['modeling_status'] == 'included_development' and r['period'] == 'validation')['calibration_exposure'] = True
        with self.assertRaisesRegex(ValueError, 'Calibration family'):
            verify_rows(changed, self.texts)
        changed = copy.deepcopy(self.manifest)
        next(r for r in changed if r['period'] == 'test')['label'] = 0
        with self.assertRaisesRegex(ValueError, 'Reserved test labels'):
            verify_rows(changed, self.texts)
        bad = copy.deepcopy(self.texts)
        bad.append({'case_id': 'reserved', 'batch': 'C', 'date_filed': '2024-01-01', 'period': 'test', 'texts': {'FULL': 'x', 'MASKED': 'x'}})
        with self.assertRaisesRegex(ValueError, 'coverage'):
            verify_rows(self.manifest, bad)

    def test_duplicate_ids_and_changed_text_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            verify_rows(self.manifest, self.texts + [self.texts[0]])
        changed = copy.deepcopy(self.texts)
        changed[0]['texts']['MASKED'] += ' revised'
        with self.assertRaisesRegex(ValueError, 'modified opinion'):
            verify_rows(self.manifest, changed)

    def test_tampered_release_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for path in self.folder.iterdir():
                (folder / path.name).write_bytes(path.read_bytes())
            with (folder / 'development.jsonl').open('a') as stream:
                stream.write('\n')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                load_release(folder / 'release.json')


if __name__ == '__main__':
    unittest.main()
