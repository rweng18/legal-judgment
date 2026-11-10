"""Run the supplied Batch B majority baseline under an explicit review assumption."""
import argparse
import csv
import json
from pathlib import Path

from data import development_texts, sha_file
from experiment import save_run
from modeling import evaluate


def csv_by_id(path):
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    mapped = {row["case_id"]: row for row in rows}
    if len(mapped) != len(rows):
        raise ValueError(f"Duplicate case IDs in {path}")
    return mapped


def load_assumed_batch_b(package, assume_labels_reviewed=False):
    if not assume_labels_reviewed:
        raise ValueError("This package requires an explicit assumption that labels have been reviewed.")
    paths = {
        "development": package / "B_development_v2_PROVISIONAL.jsonl",
        "labels": package / "inputs/B_three_reviewer_audit_169.csv",
        "families": package / "case_family_manifest_B_169_PROVISIONAL.csv",
    }
    hashes = {key: sha_file(path) for key, path in paths.items()}
    texts = development_texts(paths["development"], hashes["development"])
    labels = csv_by_id(paths["labels"])
    families = csv_by_id(paths["families"])
    rows = []
    family_period = {}
    for case_id, text in sorted(texts.items()):
        label = labels[case_id]
        family = families[case_id]
        if text["batch"] != "B" or label["unanimous_eligibility"] != "include":
            raise ValueError(f"Unexpected batch or eligibility for {case_id}")
        if label["draft_label_if_unanimous_include"] not in {"0", "1"}:
            raise ValueError(f"Missing binary outcome for {case_id}")
        if (label["date_filed"] != text["date_filed"]
                or label["period"] != text["period"] or family["period"] != text["period"]):
            raise ValueError(f"Inconsistent split metadata for {case_id}")
        group = family["family_id_PROVISIONAL"]
        if (not group or family["family_cross_period_PROVISIONAL"] != "False"
                or family_period.setdefault(group, text["period"]) != text["period"]):
            raise ValueError(f"Resolve the cross-period family for {case_id}")
        rows.append({**text, "family_id": group, "label": int(label["draft_label_if_unanimous_include"])})
    for period in ("train", "validation"):
        if {row["label"] for row in rows if row["period"] == period} != {0, 1}:
            raise ValueError(f"Expected both labels in {period}")
    if any(sha_file(path) != hashes[key] for key, path in paths.items()):
        raise ValueError("Input files changed while loading.")
    release = {
        "status": "user_assumed_labels_reviewed",
        "dataset_version": "batch_b/provisional_v1/B_development_v2_PROVISIONAL",
        "split_version": "supplied 2010–2020 training / 2021–2022 validation",
        "label_field": "draft_label_if_unanimous_include",
        "label_review_assumption": "User instructed: Proceed, assuming the labels have been reviewed",
        "source_adjudication_statuses": sorted({labels[r["case_id"]]["adjudication_status"] for r in rows}),
        "family_review_statuses": sorted({families[r["case_id"]]["family_review_status"] for r in rows}),
        "scope": "Batch B only; same supplied development IDs for FULL and MASKED",
        "inputs": {key: {"repository_path": str(path.resolve().relative_to(Path(__file__).resolve().parents[2])),
                        "sha256": hashes[key]} for key, path in paths.items()},
    }
    return release, rows


def run(package, destination, assume_labels_reviewed=False):
    release, rows = load_assumed_batch_b(package, assume_labels_reviewed)
    result = evaluate("Majority", rows, [])
    output = save_run(destination, release, rows, [], [result])
    print(json.dumps({"output": str(output), "metrics": result["metrics"]}, indent=2))
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--assume-labels-reviewed", action="store_true", required=True)
    args = parser.parse_args()
    run(args.package, args.out, args.assume_labels_reviewed)
