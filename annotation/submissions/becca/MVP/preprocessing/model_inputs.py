"""Validate approved text exports and join separate targets by case ID.

Only ModelBatch.texts may be passed to a text tokenizer/vectorizer. Targets are
supervision/scoring data; IDs are bookkeeping. No annotation metadata is returned.
"""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

VARIANTS = {"FULL": "full_v1/full.jsonl", "MASKED": "masked_v2/masked.jsonl"}
PARTITIONS = ("train", "development", "test")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def index_unique(records, name):
    result = {}
    for row in records:
        require(isinstance(row, dict), f"{name}: record must be an object")
        cid = row.get("case_id")
        require(isinstance(cid, str) and cid, f"{name}: missing/invalid case ID")
        require(cid not in result, f"{name}: duplicate case ID {cid}")
        result[cid] = row
    return result


def validate_records(exports, manifest):
    """Schema/coverage guard, separated from disk I/O for failure-path checks."""
    require(set(exports) == set(VARIANTS), "Expected FULL and MASKED exports")
    cases = index_unique(manifest["cases"], "split manifest")
    require(len(cases) == 114, "Expected frozen 114-case selection")
    indexed = {}
    for variant, records in exports.items():
        for row in records:
            require(isinstance(row, dict) and set(row) == {"case_id", "text"},
                    f"{variant}: allowed fields are exactly case_id and text")
            require(isinstance(row["text"], str), f"{variant}: text must be a string")
        indexed[variant] = index_unique(records, variant)
        require(set(indexed[variant]) == set(cases), f"{variant}: IDs differ from frozen selection")
    assigned = set()
    family_partition = {}
    for partition in PARTITIONS:
        ids = manifest["split_case_ids"][partition]
        require(len(ids) == len(set(ids)), f"{partition}: duplicate split ID")
        for cid in ids:
            require(cid in cases and cid not in assigned, "Unknown or overlapping split ID")
            assigned.add(cid)
            row = cases[cid]
            require(row["split"] == partition and row["status"] == "assigned", "Split/status mismatch")
            require(type(row.get("target")) is int and row["target"] in (0, 1),
                    f"{cid}: missing/nonbinary target for assigned case")
            require(row.get("target_review_status") and row.get("target_status"), "Missing label provenance")
            family = row.get("case_family_id")
            require(isinstance(family, str) and family, "Missing family ID")
            require(family_partition.get(family, partition) == partition, "Family overlaps partitions")
            family_partition[family] = partition
            require(not row.get("training_only") or partition == "train", "Calibration case outside training")
            for variant in indexed:
                require(indexed[variant][cid]["text"].strip(), f"{cid}: empty {variant} text cannot enter modeling")
    pending = manifest["pending_case_ids"]
    excluded = manifest["excluded_case_ids"]
    require(len(pending) == len(set(pending)) and len(excluded) == len(set(excluded)), "Duplicate unassigned ID")
    require(not (assigned & set(pending) or assigned & set(excluded) or set(pending) & set(excluded)), "Conflicting assignment lists")
    require(assigned | set(pending) | set(excluded) == set(cases), "Incomplete split coverage")
    for cid in pending + excluded:
        require(cases[cid]["split"] is None and cases[cid]["status"] != "assigned", "Unassigned case has a split")
    return indexed, cases


def read_validated(mvp):
    mvp = Path(mvp)
    split_path = mvp / "data/mvp_split_v1/split_manifest.json"
    manifest = json.loads(split_path.read_text())
    exports, input_hashes = {}, {"data/mvp_split_v1/split_manifest.json": sha256(split_path)}
    for variant, relative in VARIANTS.items():
        path = mvp / "data" / relative
        export_manifest_path = path.parent / "manifest.json"
        export_manifest = json.loads(export_manifest_path.read_text())
        require(sha256(path) == export_manifest["outputs"][path.name], f"{variant}: export checksum changed")
        if variant == "MASKED":
            expected_split = export_manifest["input_sha256"]["split"]
            require(export_manifest["input_sha256"]["full"] == input_hashes["data/full_v1/full.jsonl"], "MASKED uses another FULL base")
        else:
            expected_split = next(v for k, v in export_manifest["inputs"].items() if k.endswith("mvp_split_v1/split_manifest.json"))
        require(expected_split == sha256(split_path), f"{variant}: shared split/labels changed; version required")
        exports[variant] = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        input_hashes[str(path.relative_to(mvp))] = sha256(path)
        input_hashes[str(export_manifest_path.relative_to(mvp))] = sha256(export_manifest_path)
    indexed, cases = validate_records(exports, manifest)
    report = {"contract_version": "model_input_contract_v1", "status": "passed",
              "selection_count": len(cases), "partition_counts": {k: len(manifest["split_case_ids"][k]) for k in PARTITIONS},
              "pending_case_ids": manifest["pending_case_ids"], "excluded_case_ids": manifest["excluded_case_ids"],
              "approved_variants": VARIANTS, "allowed_export_fields": ["case_id", "text"],
              "feature_field": "text", "target_source": "mvp_split_v1/split_manifest.json: cases[].target",
              "target_review_status_counts": {s: sum(r["target_review_status"] == s for r in cases.values()) for s in sorted({r["target_review_status"] for r in cases.values()})},
              "near_empty_case_ids_by_variant": {v: [cid for cid, r in rows.items() if len(r["text"].split()) < 50] for v, rows in indexed.items()},
              "input_sha256": input_hashes,
              "limitations": ["Checks do not establish human-reviewed targets or exhaustive removal of outcome cues.",
                              "Legal reasoning and quotations in source opinion text are retained under the preprocessing rules.",
                              "Only the provided loader is guarded; other training code must follow the same contract."]}
    return indexed, cases, manifest, report


@dataclass(frozen=True)
class ModelBatch:
    case_ids: tuple
    texts: tuple
    targets: tuple


def load_model_batch(mvp, variant, partition):
    """Load assigned cases in manifest order. Labels remain separate from texts.

    These targets are currently provisional. Do not describe evaluation using
    them as human-gold evaluation. Pending/excluded cases are never returned.
    """
    require(variant in VARIANTS, "Choose FULL or MASKED (MASKED resolves to v2)")
    require(partition in PARTITIONS, "Choose train, development or test")
    indexed, cases, manifest, _ = read_validated(mvp)
    ids = tuple(manifest["split_case_ids"][partition])
    return ModelBatch(ids, tuple(indexed[variant][cid]["text"] for cid in ids),
                      tuple(cases[cid]["target"] for cid in ids))
