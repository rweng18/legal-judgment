"""Reproducible, label-free family screening of the frozen 506-source corpus."""
from collections import Counter, defaultdict
from datetime import date
from itertools import combinations
from pathlib import Path
import hashlib
import json
import math
import re
import unicodedata

CONFIG = {
    "version": "family_v1",
    "cosine_threshold": 0.70,
    "shingle_size": 5,
    "shingle_jaccard_threshold": 0.30,
    "shingle_containment_threshold": 0.60,
    "minimum_shared_shingles": 50,
    "idf_max_document_fraction": 0.80,
    "scope": "all 506 source opinions; no target labels used for screening",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_rows(path):
    return [json.loads(s) for s in Path(path).read_text(encoding="utf-8").splitlines() if s.strip()]


def canonical(text):
    return re.sub(r"[^a-z0-9]+", " ", unicodedata.normalize("NFKC", text).lower()).strip()


def docket_keys(text):
    # Preserve years and digits. Strip only explicit Index/CA prefixes and display numbers.
    keys = set(re.findall(r"\d{2,7}\s*[/\-]\s*\d{2,6}", text or ""))
    return sorted(re.sub(r"\s+", "", k) for k in keys)


def period(value):
    year = date.fromisoformat(value).year
    if 2010 <= year <= 2020:
        return "train"
    if 2021 <= year <= 2022:
        return "development"
    if 2023 <= year <= 2024:
        return "test"
    return "outside_proposed_periods"


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def jsonl_bytes(rows):
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8")


def immutable_write(path, content):
    path = Path(path)
    require(not path.exists() or path.read_bytes() == content,
            f"Existing version differs: {path}. Choose a new version.")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(content)


def screen(root):
    root = Path(root)
    rows = sorted(read_rows(root / "annotation/source/cases.jsonl"), key=lambda r: r["case_id"])
    require(len(rows) == len({r["case_id"] for r in rows}) == 506, "Expected 506 unique sources")
    selected = set(read_json(root / "annotation/submissions/becca/MVP/data/unanimous_include_v1/case_ids.json"))
    require(len(selected) == 114, "Expected 114 MVP IDs")
    tokens, counts, shingles, norm_hashes = [], [], [], []
    df = Counter()
    for row in rows:
        require(hashlib.sha256(row["text"].encode()).hexdigest() == row["text_sha256"],
                f"Source hash mismatch: {row['case_id']}")
        t = canonical(row["text"]).split()
        tokens.append(t)
        c = Counter(t)
        counts.append(c)
        df.update(c.keys())
        n = CONFIG["shingle_size"]
        shingles.append(set(tuple(t[k:k+n]) for k in range(len(t)-n+1)))
        norm_hashes.append(hashlib.sha256(" ".join(t).encode()).hexdigest())
    vectors = []
    for c in counts:
        vec = {t: (1 + math.log(v)) * (1 + math.log((1 + len(rows)) / (1 + df[t])))
               for t, v in c.items() if len(t) > 2 and df[t] <= len(rows)*CONFIG["idf_max_document_fraction"]}
        norm = math.sqrt(sum(v*v for v in vec.values()))
        vectors.append({t: v/norm for t, v in vec.items()} if norm else {})
    names = [canonical(r["case_name"]) for r in rows]
    plaintiffs = [n.split(" v ")[0] for n in names]
    dockets = [set(docket_keys(r.get("docket_number", ""))) for r in rows]
    candidates = []
    for i, j in combinations(range(len(rows)), 2):
        a, b = rows[i], rows[j]
        reasons = []
        if a["text_sha256"] == b["text_sha256"]:
            reasons.append("exact_text_hash")
        if norm_hashes[i] == norm_hashes[j]:
            reasons.append("normalized_text_hash")
        if names[i] == names[j]:
            reasons.append("same_normalized_case_name")
        if plaintiffs[i] == plaintiffs[j]:
            reasons.append("same_normalized_plaintiff")
        if dockets[i] & dockets[j]:
            reasons.append("shared_docket_identifier")
        if a.get("opinion_id") and a["opinion_id"] == b.get("opinion_id"):
            reasons.append("same_opinion_id")
        v1, v2 = vectors[i], vectors[j]
        if len(v1) > len(v2):
            v1, v2 = v2, v1
        cosine = sum(v*v2.get(k, 0) for k, v in v1.items())
        shared = len(shingles[i] & shingles[j])
        union = len(shingles[i]) + len(shingles[j]) - shared
        jaccard = shared/union if union else 0
        containment = shared/min(len(shingles[i]), len(shingles[j])) if min(len(shingles[i]),len(shingles[j])) else 0
        if cosine >= CONFIG["cosine_threshold"]:
            reasons.append("high_tfidf_cosine")
        if shared >= CONFIG["minimum_shared_shingles"] and jaccard >= CONFIG["shingle_jaccard_threshold"]:
            reasons.append("high_5gram_jaccard")
        if shared >= CONFIG["minimum_shared_shingles"] and containment >= CONFIG["shingle_containment_threshold"]:
            reasons.append("high_5gram_containment")
        if reasons:
            candidates.append({
                "pair_id": a["case_id"] + "__" + b["case_id"],
                "case_ids": [a["case_id"], b["case_id"]],
                "names": [a["case_name"], b["case_name"]],
                "dates": [a["date_filed"], b["date_filed"]],
                "date_gap_days": abs((date.fromisoformat(a["date_filed"]) - date.fromisoformat(b["date_filed"])).days),
                "dockets": [a.get("docket_number"), b.get("docket_number")],
                "reasons": reasons, "shared_docket_keys": sorted(dockets[i] & dockets[j]),
                "tfidf_cosine": round(cosine, 6), "shingle_jaccard": round(jaccard, 6),
                "shingle_containment": round(containment, 6), "shared_shingles": shared,
                "affects_mvp": bool(set((a["case_id"], b["case_id"])) & selected),
            })
    # Current-opinion amendment/replacement signals; ordinary amended pleadings are separate.
    signal_re = re.compile(
        r"(?:amended|corrected|revised|supersed\w*|withdrawn|substituted)\s+(?:memorandum\s+(?:and\s+)?)?(?:opinion|decision)"
        r"|(?:opinion|decision|memorandum)\s+(?:is\s+|was\s+|has\s+been\s+)?(?:amended|corrected|revised|withdrawn|superseded|substituted)"
        r"|(?:upon|on)\s+reargument|(?:prior|previous|companion)\s+appeal|appeal\s+No\.\s*2",
        re.IGNORECASE,
    )
    notices = []
    for r in rows:
        hits = [{"match": m.group(), "start": max(0,m.start()-160), "end": min(len(r["text"]),m.end()+250),
                 "context": r["text"][max(0,m.start()-160):min(len(r["text"]),m.end()+250)]}
                for m in signal_re.finditer(r["text"])]
        if hits:
            notices.append({"case_id": r["case_id"], "case_name": r["case_name"],
                            "affects_mvp": r["case_id"] in selected, "signals": hits})
    return {"config": CONFIG, "pair_count_screened": len(rows)*(len(rows)-1)//2,
            "candidates": candidates, "opinion_notices": notices,
            "exact_duplicate_pairs": sum("exact_text_hash" in p["reasons"] for p in candidates),
            "normalized_duplicate_pairs": sum("normalized_text_hash" in p["reasons"] for p in candidates)}


def attach_families_to_chunks(chunks, case_manifest):
    """Use for future encoder chunks: each chunk must identify exactly one source case."""
    lookup = {r["case_id"]: r["case_family_id"] for r in case_manifest}
    result = []
    for chunk in chunks:
        cid = chunk.get("case_id")
        require(cid in lookup, f"Unknown chunk case ID: {cid}")
        require("case_family_id" not in chunk or chunk["case_family_id"] == lookup[cid],
                f"Conflicting family on chunk for {cid}")
        result.append({**chunk, "case_family_id": lookup[cid]})
    return result


def validate_family_partition(assignments, case_manifest):
    """Validate future case/chunk split assignments; no split is created here."""
    lookup = {r["case_id"]: r for r in case_manifest}
    seen = defaultdict(set)
    for row in assignments:
        cid = row["case_id"]
        require(cid in lookup, f"Unknown split case ID: {cid}")
        split = row["split"]
        require(split in {"train", "development", "test"}, "Unexpected split")
        info = lookup[cid]
        require(not info["cross_period_family"], f"Exclude boundary-spanning family: {cid}")
        require(not info["external_companion_unresolved"], f"Resolve external companion first: {cid}")
        require(not info["family_training_only"] or split == "train", f"Calibration-family leakage: {cid}")
        seen[info["case_family_id"]].add(split)
    require(all(len(splits) == 1 for splits in seen.values()), "Family appears in multiple splits")
    return True


def build_outputs(root, result):
    root = Path(root)
    mvp = root / "annotation/submissions/becca/MVP"
    review_dir = mvp / "family_review"
    decisions = read_json(review_dir / "review_decisions.json")
    rows = {r["case_id"]: r for r in read_rows(root / "annotation/source/cases.jsonl")}
    metadata = read_rows(mvp / "data/metadata_v1/metadata.jsonl")
    selected = set(read_json(mvp / "data/unanimous_include_v1/case_ids.json"))
    require({r["case_id"] for r in metadata} == selected, "MVP metadata/selection mismatch")
    candidate_map = {p["pair_id"]: p for p in result["candidates"]}
    review_map = {p["pair_id"]: p for p in decisions["pair_reviews"]}
    require(len(review_map) == len(decisions["pair_reviews"]), "Duplicate pair decisions")
    require(set(candidate_map) == set(review_map), "Every candidate must have one recorded decision")
    parent = {cid: cid for cid in rows}

    def find(cid):
        while parent[cid] != cid:
            parent[cid] = parent[parent[cid]]
            cid = parent[cid]
        return cid

    pair_log = []
    for pair_id, decision in review_map.items():
        require(decision["case_ids"] == candidate_map[pair_id]["case_ids"], "Pair identity mismatch")
        for e in decision["evidence"]:
            src = rows[e["case_id"]]
            require(src["text"][e["start"]:e["end"]] == e["quote"], "Review quote/offset mismatch")
            require(src["text_sha256"] == e["text_sha256"], "Review evidence hash mismatch")
        a, b = decision["case_ids"]
        if decision["grouping_action"] == "group":
            ra, rb = find(a), find(b)
            parent[max(ra, rb)] = min(ra, rb)
        else:
            require(decision["grouping_action"] == "separate", "Unresolved pair action needs explicit policy")
        pair_log.append({**candidate_map[pair_id], **decision})
    groups = defaultdict(list)
    for cid in sorted(rows):
        groups[find(cid)].append(cid)
    for decision in review_map.values():
        if decision["grouping_action"] == "separate":
            a, b = decision["case_ids"]
            require(find(a) != find(b), "Rejected pair indirectly grouped; resolve contradiction")

    external = {n["case_id"]: n for n in decisions["opinion_notice_reviews"]
                if n["interpretation"] == "external_companion_unresolved"}
    calibration_paths = [root / "annotation/calibration/manifest.json"]
    calibration = set(read_json(calibration_paths[0])["case_ids"])
    for name in ("becca", "hyunsang", "yinkui"):
        path = root / f"annotation/submissions/{name}/independent_calibration_notes.md"
        if path.exists():
            calibration_paths.append(path)
            calibration.update(re.findall(r"NY-\d+", path.read_text(encoding="utf-8")))

    family_rows, case_rows = [], []
    for representative, members in sorted(groups.items()):
        family_id = "FAM-" + representative
        periods = sorted({period(rows[c]["date_filed"]) for c in members})
        cross = len(periods) > 1
        unresolved = sorted(set(members) & set(external))
        origin_calibration = sorted(set(members) & calibration)
        links = [p["pair_id"] for p in pair_log if p["grouping_action"] == "group"
                 and set(p["case_ids"]) <= set(members)]
        status = "assistant_supported_link_pending_human_review" if links else "screened_singleton_not_proof_of_independence"
        if unresolved:
            status = "external_companion_unresolved"
        boundary_status = ("exclude_primary_cross_period" if cross else "hold_pending_external_companion_review"
                           if unresolved else "no_known_boundary_conflict")
        family = {
            "case_family_id": family_id, "case_ids": members,
            "mvp_case_ids": sorted(set(members) & selected), "source_record_count": len(members),
            "review_status": "llm_draft", "human_review_status": "pending", "family_status": status,
            "supporting_pair_ids": links, "observed_periods": periods,
            "cross_period_family": cross, "primary_boundary_policy_status": boundary_status,
            "external_companion_unresolved": bool(unresolved), "unresolved_source_case_ids": unresolved,
            "family_training_only": bool(origin_calibration), "calibration_origin_case_ids": origin_calibration,
        }
        family_rows.append(family)
        for cid in members:
            case_rows.append({
                "case_id": cid, "case_name": rows[cid]["case_name"], "case_family_id": family_id,
                "date_filed": rows[cid]["date_filed"], "date_period": period(rows[cid]["date_filed"]),
                "source_url": rows[cid]["source_url"], "text_sha256": rows[cid]["text_sha256"],
                "selected_for_mvp": cid in selected, "family_status": status,
                "review_status": "llm_draft", "human_review_status": "pending",
                "family_member_case_ids": members, "cross_period_family": cross,
                "primary_boundary_policy_status": boundary_status,
                "external_companion_unresolved": bool(unresolved),
                "family_training_only": bool(origin_calibration),
                "calibration_origin_case_ids": origin_calibration,
                "calibration_inherited_from_related_case": cid not in calibration and bool(origin_calibration),
                "actual_split": None,
            })
    case_rows.sort(key=lambda r: r["case_id"])
    lookup = {r["case_id"]: r for r in case_rows}
    assignments = read_json(root / "annotation/source/assignments.json")["assignments"]
    require(len(assignments) == len(rows) and {r["case_id"] for r in assignments} == set(rows),
            "Original packet assignments must cover each source once")
    packet_rows = [{"case_id": r["case_id"], "batch": r["batch"],
                    "annotation_packet_id": r["chunk_id"], "case_family_id": lookup[r["case_id"]]["case_family_id"],
                    "usage": "case membership only; multi-case annotation packets are not model/split units"}
                   for r in assignments]
    passage_rows = []
    for cid, src in sorted(rows.items()):
        previous_end = 0
        for p in src["passages"]:
            require(p["start"] == previous_end and src["text"][p["start"]:p["end"]] == p["text"],
                    f"Passage coverage mismatch: {cid}")
            previous_end = p["end"]
            passage_rows.append({"case_id": cid, "chunk_id": cid + ":" + p["passage_id"],
                                 "source_passage_id": p["passage_id"], "chunk_type": "existing_source_passage",
                                 "start": p["start"], "end": p["end"], "text_sha256": src["text_sha256"],
                                 "chunk_text_sha256": hashlib.sha256(p["text"].encode()).hexdigest()})
        require(previous_end == len(src["text"]), f"Incomplete source passage coverage: {cid}")
    passage_rows = attach_families_to_chunks(passage_rows, case_rows)
    require(len(passage_rows) == len({r["chunk_id"] for r in passage_rows}), "Duplicate passage IDs")
    require({r["case_id"] for r in passage_rows} == set(rows), "Missing source passages")
    require(all(p["case_family_id"] == lookup[p["case_id"]]["case_family_id"] for p in passage_rows),
            "Passage split from its case family")

    updated_metadata = []
    for original in metadata:
        info = lookup[original["case_id"]]
        updated_metadata.append({**original,
            "case_family_id": info["case_family_id"], "family_review_status": info["family_status"],
            "family_human_review_status": "pending", "family_manifest_version": CONFIG["version"],
            "family_member_case_ids": info["family_member_case_ids"],
            "family_training_only": info["family_training_only"],
            "calibration_training_only_before_family_review": original["calibration_training_only"],
            "calibration_training_only": info["family_training_only"],
            "calibration_inherited_from_related_case": info["calibration_inherited_from_related_case"],
            "calibration_origin_case_ids": info["calibration_origin_case_ids"],
            "calibration_review_status": "family_inherited_recorded_exposure" if info["calibration_inherited_from_related_case"] else original["calibration_review_status"],
            "family_calibration_evidence_manifest": "annotation/submissions/becca/MVP/data/family_v1/family_manifest.json",
            "cross_period_family": info["cross_period_family"],
            "primary_boundary_policy_status": info["primary_boundary_policy_status"],
            "external_companion_unresolved": info["external_companion_unresolved"],
            "metadata_version": "metadata_v2_family_review", "supersedes": "metadata_v1",
        })
    require([r["case_id"] for r in updated_metadata] == [r["case_id"] for r in metadata], "MVP IDs changed")
    for old, new in zip(metadata, updated_metadata):
        for field in ("target", "provisional_target", "target_review_status", "text_sha256"):
            require(old[field] == new[field], f"Forbidden metadata change: {field}")

    uncertain = []
    for p in pair_log:
        if p["relationship"] == "same_opinion_publication_variant":
            uncertain.append({"issue_id": "canonical_source:" + p["pair_id"], "case_ids": p["case_ids"],
                              "issue": "publication_precedence_and_canonical_text_pending",
                              "family_action": "keep together; retain both records; do not count as independent observations",
                              "details": p["uncertainty"], "affects_mvp": p["affects_mvp"]})
    for cid, notice in external.items():
        uncertain.append({"issue_id": "external_companion:" + cid, "case_ids": [cid],
                          "issue": "missing_companion_identity_and_date",
                          "family_action": "retain source; hold final family/split decision pending review",
                          "details": notice["rationale"], "affects_mvp": cid in selected})
    summary = {
        "source_records": len(rows), "pairs_screened": result["pair_count_screened"],
        "candidate_pairs_reviewed": len(pair_log),
        "pair_relationship_counts": dict(Counter(p["relationship"] for p in pair_log)),
        "exact_text_duplicate_pairs": result["exact_duplicate_pairs"],
        "normalized_text_duplicate_pairs": result["normalized_duplicate_pairs"],
        "confirmed_appellate_amendment_pairs": 0,
        "all_source_families": len(family_rows), "mvp_cases": len(selected),
        "mvp_families": len({lookup[c]["case_family_id"] for c in selected}),
        "linked_families_touching_mvp": sum(bool(f["supporting_pair_ids"]) and bool(f["mvp_case_ids"]) for f in family_rows),
        "known_cross_period_families": sum(f["cross_period_family"] for f in family_rows),
        "unresolved_external_companions": len(external),
        "mvp_unresolved_external_companions": sorted(set(external) & selected),
        "mvp_training_only_cases": sorted(c for c in selected if lookup[c]["family_training_only"]),
        "mvp_newly_inherited_training_only": sorted(c for c in selected if lookup[c]["calibration_inherited_from_related_case"]),
        "source_passages_mapped": len(passage_rows), "annotation_case_memberships_mapped": len(packet_rows),
        "actual_splits_assigned": 0, "human_adjudication": "pending",
    }
    inputs = [root / "annotation/source/cases.jsonl", root / "annotation/source/assignments.json",
              root / "annotation/source/family_hints.json", mvp / "data/metadata_v1/metadata.jsonl",
              mvp / "data/unanimous_include_v1/case_ids.json", review_dir / "review_decisions.json",
              review_dir / "family_audit.py", review_dir / "variant_differences.json", *calibration_paths]
    payloads = {
        "family_manifest.json": json_bytes({"version": CONFIG["version"], "config": CONFIG,
                                             "summary": summary, "families": family_rows}),
        "case_family_manifest.jsonl": jsonl_bytes(case_rows),
        "chunk_family_manifest.jsonl": jsonl_bytes(passage_rows),
        "annotation_packet_membership.jsonl": jsonl_bytes(packet_rows),
        "pair_review_log.jsonl": jsonl_bytes(pair_log),
        "opinion_notice_review.jsonl": jsonl_bytes(decisions["opinion_notice_reviews"]),
        "uncertain_matches.jsonl": jsonl_bytes(uncertain),
        "screening_results.json": json_bytes(result),
        "summary.json": json_bytes(summary),
    }
    meta_bytes = jsonl_bytes(updated_metadata)
    provenance = {
        "version": CONFIG["version"], "review_status": "llm_draft; human review pending",
        "inputs": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        "outputs": {name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()},
        "metadata_v2_family_review/metadata.jsonl": hashlib.sha256(meta_bytes).hexdigest(),
        "no_external_lookup": True,
        "limitations": ["No external companion records fetched; identities/dates remain pending.",
                        "No detected link is not proof of independence; metadata may be missing and thresholds have finite recall.",
                        "Annotation packets contain multiple cases and must not be used as model splitting units.",
                        "Encoder chunks do not yet exist; attach_families_to_chunks enforces their future family inheritance.",
                        "All family decisions are assistant drafts; no human review claimed."]}
    payloads["provenance.json"] = json_bytes(provenance)
    destination = mvp / "data" / CONFIG["version"]
    # Validate every destination before writing any versioned output.
    targets = {destination / k: v for k, v in payloads.items()}
    targets[mvp / "data/metadata_v2_family_review/metadata.jsonl"] = meta_bytes
    for path, content in targets.items():
        require(not path.exists() or path.read_bytes() == content, f"Versioned output changed: {path}")
    for path, content in targets.items():
        immutable_write(path, content)
    return {"summary": summary, "case_manifest": case_rows, "families": family_rows,
            "metadata": updated_metadata, "uncertain": uncertain, "pair_log": pair_log}


if __name__ == "__main__":
    root = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "annotation/source/cases.jsonl").exists())
    result = screen(root)
    output = root / "annotation/submissions/becca/MVP/family_review/candidate_screen.json"
    immutable_write(output, json_bytes(result))
    print(f"Screened {result['pair_count_screened']} pairs; {len(result['candidates'])} candidates; "
          f"{len(result['opinion_notices'])} opinions with amendment/related-appeal signals.")
    for p in result["candidates"]:
        print(p["pair_id"], p["names"], p["reasons"], "cosine",p["tfidf_cosine"], "MVP",p["affects_mvp"])
