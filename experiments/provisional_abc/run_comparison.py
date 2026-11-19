"""Extend the saved A-C run with linear SVM, then frozen LEGAL-BERT + LR."""
import argparse
import contextlib
import csv
import io
import json
import subprocess
import sys
import time
import warnings
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import numpy as np

from prepare import HERE, ROOT, PRE, digest, load_release
from run_logistic import SHARED, check_folds
from encoder import SETTINGS, feature_vectors, load_tokenizer
from experiment import save_run
from lengths import measure
from modeling import BERT, SEED, evaluate
from outputs import new_directory, write_csv, write_json
from reporting import report
from sklearn.exceptions import ConvergenceWarning


def sha(path):
    return digest(Path(path).read_bytes())


def csv_rows(path):
    with Path(path).open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def reference_folds(rows, reference, release_path):
    meta = json.loads((reference / 'run.json').read_text())
    if meta['prepared_release_sha256'] != sha(release_path):
        raise ValueError('Prepared release differs from the reference run.')
    saved = csv_rows(reference / 'splits.csv')
    fields = ('case_id', 'family_id', 'batch', 'date_filed', 'label', 'period')
    if len(saved) != len(rows) or {tuple(r[k] for k in fields) for r in saved} != {tuple(str(r[k]) for k in fields) for r in rows}:
        raise ValueError('Case, label or split metadata differs from the reference.')
    membership = {r['case_id']: int(r['held_out_cv_fold']) for r in saved if r['period'] == 'train'}
    training = [r for r in rows if r['period'] == 'train']
    fold_ids = sorted(set(membership.values()))
    if fold_ids != list(range(1, len(fold_ids) + 1)) or len(fold_ids) not in (2, 3):
        raise ValueError('Invalid saved fold numbers.')
    assigned = np.array([membership[r['case_id']] for r in training])
    folds = [(np.flatnonzero(assigned != f), np.flatnonzero(assigned == f)) for f in fold_ids]
    check_folds(rows, folds)
    return folds, meta


def verify_reproduction(result, reference):
    selection = json.loads((reference / 'selection.json').read_text())
    name = result['model']
    if name not in selection:
        return None
    if selection[name] != {'selected_C': result['selected_C'], 'grid': result['cv']}:
        raise ValueError(f'{name} model selection differs from the reference.')
    old = {(r['case_id'], r['variant']): r for r in csv_rows(reference / 'predictions.csv') if r['model'] == name}
    if len(old) != len(result['predictions']):
        raise ValueError('Reference prediction coverage differs.')
    differences = []
    for current in result['predictions']:
        prior = old[current['case_id'], current['variant']]
        for field in ('label', 'prediction', 'family_id', 'batch', 'period'):
            if prior[field] != str(current[field]):
                raise ValueError(f'{name} prediction or metadata changed: {current["case_id"]}')
        if current['decision_score'] is not None:
            delta = abs(float(prior['decision_score']) - current['decision_score'])
            if delta > 1e-12:
                raise ValueError('Reference decision score differs beyond floating-point tolerance.')
            differences.append(delta)
    return {'predictions_and_selection_identical': True, 'max_decision_score_difference': max(differences, default=0)}


def encoder_features(rows):
    # Verify the cached pinned checkpoint against the completed B run before use.
    reference = SHARED / 'runs/b_bert_assumed_reviewed_v1/verification.json'
    expected = json.loads(reference.read_text())['checkpoint_files_sha256']
    snapshot = SHARED / '.cache/huggingface' / ('models--' + SETTINGS['encoder'].replace('/', '--')) / 'snapshots' / SETTINGS['revision']
    actual = {name: sha(snapshot / name) for name in expected}
    if actual != expected:
        raise ValueError('Checkpoint differs from the previously verified pinned encoder.')
    tokenizer = load_tokenizer()
    lengths, summary = measure({r['case_id']: r for r in rows}, tokenizer)
    counts = {r['case_id']: r for r in lengths}
    length_references = {}
    for batch in 'BC':
        path = ROOT / PRE / f'batch_{batch.lower()}/provisional_v1/{batch}_v2_exact_token_lengths/case_lengths.csv'
        prior = csv_rows(path)
        if {r['case_id'] for r in prior} != {r['case_id'] for r in rows if r['batch'] == batch}:
            raise ValueError('Upstream length-reference case IDs differ.')
        for r in prior:
            for v in ('FULL', 'MASKED'):
                for unit in ('words', 'tokens', 'chunks', 'final_chunk'):
                    if counts[r['case_id']][v + '_' + unit] != int(r[v + '_' + unit]):
                        raise ValueError('Token/chunk counts differ from the supplied package.')
        length_references[str(path.relative_to(ROOT))] = sha(path)
    cache = SHARED / '.cache/vectors'
    before = len(list(cache.glob('*.npy')))
    started = time.perf_counter()
    vectors = feature_vectors(rows, cache, SEED)
    seconds = time.perf_counter() - started
    # This second load must be cache-only; a missing vector would raise here.
    with contextlib.redirect_stdout(io.StringIO()), patch('transformers.AutoModel.from_pretrained', side_effect=AssertionError('Unexpected encoder reload')):
        cached = feature_vectors(rows, cache, SEED)
    if any(not np.array_equal(vectors[v], cached[v]) for v in ('FULL', 'MASKED')):
        raise ValueError('Cache reload differs from extracted vectors.')
    verification = {
        'encoder_frozen': True, 'encoder_fine_tuned': False, 'checkpoint_files_sha256': actual,
        'checkpoint_reference_sha256': sha(reference), 'tokenizer_class': type(tokenizer).__name__,
        'all_chunks_used': True, 'content_tokens_per_chunk': 510, 'cache_only_reload_identical': True,
        'cache_entries_before': before, 'cache_entries_after': len(list(cache.glob('*.npy'))),
        'encoder_seconds': seconds, 'supplied_B_C_length_counts_match': True,
        'length_reference_sha256': length_references,
    }
    return vectors, lengths, summary, verification


