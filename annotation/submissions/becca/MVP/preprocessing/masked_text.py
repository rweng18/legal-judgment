"""Label-blind, deterministic sentence masking of frozen FULL text. Standard library only."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

VERSION = "masked_v1"
RULE_VERSION = "masker_v1"
ABBREVIATIONS = {"v", "vs", "inc", "corp", "co", "ltd", "llc", "dept", "st",
                 "mt", "dr", "mr", "mrs", "ms", "jr", "sr", "no", "nos", "etc",
                 "cf", "assn", "auth", "hous", "ins", "elec", "bros", "contrs"}
OUTCOME = r"(?:affirm(?:ed)?|revers(?:e|ed)|vacat(?:e|ed)|modif(?:y|ied)|dismiss(?:ed)?|remand(?:ed)?)"
ACTION = r"(?:grant(?:ed|ing)?|den(?:y|ied|ying)|dismiss(?:ed|ing)?|reinstat(?:e|ed|ing)|strik(?:e|ing)|struck|preclud(?:e|ed|ing))"
OBJECT = r"(?:motion|cross[- ]motion|summary judgment|complaint|petition|answer|order|judgment|sanctions|appeal)"
CUE = re.compile(r"\b(?:affirm\w*|revers\w*|vacat\w*|modif\w*|remand\w*|ordered|properly|correctly|improperly|incorrectly|erred|should have|should not have|must be|should be|we (?:agree|disagree|reject))\b", re.I)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(obj):
    return (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode()


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_immutable(path, data):
    require(not path.exists() or path.read_bytes() == data, f"Frozen file differs: {path}; use a new version")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(data)


def sentence_spans(text):
    """Offsets retain citations, brackets, initials and common legal abbreviations.

    Not a universal legal parser: unmatched brackets and retained cues are audited.
    Quote-closing punctuation belongs to the sentence ending before the whitespace.
    """
    start = 0
    depth = 0
    for i, char in enumerate(text):
        if char in "([":
            depth += 1
        elif char in ")]":
            depth = max(0, depth - 1)
        if char not in ".!?" or depth:
            continue
        end = i + 1
        while end < len(text) and text[end] in '\"”’':
            end += 1
        if end < len(text) and not text[end].isspace():
            continue
        token = re.search(r"([A-Za-z.]+)\s*$", text[start:i])
        word = token.group(1).lower() if token else ""
        next_sentence = re.match(r"\s+(?:The|A|An|In|On|After|Before|Following|Ordered|It|We|Plaintiffs?|Defendants?|Supreme|Accordingly|However|Here|This|That|To|Although|Because|Moreover|Appeal)\b", text[end:])
        if char == "." and not next_sentence and (word in ABBREVIATIONS or len(word) == 1 or re.fullmatch(r"(?:[a-z]\.)+[a-z]", word)):
            continue
        left = start
        while left < end and text[left].isspace():
            left += 1
        if left < end:
            yield left, end
        start = end
    while start < len(text) and text[start].isspace():
        start += 1
    if start < len(text):
        yield start, len(text)


def outside_citations(sentence):
    # Hide parenthetical/citation content for decisions only; preserve original spans.
    depth = 0
    out = []
    for char in sentence:
        if char in "([":
            depth += 1
        if not depth:
            out.append(char)
        if char in ")]":
            depth = max(0, depth - 1)
            out.append(" ")
    return re.sub(r"\s+", " ", "".join(out)).strip()


def removal_reason(sentence):
    s = outside_citations(sentence)
    if re.match(r"(?:It is hereby\s+)?Ordered\s+that\b", s, re.I):
        return "disposition_block"
    if re.match(r"(?:Order(?:s)?|Judgment(?:s)?)(?:\s+and\s+(?:order|judgment)s?)?\s*,", s, re.I) and re.search(r"\b" + OUTCOME + r"\b", s, re.I):
        return "disposition_synopsis"
    # Quoted decisions, requests, counterfactuals and historical appellate decisions
    # are retained for review instead of treating every outcome verb as current.
    if re.match(r'["“]', s) or re.match(r"In\s+.{0,100}\s+v\.?\s", s) or re.search(r"\b(?:we previously|we had|prior appeal|earlier appeal|would (?:affirm|reverse)|had (?:affirmed|reversed))\b", s, re.I):
        return None
    if re.search(r"\bwe\s+(?:(?:therefore|thus|accordingly|unanimously|now|must)\s+)*" + OUTCOME + r"\b", s, re.I):
        return "current_appellate_result"
    # A party's request or contention is not the court's current ruling.
    if re.match(r"(?:(?:The\s+)?(?:plaintiffs?|defendants?|appellants?|respondents?)\b.{0,100}\b(?:argues?|contends?|asserts?|requests?|seeks?)|(?:If|Assuming)\b)", s, re.I):
        return None
    if re.search(r"\b(?:court|court's|court’s)\b.{0,150}?\b(?:properly|correctly|improperly|incorrectly|erred|error|should (?:not )?have)\b.{0,100}?\b" + ACTION + r"\b.{0,160}?\b" + OBJECT + r"\b", s, re.I):
        return "reviewed_ruling_result"
    if re.search(r"\b" + OBJECT + r"\b.{0,120}?\b(?:was|were|is|are|must be|should be|should (?:not )?have been)\s+(?:(?:not|properly|correctly|improperly|incorrectly)\s+)*" + ACTION + r"\b", s, re.I):
        # Bare 'was granted' is procedural history, not an appellate endorsement.
        if re.search(r"\b(?:properly|correctly|improperly|incorrectly|must be|should (?:not )?(?:be|have been))\b", s, re.I):
            return "operative_relief_result"
    if re.search(r"\b(?:order|judgment|appeal)\b.{0,80}?\b(?:must|should|is|are)\s+(?:be\s+)?" + OUTCOME + r"\b", s, re.I):
        return "current_appellate_result"
    if re.match(r"(?:Accordingly|Therefore|Thus|Consequently|Hence)\b", s, re.I) and re.search(r"\b(?:entitled to summary judgment|motion.{0,80}(?:granted|denied)|complaint.{0,40}dismissed)\b", s, re.I):
        return "concluding_relief_result"
    if re.search(r"\bwe\s+(?:(?:also|therefore|thus|accordingly)\s+)?(?:conclude|agree|reject)\b.{0,180}?\b(?:entitled to summary judgment|motion.{0,80}(?:granted|denied))\b", s, re.I):
        return "express_relief_resolution"
    return None


def apply_edits(text, edits):
    cursor = 0
    kept = []
    for edit in edits:
        a, b = edit["start"], edit["end"]
        require(cursor <= a < b <= len(text), "Overlapping or invalid offsets")
        require(text[a:b] == edit["removed_text"], "Offset/text mismatch")
        kept.append(text[cursor:a])
        cursor = b
    kept.append(text[cursor:])
    return " ".join(" ".join(kept).split())


def mask_text(text):
    edits, residual = [], []
    previous = ""
    for a, b in sentence_spans(text):
        sentence = text[a:b]
        reason = removal_reason(sentence)
        if not reason and re.fullmatch(r"We (?:agree|disagree)\.", sentence, re.I):
            if re.search(r"\b(?:contend|argue)\w*\b.{0,120}?\bcourt\b.{0,80}?\b(?:erred|properly|improperly)\b.{0,100}?\b" + ACTION + r"\b.{0,160}?\b" + OBJECT + r"\b", outside_citations(previous), re.I):
                reason = "response_to_explicit_relief_argument"
        if reason:
            edits.append({"start": a, "end": b, "reason": reason, "removed_text": sentence,
                          "removed_words": len(sentence.split())})
        elif CUE.search(sentence):
            residual.append({"start": a, "end": b, "text": sentence,
                             "status": "candidate_only_requires_context_review"})
        previous = sentence
    masked = apply_edits(text, edits)
    before, after = len(text.split()), len(masked.split())
    flags = []
    if not edits:
        flags.append("no_direct_outcome_detected")
    if not masked:
        flags.append("empty_output_exclude_from_modeling")
    elif after < 50:
        flags.append("near_empty_under_50_words_review")
    if before and (before-after)/before > .5:
        flags.append("over_half_words_removed_review")
    if residual:
        flags.append("retained_cue_candidates_review")
    if text.count("(") != text.count(")") or text.count("[") != text.count("]"):
        flags.append("unbalanced_brackets_review_segmentation")
    return masked, {"edits": edits, "full_words": before, "masked_words": after,
                    "removed_words": before-after,
                    "removed_word_fraction": (before-after)/before if before else 0,
                    "residual_cue_candidates": residual, "flags": flags}


def build(root):
    mvp = Path(root) / "annotation/submissions/becca/MVP"
    policy_path = mvp / "preprocessing/masked_rules_v1.json"
    policy = json.loads(policy_path.read_text())
    input_paths = {"full": mvp / "data/full_v1/full.jsonl",
                   "full_manifest": mvp / "data/full_v1/manifest.json",
                   "split": mvp / "data/mvp_split_v1/split_manifest.json",
                   "training_review": mvp / "preprocessing/masked_training_review_v1.json",
                   "code": Path(__file__)}
    for name, path in input_paths.items():
        require(digest(path.read_bytes()) == policy["input_sha256"][name], f"Frozen {name} changed")
    full_manifest = json.loads(input_paths["full_manifest"].read_text())
    require(digest(input_paths["full"].read_bytes()) == full_manifest["outputs"]["full.jsonl"], "FULL checksum mismatch")
    # Read only ID assignments. Targets/annotation evidence are never passed to masker.
    split = json.loads(input_paths["split"].read_text())
    partition = {cid: name for name, ids in split["split_case_ids"].items() for cid in ids}
    full_rows = rows(input_paths["full"])
    ids = [r["case_id"] for r in full_rows]
    require(len(ids) == len(set(ids)) == 114, "Expected 114 unique cases")
    require(set(ids) == set(partition) | set(split["pending_case_ids"]) | set(split["excluded_case_ids"]), "Split coverage mismatch")
    audits, model_rows, outputs = [], [], {}
    for row in full_rows:
        cid, text = row["case_id"], row["text"]
        masked, audit = mask_text(text)
        audits.append({"case_id": cid, "partition": partition.get(cid, "pending_or_excluded"),
                       "full_sha256": digest(text.encode()), "masked_sha256": digest(masked.encode()),
                       "rule_version": RULE_VERSION, **audit})
        model_rows.append({"case_id": cid, "text": masked})
        outputs[f"texts/{cid}.txt"] = (masked + "\n").encode()
    summary = {"version": VERSION, "case_count": len(ids),
               "partition_counts": dict(Counter(a["partition"] for a in audits)),
               "full_words": sum(a["full_words"] for a in audits),
               "masked_words": sum(a["masked_words"] for a in audits),
               "removed_sentences": sum(len(a["edits"]) for a in audits),
               "removal_reasons": dict(Counter(e["reason"] for a in audits for e in a["edits"])),
               "flag_counts": dict(Counter(f for a in audits for f in a["flags"])),
               "empty_case_ids": [a["case_id"] for a in audits if not a["masked_words"]],
               "near_empty_case_ids": [a["case_id"] for a in audits if 0 < a["masked_words"] < 50],
               "review_status": "automated masking with training sample assistant review; not human-reviewed",
               "labels_or_annotation_evidence_used": False,
               "frozen_ids_splits_and_labels_changed": False}
    summary["removed_words"] = summary["full_words"] - summary["masked_words"]
    summary["removed_word_fraction"] = summary["removed_words"] / summary["full_words"]
    for name, obj in (("masked.jsonl", model_rows), ("removal_audit.jsonl", audits)):
        outputs[name] = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in obj).encode()
    outputs["summary.json"] = json_bytes(summary)
    outputs["manifest.json"] = json_bytes({"version": VERSION, "rule_version": RULE_VERSION,
        "policy_sha256": digest(policy_path.read_bytes()), "input_sha256": policy["input_sha256"],
        "outputs": {name: digest(data) for name, data in outputs.items()}, "case_ids": ids,
        "offset_unit": "Python Unicode code points in frozen FULL text (end exclusive)",
        "word_count_policy": "Whitespace-separated words; not encoder tokens",
        "empty_text_policy": "Retain ID and flag empty/near-empty; no automatic split or label changes; empty text cannot enter training",
        "evaluation_policy": "Apply frozen rules without evaluation-specific overrides; flags remain review candidates"})
    out = mvp / "data" / VERSION
    for name, data in outputs.items():
        require(not (out/name).exists() or (out/name).read_bytes() == data, "Existing version differs; use new version")
    for name, data in outputs.items():
        write_immutable(out/name, data)
    return summary, audits
