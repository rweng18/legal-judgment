"""Shared FULL cleaner for the frozen source-text snapshot. No labels are inputs."""
from collections import Counter
from pathlib import Path
import hashlib
import html
import json
import re

VERSION = "full_v1"
RULE_VERSION = "full_cleaner_v1"
BODY = re.compile(r"\b(?:In an action\b|Appeals? from\b|Orders?, Supreme Court\b|Judgments?, Supreme Court\b)")
AUTHOR = re.compile(r"(?:[A-Z][A-Za-z'’-]+(?:,? Jr\.)?), J\.(?:P\.)?\s*$")
TAG = re.compile(r"<!--.*?-->|</?(?:html|head|body|title|meta|link|div|span|p|br|hr|a|b|i|em|strong|small|sup|sub|font|center|table|thead|tbody|tr|td|th|ul|ol|li|h[1-6])\b[^>]*>", re.I | re.S)
CONTAINER = re.compile(r"<(script|style|nav|head)\b[^>]*>.*?</\1\s*>", re.I | re.S)
PAGE = re.compile(r"\[\*\d+\]|(?<!\w)\*\d{1,4}\b")
PDF_PAGE = re.compile(r"-\s*\d+\s*-\s*\d+\s+(?:CA|CV)\s+\d{2}-\d{3,6}\b")
PRIOR_HISTORY = re.compile(r"\[Prior Case History:\s*[^\]]*\]", re.I)
CLERK = re.compile(r"\bEntered:\s*[A-Za-z]+\s+\d{1,2},\s*\d{4}\s+[A-Za-z .’'\-]{1,100}?Clerk of the Court\b", re.I)
PANEL = re.compile(r"\b(?:Concur|Present)\s*[—–-]\s*.{0,280}?\bJJ\.", re.S)
JUDGE = r"[A-Z][A-Za-zÀ-ÿ'’\-]*(?:\s+[A-Z][A-Za-zÀ-ÿ'’\-]*)?(?:,?\s+Jr\.)?"
NAMES = rf"{JUDGE}(?:,\s*(?:J\.P\.?|P\.J\.?))?(?:,\s*{JUDGE})*(?:,?\s+and\s+{JUDGE})?"
CONCUR = re.compile(rf"(?<!\w){NAMES},\s*JJ?\.?,?\s+concur\.")
DISSENT_HEADING = re.compile(rf"\b{JUDGE},\s*J(?:J)?\.(?:P\.)?\s*[, ]*\((?:dissenting|concurring in part and dissenting in part)[^)]*\)\s*[.:]?", re.I)
DISSENT_INTRO = re.compile(r"\bAll concur except\s+.{1,180}?\b(?:dissents|dissent)\s+and\s+votes?\s+.{1,160}?\bin the following memorandum\s*:", re.I)
ENTITY = re.compile(r"&(?:#[0-9]+|#x[0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]+);")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def normalize_space(text):
    return " ".join(text.split())


def apply_edits(source, edits):
    parts, cursor = [], 0
    for e in sorted(edits, key=lambda x: x["start"]):
        require(cursor <= e["start"] < e["end"] <= len(source), "Overlapping/invalid edits")
        require(source[e["start"]:e["end"]] == e["source_text"], "Edit/source mismatch")
        parts.extend((source[cursor:e["start"]], e["replacement"]))
        cursor = e["end"]
    parts.append(source[cursor:])
    return normalize_space("".join(parts))


