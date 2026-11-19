"""Checks specific to saved-fold reuse and the SVM/frozen-feature extension."""
import copy
import csv
import tempfile
import unittest
from pathlib import Path

import numpy as np

from prepare import HERE, load_release
from run_comparison import reference_folds
from modeling import BERT, estimator, evaluate, grouped_folds


class ComparisonTests(unittest.TestCase):
    def test_reference_folds_are_reused_by_case_id(self):
        path = HERE / 'inputs/abc_provisional_v1/release.json'
        _, rows = load_release(path)
        reference = HERE / 'runs/abc_logistic_provisional_v1'
        folds, _ = reference_folds(rows, reference, path)
        training = [r for r in rows if r['period'] == 'train']
        saved = [{training[i]['case_id'] for i in hold} for _, hold in folds]
        reversed_rows = list(reversed(rows))
        reverse_folds, _ = reference_folds(reversed_rows, reference, path)
        reverse_train = [r for r in reversed_rows if r['period'] == 'train']
        self.assertEqual(saved, [{reverse_train[i]['case_id'] for i in hold} for _, hold in reverse_folds])

    def test_corrupt_family_fold_assignment_is_rejected(self):
        path = HERE / 'inputs/abc_provisional_v1/release.json'
        _, rows = load_release(path)
        reference = HERE / 'runs/abc_logistic_provisional_v1'
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            (folder / 'run.json').write_bytes((reference / 'run.json').read_bytes())
            with (reference / 'splits.csv').open(newline='') as stream:
                records = list(csv.DictReader(stream))
            member = next(r for r in records if r['case_id'] == 'NY-6228997')
            member['held_out_cv_fold'] = str(int(member['held_out_cv_fold']) % 3 + 1)
            with (folder / 'splits.csv').open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(records[0]))
                writer.writeheader()
                writer.writerows(records)
            with self.assertRaisesRegex(ValueError, 'Family crosses a CV'):
                reference_folds(rows, folder, path)

    def test_svm_and_encoder_transforms_fit_training_only(self):
        svm = estimator('TFIDF_SVM', 1)
        svm.fit(['shared apple', 'shared apple', 'shared pear', 'shared pear'], [0, 0, 0, 1])
        vectorizer = svm.steps[0][1]
        idf = vectorizer.idf_.copy()
        svm.predict(['holdoutonly shared', 'holdoutonly shared'])
        self.assertNotIn('holdoutonly', vectorizer.vocabulary_)
        np.testing.assert_array_equal(idf, vectorizer.idf_)
        explicit = estimator('TFIDF_SVM', 1)
        explicit.steps[-1][1].set_params(class_weight={0: 4/6, 1: 2})
        explicit.fit(['shared apple', 'shared apple', 'shared pear', 'shared pear'], [0, 0, 0, 1])
        np.testing.assert_allclose(svm.steps[-1][1].coef_, explicit.steps[-1][1].coef_)
        bert = estimator(BERT, 1)
        x = np.array([[0., 1.], [1., 2.], [2., 3.], [3., 4.]])
        bert.fit(x, [0, 0, 0, 1])
        bert.predict([[10000., -10000.]])
        np.testing.assert_allclose(bert.steps[0][1].mean_, x.mean(axis=0))
        np.testing.assert_allclose(bert.steps[0][1].var_, x.var(axis=0))

    def test_svm_and_encoder_selection_ignore_full_and_validation(self):
        rows = [{'case_id': str(i), 'family_id': str(i), 'batch': 'ABC'[i % 3],
                 'period': 'train' if i < 12 else 'validation', 'label': i % 2,
                 'texts': {'FULL': 'shared apple pear', 'MASKED': 'shared ' + ('apple apple' if i % 2 else 'pear pear')}}
                for i in range(16)]
        folds = grouped_folds(rows[:12])
        x = np.array([[i % 2, i % 3, i / 16] for i in range(16)])
        vectors = {'FULL': x.copy(), 'MASKED': x.copy()}
        for name in ('TFIDF_SVM', BERT):
            original = evaluate(name, rows, folds, vectors if name == BERT else None)
            changed = copy.deepcopy(rows)
            for r in changed:
                r['texts']['FULL'] = 'changed full input'
                if r['period'] == 'validation':
                    r['texts']['MASKED'] = 'changed development input'
                    r['label'] = 1 - r['label']
            altered_vectors = {'FULL': np.zeros_like(x), 'MASKED': x.copy()}
            altered_vectors['MASKED'][12:] = 1000
            alternate = evaluate(name, changed, folds, altered_vectors if name == BERT else None)
            self.assertEqual(original['cv'], alternate['cv'])
            self.assertEqual(original['selected_C'], alternate['selected_C'])


if __name__ == '__main__':
    unittest.main()
