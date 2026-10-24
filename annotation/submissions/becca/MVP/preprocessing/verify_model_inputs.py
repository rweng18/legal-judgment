"""Exercise rejection of annotation leakage and incorrect target joins."""
from copy import deepcopy
import json
from pathlib import Path
import model_inputs as m


def check(mvp):
    mvp = Path(mvp)
    exports = {v: [json.loads(line) for line in (mvp / "data" / path).read_text().splitlines()]
               for v, path in m.VARIANTS.items()}
    manifest = json.loads((mvp / "data/mvp_split_v1/split_manifest.json").read_text())
    passed = []

    def rejects(name, change, expected):
        e, s = deepcopy(exports), deepcopy(manifest)
        change(e, s)
        try:
            m.validate_records(e, s)
        except ValueError as error:
            m.require(expected in str(error), f"{name}: unexpected failure {error}")
            passed.append(name)
        else:
            raise AssertionError(f"{name}: invalid input accepted")

    for field in ("label", "target", "favors", "legal_findings", "factual_summary", "supporting_quotations", "metadata"):
        rejects(f"reject_{field}", lambda e, s, f=field: e["FULL"][0].update({f: "annotation"}), "allowed fields")
    rejects("duplicate_id", lambda e, s: e["MASKED"].append(e["MASKED"][0]), "duplicate case ID")
    rejects("missing_variant_case", lambda e, s: e["MASKED"].pop(), "IDs differ")
    assigned_index = next(i for i, r in enumerate(manifest["cases"]) if r["status"] == "assigned")
    assigned_id = manifest["cases"][assigned_index]["case_id"]
    rejects("missing_target", lambda e, s: s["cases"][assigned_index].pop("target"), "missing/nonbinary target")
    rejects("boolean_target", lambda e, s: s["cases"][assigned_index].update(target=True), "missing/nonbinary target")
    rejects("empty_text", lambda e, s: next(r for r in e["FULL"] if r["case_id"] == assigned_id).update(text=" "), "empty FULL text")
    rejects("nested_annotation_in_text", lambda e, s: e["FULL"][0].update(text={"summary": "annotation"}), "text must be a string")
    train_id = manifest["split_case_ids"]["train"][0]
    dev_id = manifest["split_case_ids"]["development"][0]
    def overlap_family(e, s):
        by_id = {r["case_id"]: r for r in s["cases"]}
        by_id[dev_id]["case_family_id"] = by_id[train_id]["case_family_id"]
    rejects("family_overlap", overlap_family, "Family overlaps")
    # File order must not determine which target attaches to a text.
    shuffled = {v: list(reversed(rows)) for v, rows in exports.items()}
    indexed, cases = m.validate_records(shuffled, manifest)
    for partition in m.PARTITIONS:
        full = m.load_model_batch(mvp, "FULL", partition)
        masked = m.load_model_batch(mvp, "MASKED", partition)
        m.require(full.case_ids == masked.case_ids and full.targets == masked.targets, "Variant target mismatch")
        m.require(full.targets == tuple(cases[cid]["target"] for cid in full.case_ids), "ID join failure")
        m.require(full.texts == tuple(indexed["FULL"][cid]["text"] for cid in full.case_ids), "File-order-dependent join")
        m.require(not (set(full.case_ids) & set(manifest["pending_case_ids"])), "Pending case included")
    passed += ["join_by_id_not_file_order", "identical_targets_across_variants", "pending_cases_excluded"]
    return {"checks_passed": len(passed), "checks": passed}
