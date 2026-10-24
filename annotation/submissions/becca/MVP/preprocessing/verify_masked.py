"""Boundary/leakage regressions and independent export-integrity checks."""
import json
from pathlib import Path
import masked_text as m


def check_rules():
    # Both directions are exercised without passing any class labels to the masker.
    positive = [
        "Ordered that the order is affirmed, with costs.",
        "It is hereby ORDERED that the order is reversed without costs.",
        "Order, Supreme Court (Smith, J.), entered May 1, 2014, affirmed.",
        "We affirm.", "Because the motion fails, we reverse.",
        "The Supreme Court properly granted the motion for summary judgment.",
        "The Supreme Court should have denied the motion for summary judgment.",
        "The motion was properly denied.",
        "The motion should not have been granted.",
    ]
    negative = [
        "Supreme Court granted the motion. Plaintiff appeals.",
        "Defendants contend that Supreme Court erred in denying their motion.",
        "In Smith v Jones, the court properly granted the motion.",
        "On the prior appeal, we reversed the order.",
        "We previously affirmed the order.",
        "If the evidence were different, we would reverse.",
        "A defendant must establish lack of notice (Smith v Jones, 10 NY3d 1, affd 11 NY3d 2).",
        "The court correctly found a triable issue of fact.",
    ]
    for text in positive:
        m.require(m.mask_text(text)[0] == "", f"Failed outcome removal: {text}")
    for text in negative:
        m.require(m.mask_text(text)[0] == text, f"False removal: {text}")
    text = "Plaintiff fell at Example, Inc. Defendants contend that Supreme Court erred in denying their motion. We agree."
    result, audit = m.mask_text(text)
    m.require(result == text.removesuffix(" We agree."), "Party argument or facts removed")
    text = "The motion concerned Example Corp. Ordered that the order is reversed. Plaintiff fell on stairs. We reverse."
    m.require(m.mask_text(text)[0] == "The motion concerned Example Corp. Plaintiff fell on stairs.", "Abbreviation boundary/repetition failure")
    text = "Facts remain (see Smith v Jones, Inc., 10 AD3d 1 [2010]). We affirm."
    m.require(m.mask_text(text)[0] == text.removesuffix(" We affirm."), "Citation was damaged")
    return len(positive) + len(negative) + 3


def check_exports(root):
    p = Path(root) / "annotation/submissions/becca/MVP"
    full = {r["case_id"]: r["text"] for r in m.rows(p / "data/full_v1/full.jsonl")}
    masked_rows = m.rows(p / "data/masked_v1/masked.jsonl")
    masked = {r["case_id"]: r["text"] for r in masked_rows}
    audit_rows = m.rows(p / "data/masked_v1/removal_audit.jsonl")
    m.require(len(masked_rows) == len(masked) == len(audit_rows) == 114 and set(masked) == set(full), "ID coverage failure")
    m.require({a["case_id"] for a in audit_rows} == set(full), "Audit coverage failure")
    for row in masked_rows:
        m.require(set(row) == {"case_id", "text"}, "Nontext annotation fields in model input")
    for a in audit_rows:
        cid = a["case_id"]
        m.require(m.apply_edits(full[cid], a["edits"]) == masked[cid], "Reconstruction failed")
        m.require(a["full_sha256"] == m.digest(full[cid].encode()), "FULL hash failed")
        m.require(a["masked_sha256"] == m.digest(masked[cid].encode()), "MASKED hash failed")
        m.require(sum(e["removed_words"] for e in a["edits"]) == len(full[cid].split()) - len(masked[cid].split()) == a["removed_words"], "Word accounting failed")
        m.require((p/f"data/masked_v1/texts/{cid}.txt").read_text() == masked[cid]+"\n", "Text export differs")
        if not masked[cid]:
            m.require("empty_output_exclude_from_modeling" in a["flags"], "Empty output not handled")
    manifest = json.loads((p/"data/masked_v1/manifest.json").read_text())
    for name, checksum in manifest["outputs"].items():
        m.require(m.digest((p/"data/masked_v1"/name).read_bytes()) == checksum, f"Checksum failed: {name}")
    return {"verified_cases": len(full), "verified_output_files": len(manifest["outputs"])}
