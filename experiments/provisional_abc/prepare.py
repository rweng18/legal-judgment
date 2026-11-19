"""Combine existing A-C development packages without training or promoting review status."""
import argparse
import csv
import hashlib
import json
import subprocess
import tempfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
A = Path('experiments/mvp_a')
PRE = Path('annotation/submissions/hyunsang/preprocessing')
GLOBAL_FAMILIES = Path('annotation/submissions/becca/MVP/data/family_v1/case_family_manifest.jsonl')
YINKUI_C_REVISION = '87f7771b01cb8fcd75860e240c0b075a09bb3f61'
YINKUI_C_PATH = 'annotation/submissions/yinkui/batches/C/annotations.jsonl'
VARIANTS = ('FULL', 'MASKED')


def digest(value):
    return hashlib.sha256(value).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def write_rows(path, rows):
    path.write_text(''.join(json.dumps(r, ensure_ascii=False, allow_nan=False) + '\n' for r in rows), encoding='utf-8')


def keyed(rows):
    mapped = {r['case_id']: r for r in rows}
    if len(mapped) != len(rows):
        raise ValueError('Duplicate case IDs in an input.')
    return mapped


def period(value):
    year = date.fromisoformat(value).year
    if not 2010 <= year <= 2024:
        raise ValueError('Date outside experiment periods.')
    return 'train' if year <= 2020 else 'validation' if year <= 2022 else 'test'


class Families:
    def __init__(self, ids):
        self.parent = {k: k for k in ids}
        self.edges = []

    def find(self, k):
        if self.parent[k] != k:
            self.parent[k] = self.find(self.parent[k])
        return self.parent[k]

    def union(self, ids, basis):
        ids = sorted(set(ids))
        if not set(ids) <= self.parent.keys():
            raise ValueError('Unknown family member.')
        for k in ids[1:]:
            a, b = self.find(ids[0]), self.find(k)
            self.parent[max(a, b)] = min(a, b)
            self.edges.append({'a': ids[0], 'b': k, 'basis': basis})


def verify_rows(manifest, development):
    meta, texts = keyed(manifest), keyed(development)
    expected = {k for k, r in meta.items() if r['modeling_status'] == 'included_development'}
    if set(texts) != expected:
        raise ValueError('Development coverage differs from manifest.')
    groups = defaultdict(list)
    for r in manifest:
        if r['period'] != period(r['date_filed']) or r['batch'] not in 'ABC':
            raise ValueError('Invalid batch or chronological split.')
        groups[r['family_id']].append(r)
        if r['period'] == 'test' and r['label'] is not None:
            raise ValueError('Reserved test labels must not be exported.')
    for members in groups.values():
        active = [r for r in members if r['case_id'] in expected]
        if active and len({r['period'] for r in members}) > 1:
            raise ValueError('Development family crosses chronological periods.')
        if active and any(r['calibration_exposure'] for r in members) and any(r['period'] != 'train' for r in active):
            raise ValueError('Calibration family outside training.')
    for k, r in texts.items():
        if r['period'] not in ('train', 'validation') or any(r[f] != meta[k][f] for f in ('batch', 'date_filed', 'period')):
            raise ValueError('Test text or inconsistent metadata in development.')
        if type(meta[k]['label']) is not int or meta[k]['label'] not in (0, 1):
            raise ValueError('Invalid development label.')
        if set(r['texts']) != set(VARIANTS):
            raise ValueError('Expected exactly FULL/MASKED texts.')
        for v in VARIANTS:
            text = r['texts'][v]
            if not isinstance(text, str) or not text.strip() or digest(text.encode()) != meta[k]['text_sha256'][v]:
                raise ValueError('Missing or modified opinion text.')
    if {r['batch'] for r in development} != set('ABC'):
        raise ValueError('All three batches must contribute development cases.')


def load_release(path):
    path = Path(path)
    release = json.loads(path.read_text())
    if release['status'] != 'provisional_user_authorized' or release['models_run']:
        raise ValueError('Expected the authorized preparation-only release.')
    for name, checksum in release['sha256'].items():
        if Path(name).name != name or digest((path.parent / name).read_bytes()) != checksum:
            raise ValueError(f'Release checksum mismatch: {name}')
    manifest = [json.loads(l) for l in (path.parent / 'manifest.jsonl').read_text().splitlines()]
    development = [json.loads(l) for l in (path.parent / 'development.jsonl').read_text().splitlines()]
    verify_rows(manifest, development)
    meta = keyed(manifest)
    return release, [{**meta[r['case_id']], 'texts': r['texts']} for r in development]


