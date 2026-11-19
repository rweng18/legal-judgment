"""Verify fold separation and training-only feature learning before the A-C run."""
import unittest

import numpy as np

from prepare import HERE, load_release
from run_logistic import check_folds, grouped_folds
from modeling import estimator, evaluate


class LogisticTests(unittest.TestCase):
    def test_combined_folds_keep_cross_batch_families_together(self):
        _, rows = load_release(HERE / 'inputs/abc_provisional_v1/release.json')
        training = [r for r in rows if r['period'] == 'train']
        folds = grouped_folds(training)
        check_folds(rows, folds)
        self.assertEqual(len(folds), 3)
        family_folds = {}
        for f, (_, hold) in enumerate(folds):
            for i in hold:
                group = training[i]['family_id']
                self.assertEqual(family_folds.setdefault(group, f), f)

    def test_vocabulary_idf_and_class_weights_fit_only_training(self):
        model = estimator('TFIDF_LR', 1)
        train = ['shared apple', 'shared apple', 'shared pear', 'shared pear']
        model.fit(train, [0, 0, 0, 1])
        vectorizer = model.steps[0][1]
        before = vectorizer.idf_.copy()
        model.predict(['holdoutonly shared', 'holdoutonly shared'])
        self.assertNotIn('holdoutonly', vectorizer.vocabulary_)
        np.testing.assert_array_equal(before, vectorizer.idf_)
        self.assertAlmostEqual(vectorizer.idf_[vectorizer.vocabulary_['apple']], np.log(5 / 3) + 1)
        explicit = estimator('TFIDF_LR', 1)
        explicit.steps[-1][1].set_params(class_weight={0: 4/6, 1: 2})
        explicit.fit(train, [0, 0, 0, 1])
        np.testing.assert_allclose(model.steps[-1][1].coef_, explicit.steps[-1][1].coef_)

    def test_selection_ignores_full_and_validation_inputs(self):
        rows = [{'case_id': str(i), 'family_id': str(i), 'batch': 'ABC'[i % 3],
                 'period': 'train' if i < 12 else 'validation', 'label': i % 2,
                 'texts': {'FULL': 'shared apple pear', 'MASKED': 'shared ' + ('apple apple' if i % 2 else 'pear pear')}}
                for i in range(16)]
        folds = grouped_folds(rows[:12])
        original = evaluate('TFIDF_LR', rows, folds)
        for r in rows:
            r['texts']['FULL'] = 'replacement full words'
            if r['period'] == 'validation':
                r['label'] = 1 - r['label']
                r['texts']['MASKED'] = 'replacement evaluation words'
        changed = evaluate('TFIDF_LR', rows, folds)
        self.assertEqual(original['cv'], changed['cv'])
        self.assertEqual(original['selected_C'], changed['selected_C'])


if __name__ == '__main__':
    unittest.main()