def write_report(out, results, folds, encoder_used):
    lines = ['# A-C model comparison', '',
             '279 training cases from 2010–2020; the same 42 development cases from 2021–2022 for every model and text variant. '
             'Training labels: 181 affirmed / 98 reversed-vacated. Evaluation labels: 25 / 17. '
             'The majority classifier predicts label 0 throughout.', '',
             'A retains team-reviewed status. B/C use explicit user-authorized provisional assumptions; source review statuses remain pending. '
             'The original combined logistic run and prepared dataset are preserved. No test texts, labels or model evaluations enter this run.', '',
             '## Selection and transformations', '',
             f'The {len(folds)} saved training folds are reused exactly, preserving cross-batch families. '
             'Each learned model selects its own C on MASKED training-fold performance: mean balanced accuracy first, mean macro F1 next, '
             'then smaller C for a tie. Its selected C is fixed for separate FULL/MASKED fits.', '',
             '| Model | C | Mean CV balanced accuracy | Mean CV macro F1 | Selected |', '|---|---:|---:|---:|---|']
    for r in results:
        for t in r['cv']:
            lines.append(f"| {r['model']} | {t['C']:g} | {t['balanced_accuracy']:.4f} | {t['macro_f1']:.4f} | {'yes' if t['C'] == r['selected_C'] else ''} |")
    lines += ['', 'TF-IDF LR and linear SVM share word unigrams/bigrams, min_df=2, max_features=30000 and L2 TF-IDF normalization. '
              'Vocabulary, IDF and balanced class weights are fitted only within the relevant training fold. '
              'The final variants each fit a fresh pipeline on all training cases. No additional learned scaler is needed for TF-IDF. '
              'Seed: 20261023. Full parameters and effective class weights are saved in `run.json`.', '']
    if encoder_used:
        lines += [f"Frozen encoder: `{SETTINGS['encoder']}`, revision `{SETTINGS['revision']}`. "
                  'Each chunk contains at most 510 content tokens plus CLS/SEP; no overlap or truncation. '
                  'Mean pooling excludes specials and padding, and opinion pooling weights chunks by content-token count. '
                  'Every chunk contributes. The encoder runs in evaluation/inference mode with gradients disabled and is never fine-tuned. '
                  'StandardScaler and balanced L2 logistic regression stay inside the training-fold pipeline. '
                  'Cache keys include exact text, pinned settings, encoder code and software versions; cache-only reload was checked.', '']
    lines += ['## Shared development results', '',
              '| Model | Variant | C | Accuracy | Balanced accuracy | Macro F1 | Recall 0 | Recall 1 |',
              '|---|---|---:|---:|---:|---:|---:|---:|']
    for result in results:
        for r in result['metrics']:
            values = ' | '.join(f"{r[k]:.4f}" for k in ('accuracy', 'balanced_accuracy', 'macro_f1', 'recall_0', 'recall_1'))
            c = '—' if r['C'] is None else f"{r['C']:g}"
            lines.append(f"| {r['model']} | {r['variant']} | {c} | {values} |")
    lines += ['', '[REPORTING.md](REPORTING.md) provides raw and row-normalized confusion matrices (true rows, predicted columns; labels 0, 1), '
              'per-class recall, and split/fold counts. `predictions.csv` preserves every prediction, including failures; '
              '`splits.csv` records the identical evaluation IDs and family-grouped CV assignments. '
              '`batch_class_counts.csv` preserves split counts by source batch.', '',
              '## Reproduction and limitations', '',
              'The FULL/MASKED comparison uses fixed selected settings but separately fitted pipelines; it is not a same-model phrase-deletion experiment. '
              'The small development set, previous A/B development inspection, different upstream masking pipelines, pending B/C human review '
              'and unresolved family-companion warnings limit interpretation. No labels or masks were changed to improve results.', '',
              'Install this run’s `requirements-lock.txt` using the Python version in `run.json`. '
              'From `experiments/provisional_abc`, use a fresh output directory:', '', '```sh',
              ('HF_HUB_OFFLINE=1 python run_comparison.py inputs/abc_provisional_v1/release.json runs/abc_svm_provisional_v1 runs/abc_complete_reproduction' if encoder_used else
               'python run_comparison.py inputs/abc_provisional_v1/release.json runs/abc_logistic_provisional_v1 runs/abc_svm_reproduction --lexical-only'),
              '```', '',
              'For the encoder stage, the checkpoint must already be installed in the shared B cache; '
              '`../provisional_b/download_encoder.py` downloads the pinned revision when needed. '
              'The completed B checkpoint checksums are verified before use. Full runs save both portable embedding matrices and their row index. '
              'No encoder access is needed to inspect or verify the saved results. '
              '`run.json`, `selection.json`, `verification.json` and implementation hashes document the run.', '']
    (out / 'REPORT.md').write_text('\n'.join(lines), encoding='utf-8')