def clean_full(source):
    """Offsets are in the ORIGINAL text. Whitespace is normalized after recorded edits."""
    edits, flags = [], []

    def add(start, end, reason, replacement=" "):
        if end <= start:
            return
        for e in edits:
            if start < e["end"] and end > e["start"]:
                if e["start"] <= start and end <= e["end"]:
                    return  # Already removed by a containing structural span.
                raise ValueError("Conflicting cleaning spans; manual review needed")
        edits.append({"start": start, "end": end, "reason": reason,
                      "source_text": source[start:end], "replacement": replacement})

    # Equal-length view permits structure detection without changing source offsets.
    view = list(source)
    for pattern in (CONTAINER, TAG):
        for m in pattern.finditer(source):
            view[m.start():m.end()] = " " * (m.end()-m.start())
    view = "".join(view)
    body = BODY.search(view)
    body_start = 0
    if body:
        prefix = view[:body.start()]
        author = AUTHOR.search(prefix)
        candidate_start = author.start() if author else body.start()
        publication_prefix = view[:candidate_start]
        if not publication_prefix.strip():
            body_start = candidate_start
        elif re.search(r"NY Slip Op|Published by New York State|SUPREME COURT OF THE STATE", publication_prefix, re.I) and re.search(r"\bfor (?:the )?(?:plaintiff|defendant|appellant|respondent)|of counsel", publication_prefix, re.I):
            body_start = candidate_start
            add(0, body_start, "publication_caption_counsel_header")
        elif PAGE.sub("", publication_prefix).strip() == "":
            body_start = candidate_start
        else:
            flags.append("unrecognized_prefix_preserved")
    elif re.match(r"\s*[A-Z][A-Za-z'’-]+, J\.(?:P\.)?\s+", view):
        pass  # A signed opinion can begin directly with facts, without an appeal synopsis.
    else:
        flags.append("body_start_not_recognized")

    # Only explicit separate-opinion headings delimit a dissent. Majority references
    # to a dissent are never a removal rule. Do not truncate if an order may follow.
    headings = sorted([m for p in (DISSENT_HEADING, DISSENT_INTRO) for m in p.finditer(view)
                       if m.start() > body_start + 100], key=lambda m: m.start())
    dissent_start = None
    if headings:
        h = headings[0]
        if re.search(r"\bOrdered that\b|\bIt is hereby ordered\b|\bMajority opinion\b", view[h.end():], re.I):
            flags.append("ambiguous_dissent_boundary_preserved")
        else:
            dissent_start = h.start()
            add(h.start(), len(source), "separate_dissent")
    if re.search(r"\bdissent\w*\b", view[body_start:dissent_start], re.I):
        flags.append("dissent_reference_in_retained_text_check_context")

    for pattern, reason in ((CONTAINER, "web_noncontent_container"), (TAG, "web_markup"),
                            (PRIOR_HISTORY, "publisher_prior_case_history"),
                            (CLERK, "clerk_certification"), (PANEL, "judicial_panel_roster"),
                            (CONCUR, "judicial_concurrence_roster"),
                            (PDF_PAGE, "pdf_running_page_docket"), (PAGE, "publication_page_marker")):
        for m in pattern.finditer(source):
            add(m.start(), m.end(), reason)
    for m in ENTITY.finditer(source):
        decoded = html.unescape(m.group())
        if decoded != m.group():
            add(m.start(), m.end(), "html_entity_decode", decoded)
    edits.sort(key=lambda e: e["start"])
    full = apply_edits(source, edits)
    require(full == apply_edits(source, edits), "Audit reconstruction mismatch")
    if re.search(r"<\/?[A-Za-z][^>]*>|Published by New York State|of counsel|Clerk of the Court|\[Prior Case History:", full, re.I):
        flags.append("residual_metadata_or_markup_review")
    if re.search(r"\b(?:JJ\.?,?\s+concur|Concur\s*[—-]|Present\s*[—-])", full):
        flags.append("residual_judicial_roster_review")
    before, after = len(source.split()), len(full.split())
    if not full:
        flags.append("empty_output")
    elif after < 50:
        flags.append("near_empty_under_50_words")
    if before and (before-after)/before > 0.50:
        flags.append("more_than_half_words_removed_review")
    return full, {"edits": edits, "flags": sorted(set(flags)),
                  "source_words": before, "full_words": after,
                  "word_count_reduction": before-after,
                  "word_count_reduction_fraction": (before-after)/before if before else None,
                  "removed_span_words": sum(len(e["source_text"].split()) for e in edits if e["reason"] != "html_entity_decode"),
                  "whitespace_policy": "collapse whitespace after applying source-offset edits"}


