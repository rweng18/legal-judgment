"""Run majority, then MASKED-selected TF-IDF logistic regression on combined A-C."""
import argparse
import json
import subprocess
import sys
import warnings
from collections import Counter
from pathlib import Path

from prepare import HERE, ROOT, digest, load_release

# Reuse the validated B experiment implementation without changing its old runs.
SHARED = HERE.parent / 'provisional_b'
sys.path.insert(0, str(SHARED))
from experiment import save_run
from modeling import SEED, evaluate, grouped_folds
from outputs import new_directory, write_json
from reporting import report
from sklearn.exceptions import ConvergenceWarning


def check_folds(rows, folds):
    training = [r for r in rows if r['period'] == 'train']
    validation = [r for r in rows if r['period'] == 'validation']
    if {r['family_id'] for r in training} & {r['family_id'] for r in validation}:
        raise ValueError('Family crosses training/development boundary.')
    holds = []
    for fit, hold in folds:
        if set(fit) & set(hold) or set(fit) | set(hold) != set(range(len(training))):
            raise ValueError('Invalid fold coverage.')
        if {training[i]['family_id'] for i in fit} & {training[i]['family_id'] for i in hold}:
            raise ValueError('Family crosses a CV fold boundary.')
        if any({training[i]['label'] for i in indices} != {0, 1} for indices in (fit, hold)):
            raise ValueError('Fold lacks an outcome class.')
        holds.extend(hold.tolist())
    if sorted(holds) != list(range(len(training))):
        raise ValueError('Every training case must be held out exactly once.')


def write_report(out, results, rows, folds):
    training = [r for r in rows if r['period'] == 'train']
    validation = [r for r in rows if r['period'] == 'validation']
    counts = Counter(r['label'] for r in training)
    majority = max((0, 1), key=lambda label: (counts[label], -label))
    lr = results[1]
    lines = ['# Combined A-C majority and logistic-regression results', '',
             f"Training: {len(training)} cases (0: {counts[0]}, 1: {counts[1]}). "
             f"Evaluation: the same {len(validation)} development cases for every condition. "
             f"The training-majority classifier always predicts {majority}.", '',
             'A retains its team-reviewed source status. B and C labels are used under explicit user-authorized provisional assumptions; '
             'their pending-human-review statuses are preserved. No reserved test cases are evaluated.', '',
             '## MASKED training selection', '',
             f"{len(folds)} family-grouped folds within 2010–2020; batch-spanning families stay together. "
             'Select by mean balanced accuracy, then mean macro F1, then smaller C. '
             f"Selected **C = {lr['selected_C']:g}** is held fixed for the FULL/MASKED comparison.", '',
             '| C | Mean balanced accuracy | Mean macro F1 |', '|---:|---:|---:|']
    lines += [f"| {t['C']:g} | {t['balanced_accuracy']:.4f} | {t['macro_f1']:.4f} |" for t in lr['cv']]
    lines += ['', '## Development results', '',
              '| Model | Variant | Accuracy | Balanced accuracy | Macro F1 | Recall 0 | Recall 1 |',
              '|---|---|---:|---:|---:|---:|---:|']
    for result in results:
        for m in result['metrics']:
            values = ' | '.join(f'{m[k]:.4f}' for k in ('accuracy', 'balanced_accuracy', 'macro_f1', 'recall_0', 'recall_1'))
            lines.append(f"| {m['model']} | {m['variant']} | {values} |")
    lines += ['', 'TF-IDF uses word unigrams/bigrams, min_df=2, max_features=30000 and L2 vector normalization. '
              'Logistic regression uses L2 regularization, balanced training-class weights, liblinear, max_iter=10000 and seed '
              f'{SEED}. Each fold and each final text variant gets a fresh fitted pipeline. '
              'Vocabulary, IDF and class weights are learned from that fit subset only. No independent learned scaler is used for sparse TF-IDF.', '',
              '[Detailed reporting tables](REPORTING.md) include counts for each split and fold, raw and row-normalized confusion matrices, '
              'true rows and predicted columns ordered 0, 1. `batch_class_counts.csv` adds batch-specific split counts. '
              '`predictions.csv` retains all predictions and signed decision scores (not calibrated probabilities). '
              '`splits.csv` retains family IDs and CV membership; `selection.json` retains all candidate fold metrics.', '',
              '## Limits and reproduction', '',
              'These are development estimates on 42 decisions, not final-test results. A/B validation cases have been inspected previously. '
              'A and B/C use different upstream masking implementations. Two unresolved companion warnings and provisional family links remain. '
              'No labels, masks, source texts or earlier results were changed for this run.', '',
              'From `experiments/provisional_abc`, use the recorded Python version, install `requirements-lock.txt` from this run in a virtual environment, and run:', '',
              '```sh', 'python run_logistic.py inputs/abc_provisional_v1/release.json runs/abc_logistic_reproduction', '```', '',
              'Use a fresh output directory. `run.json` records the prepared release, exact source and implementation hashes, '
              'parameters, seed and software versions. `verification.json` records the run checks. '
              'The comparison is computed without loading an encoder or test texts.', '']
    (out / 'REPORT.md').write_text('\n'.join(lines), encoding='utf-8')