def run(release_path, reference, destination, lexical_only=False):
    release_path, reference, destination = map(lambda p: Path(p).resolve(), (release_path, reference, destination))
    if destination.exists():
        raise FileExistsError('Choose a new output directory.')
    release_hash = sha(release_path)
    release, rows = load_release(release_path)
    folds, previous = reference_folds(rows, reference, release_path)
    reference_hashes = {name: sha(reference / name) for name in ('run.json', 'splits.csv', 'selection.json', 'predictions.csv')}
    reproduction = {}
    vectors = lengths = summary = None
    encoder_verification = {}
    results = []
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        for name in ('Majority', 'TFIDF_LR', 'TFIDF_SVM'):
            result = evaluate(name, rows, folds)
            verified = verify_reproduction(result, reference)
            if verified is not None:
                reproduction[name] = verified
            results.append(result)
            print(f"{name}: C={result['selected_C']}; {'reference reproduced' if verified else 'new model complete'}", flush=True)
        if not lexical_only:
            vectors, lengths, summary, encoder_verification = encoder_features(rows)
            results.append(evaluate(BERT, rows, folds, vectors))
            print(f"Frozen LEGAL-BERT LR: selected C={results[-1]['selected_C']}", flush=True)
    load_release(release_path)
    if sha(release_path) != release_hash or any(sha(reference / n) != h for n, h in reference_hashes.items()):
        raise ValueError('Input or prior results changed during execution.')
    paths = [HERE / n for n in ('prepare.py', 'run_logistic.py', 'run_comparison.py')]
    paths += [SHARED / n for n in ('modeling.py', 'data.py', 'encoder.py', 'encoder_settings.json', 'experiment.py', 'outputs.py', 'reporting.py', 'lengths.py')]
    with new_directory(destination) as staging:
        out = save_run(staging / 'bundle', release, rows, folds, results, vectors=vectors)
        meta = json.loads((out / 'run.json').read_text())
        meta.update({
            'scope': 'A-C lexical comparison' if lexical_only else 'A-C complete frozen-encoder comparison',
            'prepared_release_sha256': release_hash, 'reference_run': str(reference.relative_to(ROOT)),
            'reference_run_sha256': reference_hashes, 'assumptions': previous['assumptions'],
            'encoder_used': not lexical_only,
            'implementation_sha256': {str(p.relative_to(ROOT)): sha(p) for p in paths},
            **{key: previous[key] for key in ('majority_training_label', 'effective_final_training_class_weights', 'fold_training_class_weights')},
        })
        write_json(out / 'run.json', meta)
        report(out)
        (out / 'batch_class_counts.csv').write_bytes((release_path.parent / 'class_counts.csv').read_bytes())
        if vectors is not None:
            write_csv(out / 'case_lengths.csv', lengths)
            write_json(out / 'length_summary.json', {'encoder': SETTINGS, 'splits': summary})
        write_json(out / 'verification.json', {
            'reference_reproduction': reproduction, 'saved_training_folds_reused': True,
            'family_disjoint_folds': True, 'same_evaluation_cases_and_labels': True,
            'masked_only_selection': True, 'fixed_selected_C_across_variants': True,
            'input_hashes_unchanged': True, 'metrics_recomputed_from_predictions': True,
            'reserved_test_evaluated': False, 'convergence_warnings': 0,
            'training_cases': 279, 'evaluation_cases': 42, 'conditions': len(results) * 2,
            **encoder_verification,
        })
        installed = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True)
        (out / 'requirements-lock.txt').write_text(installed, encoding='utf-8')
        write_report(out, results, folds, not lexical_only)
        for path in out.iterdir():
            path.rename(staging / path.name)
        out.rmdir()
    print(destination)
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('release', type=Path)
    parser.add_argument('reference', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('--lexical-only', action='store_true')
    args = parser.parse_args()
    run(args.release, args.reference, args.out, args.lexical_only)