def write_immutable(path, data):
    path = Path(path)
    require(not path.exists() or path.read_bytes() == data, f"Existing version differs: {path}; use a new version")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(data)


def build(root):
    root = Path(root)
    mvp = root / "annotation/submissions/becca/MVP"
    sources_path = mvp / "data/unanimous_include_v1/cases.jsonl"
    split_path = mvp / "data/mvp_split_v1/split_manifest.json"
    policy_path = mvp / "preprocessing/full_rules_v1.json"
    split = json.loads(split_path.read_text())
    policy = json.loads(policy_path.read_text())
    require(digest(Path(__file__).read_bytes()) == policy["cleaner_sha256"], "Cleaner differs from frozen rules")
    require(digest(sources_path.read_bytes()) == policy["source_subset_sha256"], "Sources changed")
    require(digest(split_path.read_bytes()) == policy["split_manifest_sha256"], "Frozen split changed")
    source_rows = read_rows(sources_path)
    require(len(source_rows) == len({r["case_id"] for r in source_rows}) == 114, "Source coverage mismatch")
    require({r["case_id"] for r in source_rows} == {r["case_id"] for r in split["cases"]}, "Split/ID mismatch")
    full_rows, audit_rows, outputs = [], [], {}
    for r in source_rows:
        cid, source = r["case_id"], r["text"]
        require(digest(source.encode()) == r["text_sha256"], f"Source hash mismatch: {cid}")
        full, audit = clean_full(source)
        full_rows.append({"case_id": cid, "text": full})
        audit_rows.append({"case_id": cid, "source_sha256": r["text_sha256"],
                           "full_sha256": digest(full.encode()), "rule_version": RULE_VERSION, **audit})
        outputs[f"texts/{cid}.txt"] = (full + "\n").encode()
    require(not any("empty_output" in a["flags"] for a in audit_rows), "Empty FULL output; resolve before release")
    summary = {"case_count": len(full_rows),
               "rule_version": RULE_VERSION,
               "removal_reasons": dict(Counter(e["reason"] for a in audit_rows for e in a["edits"])),
               "flag_counts": dict(Counter(f for a in audit_rows for f in a["flags"])),
               "source_words": sum(a["source_words"] for a in audit_rows),
               "full_words": sum(a["full_words"] for a in audit_rows),
               "separate_dissent_cases": [a["case_id"] for a in audit_rows if any(e["reason"] == "separate_dissent" for e in a["edits"])],
               "label_fields_in_model_text_export": False,
               "frozen_ids_and_splits_changed": False,
               "masked_generated": False}
    def jb(obj): return (json.dumps(obj, ensure_ascii=False, indent=2)+"\n").encode()
    def jl(rows): return "".join(json.dumps(r, ensure_ascii=False)+"\n" for r in rows).encode()
    outputs["full.jsonl"] = jl(full_rows)
    outputs["removal_audit.jsonl"] = jl(audit_rows)
    outputs["summary.json"] = jb(summary)
    outputs["manifest.json"] = jb({"version": VERSION, "rule_version": RULE_VERSION,
        "shared_base_policy": "Every later condition must derive from these exact FULL texts; MASKED applies only additional removal",
        "review_status": "assistant structural audit; not human-adjudicated text",
        "inputs": {str(p.relative_to(root)): digest(p.read_bytes()) for p in (sources_path, split_path, policy_path, Path(__file__))},
        "outputs": {k: digest(v) for k,v in outputs.items()},
        "case_ids": [r["case_id"] for r in full_rows],
        "text_sha256_note": "Per-case full_sha256 excludes file-ending newline; output file checksums include it",
        "source_offset_unit": "Python Unicode code points in original source text",
        "word_count_note": "Whitespace-separated words; reduction includes metadata/page-marker and whitespace effects, not tokenizer counts"})
    out = mvp / "data" / VERSION
    for name,data in outputs.items():
        require(not (out/name).exists() or (out/name).read_bytes() == data, "Frozen output differs; use a new version")
    for name,data in outputs.items():
        write_immutable(out/name, data)
    return summary, audit_rows