def prepare(destination):
    destination = Path(destination).resolve()
    if destination.exists():
        raise FileExistsError('Choose a fresh output directory; previous releases are preserved.')
    source_hashes = {}

    def raw(name):
        data = (ROOT / name).read_bytes()
        source_hashes[str(name)] = digest(data)
        return data

    def obj(name):
        return json.loads(raw(name))

    def rows(name):
        return keyed([json.loads(l) for l in raw(name).decode().splitlines() if l.strip()])

    def table(name):
        return keyed(list(csv.DictReader(raw(name).decode().splitlines())))

    assumptions = obj(HERE.relative_to(ROOT) / 'assumptions.json')
    raw(A / 'team_review_confirmation.json')
    raw(A / 'outputs/data_provenance.json')
    global_meta = rows(GLOBAL_FAMILIES)
    batch_ids = {b: set(obj(Path(f'annotation/batches/{b}/manifest.json'))['case_ids']) for b in 'ABC'}
    ids = [k for values in batch_ids.values() for k in values]
    if len(ids) != len(set(ids)) or set(ids) != global_meta.keys():
        raise ValueError('Batch manifests overlap or differ from the global source inventory.')
    calibration = set(obj(Path('annotation/calibration/manifest.json'))['case_ids'])
    families = Families(ids)
    for r in global_meta.values():
        families.union(r['family_member_case_ids'], 'existing_global_family_manifest')
    for group in obj(Path('annotation/source/family_hints.json'))['groups']:
        families.union(group['case_ids'], 'existing_source_family_hint')
    same_hash = defaultdict(list)
    for k, r in global_meta.items():
        same_hash[r['text_sha256']].append(k)
    for group in same_hash.values():
        families.union(group, 'identical_source_text')
    a_meta = rows(A / 'outputs/case_manifest.jsonl')
    a_dev = rows(A / 'outputs/development_cases.jsonl')
    prepared = {'A': a_dev}
    audits, batch_families = {}, {}
    for b, count in (('B', 169), ('C', 168)):
        folder = PRE / f'batch_{b.lower()}/provisional_v1'
        audits[b] = table(folder / ('inputs' if b == 'B' else '') / f'{b}_three_reviewer_audit_{count}.csv')
        batch_families[b] = table(folder / f'case_family_manifest_{b}_{count}_PROVISIONAL.csv')
        prepared[b] = rows(folder / f'{b}_development_v2_PROVISIONAL.jsonl')
        raw(folder / 'masking_removal_logs_v2.jsonl')
        raw(folder / 'SUBMISSION_README.md')
        for r in batch_families[b].values():
            families.union(r['family_members'].split(';'), f'{b}_provisional_family_manifest')
    ybytes = subprocess.check_output(['git', 'show', f'{YINKUI_C_REVISION}:{YINKUI_C_PATH}'], cwd=ROOT)
    reviews = {name: rows(Path(f'annotation/submissions/{name}/batches/C/annotations.jsonl')) for name in ('becca', 'hyunsang')}
    reviews['yinkui'] = keyed([json.loads(l) for l in ybytes.decode().splitlines()])
    if any(set(r) != batch_ids['C'] for r in reviews.values()):
        raise ValueError('Incomplete C reviewer coverage.')
    c_votes = []
    for k in sorted(prepared['C']):
        votes = {name: {'label': r[k]['outcome']['binary_label'], 'eligibility': r[k]['eligibility']['binary_task'],
                        'source_review_status': r[k]['run']['review_status'], 'source_text_sha256': r[k]['text_sha256']}
                 for name, r in reviews.items()}
        if any(v['eligibility'] != 'include' or v['source_text_sha256'] != global_meta[k]['text_sha256'] for v in votes.values()):
            raise ValueError(f'C source/eligibility mismatch: {k}')
        labels = [v['label'] for v in votes.values()]
        if any(type(v) is not int or v not in (0, 1) for v in labels) or len(set(labels)) != 1:
            raise ValueError(f'C label disagreement requires explicit review: {k}')
        c_votes.append({'case_id': k, 'label': labels[0], 'votes': votes})
    c_labels = {r['case_id']: r['label'] for r in c_votes}
    same_full = defaultdict(list)
    for b, records in prepared.items():
        if not records.keys() <= batch_ids[b]:
            raise ValueError('Prepared case assigned to the wrong batch.')
        for k, r in records.items():
            same_full[digest(r['texts']['FULL'].encode())].append(k)
    for group in same_full.values():
        families.union(group, 'identical_prepared_FULL')
    manifest, development = [], []
    for b in 'ABC':
        for k in sorted(batch_ids[b]):
            global_row = global_meta[k]
            source = a_meta.get(k, {}) if b == 'A' else audits[b][k]
            sp = period(global_row['date_filed'])
            included = k in prepared[b]
            label = None
            if included:
                if b == 'A':
                    if source['status'] != 'assigned' or source['review_status'] != 'team_reviewed':
                        raise ValueError('Unexpected A source status.')
                    label = source['label']
                else:
                    if source['unanimous_eligibility'] != 'include':
                        raise ValueError('Non-unanimous prepared case.')
                    label = int(source['draft_label_if_unanimous_include']) if b == 'B' else c_labels[k]
                r = prepared[b][k]
                if r['date_filed'] != global_row['date_filed'] or r['period'] != sp:
                    raise ValueError('Upstream split/date mismatch.')
                if source.get('source_text_sha256') != global_row['text_sha256']:
                    raise ValueError('Source text checksum mismatch.')
                development.append({'case_id': k, 'batch': b, 'date_filed': r['date_filed'], 'period': sp,
                                    'texts': {v: r['texts'][v] for v in VARIANTS}})
            meta = {'case_id': k, 'batch': b, 'date_filed': global_row['date_filed'], 'period': sp,
                    'family_id': 'ABC-FAM-' + families.find(k), 'source_family_id': source.get('family_id', source.get('family_id_provisional')),
                    'label': label, 'modeling_status': 'included_development' if included else 'reserved_test' if sp == 'test' else 'upstream_not_selected',
                    'source_review_status': source.get('review_status', source.get('adjudication_status', 'not_in_reviewed_A_selection')),
                    'label_basis': ('team_reviewed_A' if b == 'A' else 'supplied_B_draft_label_under_user_assumption' if b == 'B' else 'three_reviewer_C_consensus_under_user_assumption') if included else None,
                    'source_selection_status': source.get('status', source.get('unanimous_eligibility') or 'disagreement_or_unselected'),
                    'calibration_exposure': k in calibration or global_row['family_training_only'],
                    'family_review_status': 'upstream_family_links_preserved; combined_union_provisional',
                    'external_companion_unresolved': global_row['external_companion_unresolved'],
                    'source_text_sha256': global_row['text_sha256'],
                    'text_sha256': {v: digest(prepared[b][k]['texts'][v].encode()) for v in VARIANTS} if included else {}}
            manifest.append(meta)
    verify_rows(manifest, development)
    groups = defaultdict(list)
    for r in manifest:
        groups[r['family_id']].append(r)
    family_audit = {'edges': families.edges, 'groups': [
        {'family_id': g, 'case_ids': [r['case_id'] for r in members], 'batches': sorted({r['batch'] for r in members}),
         'periods': sorted({r['period'] for r in members}), 'development_case_ids': [r['case_id'] for r in members if r['modeling_status'] == 'included_development']}
        for g, members in sorted(groups.items()) if len(members) > 1],
        'unresolved_companions_in_development': [r['case_id'] for r in manifest if r['external_companion_unresolved'] and r['modeling_status'] == 'included_development'],
        'cross_period_development_families': [], 'limitation': 'Existing candidate links, not fresh legal adjudication or proof of independent families. No case is dropped or relabeled by this combination.'}
    counts = []
    for b in (*'ABC', 'ALL'):
        for sp in ('train', 'validation'):
            yy = Counter(r['label'] for r in manifest if r['modeling_status'] == 'included_development' and r['period'] == sp and (b == 'ALL' or r['batch'] == b))
            counts.append({'batch': b, 'split': sp, 'label_0': yy[0], 'label_1': yy[1], 'n': sum(yy.values())})
    summary = {'candidate_cases': len(manifest), 'development_cases': len(development), 'class_counts': counts,
               'cross_batch_family_groups': sum(len(g['batches']) > 1 for g in family_audit['groups']),
               'unresolved_companions_in_development': family_audit['unresolved_companions_in_development'],
               'models_run': False, 'test_texts_exported': False, 'test_labels_exported': False,
               'source_review_statuses': {b: sorted({r['source_review_status'] for r in manifest if r['batch'] == b and r['modeling_status'] == 'included_development'}) for b in 'ABC'},
               'masking_policy': 'Exact existing strings; A masker_v2 and B/C mask_v2_abbreviation_boundary_pre_review are different upstream pipelines.'}
    for name, checksum in source_hashes.items():
        if digest((ROOT / name).read_bytes()) != checksum:
            raise ValueError('Input changed during preparation.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        out = Path(tmp) / 'release'
        out.mkdir()
        write_rows(out / 'manifest.jsonl', manifest)
        write_rows(out / 'development.jsonl', development)
        write_rows(out / 'C_label_provenance.jsonl', c_votes)
        write_json(out / 'assumptions.json', assumptions)
        write_json(out / 'family_audit.json', family_audit)
        write_json(out / 'summary.json', summary)
        with (out / 'class_counts.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(counts[0]), lineterminator='\n')
            writer.writeheader()
            writer.writerows(counts)
        write_json(out / 'release.json', {
            'status': 'provisional_user_authorized', 'dataset_version': 'abc_provisional_v1',
            'split_version': '2010-2020_train__2021-2022_validation__2023-2024_reserved',
            'mask_version': 'upstream_by_batch_no_reprocessing', 'models_run': False,
            'class_order': [0, 1], 'class_names': ['affirmed', 'reversed/vacated'],
            'source_sha256': source_hashes,
            'yinkui_C_git_source': {'commit': YINKUI_C_REVISION, 'path': YINKUI_C_PATH, 'sha256': digest(ybytes)},
            'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'preparation_code_sha256': digest(Path(__file__).read_bytes()),
            'sha256': {p.name: digest(p.read_bytes()) for p in sorted(out.iterdir())},
            'limitations': ['B/C labels authorized provisionally, not human gold.', 'A-C families need joint confirmation; unresolved companions retained.', 'Batch-specific masking and prior development exposure limit interpretation.']})
        load_release(out / 'release.json')
        out.rename(destination)
    print(json.dumps(summary, indent=2))
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE / 'inputs/abc_provisional_v1')
    prepare(parser.parse_args().out)