def run(release_path, destination):
    release_path, destination = Path(release_path).resolve(), Path(destination).resolve()
    if destination.exists():
        raise FileExistsError('Use a fresh output directory.')
    release_bytes = release_path.read_bytes()
    release, rows = load_release(release_path)
    training = [r for r in rows if r['period'] == 'train']
    folds = grouped_folds(training, SEED)
    check_folds(rows, folds)
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        results = [evaluate('Majority', rows, folds)]
        print('Training-majority evaluation complete.', flush=True)
        results.append(evaluate('TFIDF_LR', rows, folds))
        print(f"MASKED CV selected C = {results[1]['selected_C']:g}; FULL/MASKED evaluation complete.", flush=True)
    counts = Counter(r['label'] for r in training)
    majority = max((0, 1), key=lambda label: (counts[label], -label))
    if any(p['prediction'] != majority for p in results[0]['predictions']):
        raise ValueError('Majority prediction differs from the training majority.')
    load_release(release_path)  # Recheck input hashes after fitting.
    if release_path.read_bytes() != release_bytes:
        raise ValueError('Release metadata changed during the run.')
    code_paths = [HERE / 'prepare.py', Path(__file__), *[SHARED / n for n in
                  ('modeling.py', 'data.py', 'experiment.py', 'reporting.py', 'outputs.py', 'encoder.py')]]
    with new_directory(destination) as staging:
        out = save_run(staging / 'bundle', release, rows, folds, results)
        metadata = json.loads((out / 'run.json').read_text())
        metadata.update({
            'scope': 'Combined A-C development: Majority and TF-IDF logistic regression',
            'prepared_release_sha256': digest(release_bytes),
            'assumptions': json.loads((release_path.parent / 'assumptions.json').read_text()),
            'encoder_used': False,
            'implementation_sha256': {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in code_paths},
            'majority_training_label': majority,
            'effective_final_training_class_weights': {str(k): len(training) / (2 * counts[k]) for k in (0, 1)},
            'fold_training_class_weights': [
                {'fold': number, 'weights': {str(k): len(fit) / (2 * sum(training[i]['label'] == k for i in fit)) for k in (0, 1)}}
                for number, (fit, _) in enumerate(folds, 1)],
        })
        write_json(out / 'run.json', metadata)
        report(out)  # Verify saved predictions/metrics; refresh reporting metadata hashes.
        (out / 'batch_class_counts.csv').write_bytes((release_path.parent / 'class_counts.csv').read_bytes())
        installed = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True)
        (out / 'requirements-lock.txt').write_text(installed, encoding='utf-8')
        write_json(out / 'verification.json', {
            'same_evaluation_cases_and_labels': True, 'majority_from_training_only': True,
            'family_disjoint_folds': True, 'each_training_case_held_out_once': True,
            'both_classes_in_each_fold': True, 'masked_only_selection': True,
            'same_C_for_FULL_MASKED': True, 'metrics_recomputed_from_saved_predictions': True,
            'input_hashes_unchanged': True, 'convergence_warnings': 0,
            'reserved_test_evaluated': False, 'training_cases': len(training),
            'evaluation_cases': len(rows) - len(training), 'conditions': 4,
            'training_only_transform_basis': 'Fresh sklearn Pipeline fitted only on each training subset; guarded by synthetic held-out-vocabulary test.',
        })
        write_report(out, results, rows, folds)
        for path in out.iterdir():
            path.rename(staging / path.name)
        out.rmdir()
    print(destination)
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('release', type=Path)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    run(args.release, args.out)
