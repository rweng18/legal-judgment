"""Descriptive lengths for training/development only; no encoder weights needed."""
import hashlib
import importlib.metadata
import json
import math
import platform
import statistics
from pathlib import Path

import model_inputs

MODEL = "nlpaueb/legal-bert-base-uncased"
REVISION = "15b570cbf88259610b082a167dacc190124f60f6"
VERSION = "length_statistics_v1"
CONTENT_SIZE = 510


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def describe(values):
    values = sorted(values)
    if not values:
        raise ValueError("Cannot summarize an empty group")
    position = .9 * (len(values) - 1)
    lo, hi = math.floor(position), math.ceil(position)
    return {"minimum": values[0], "median": statistics.median(values),
            "mean": statistics.mean(values),
            "p90": values[lo] + (values[hi] - values[lo]) * (position - lo),
            "maximum": values[-1]}


def chunk_lengths(count):
    return [min(CONTENT_SIZE, count - start) for start in range(0, count, CONTENT_SIZE)]


def tokenizer_snapshot(mvp):
    from huggingface_hub import snapshot_download
    return Path(snapshot_download(MODEL, revision=REVISION,
                cache_dir=str(Path(mvp) / ".cache/huggingface"), local_files_only=True))


def build(root):
    from transformers import AutoTokenizer
    root = Path(root)
    mvp = root / "annotation/submissions/becca/MVP"
    settings_path = root / "experiments/provisional_a/encoder_settings.json"
    settings = json.loads(settings_path.read_text())
    assert settings["encoder"] == MODEL and settings["revision"] == REVISION
    assert settings["chunking"]["max_content_tokens"] == CONTENT_SIZE
    assert settings["chunking"]["window_step"] == CONTENT_SIZE
    assert settings["chunking"]["overlap_tokens"] == 0
    assert settings["test_processing_enabled"] is False
    snapshot = tokenizer_snapshot(mvp)
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, use_fast=False)
    assert type(tokenizer).__name__ == "BertTokenizer" and not tokenizer.is_fast
    assert tokenizer.do_lower_case and tokenizer.vocab_size == 30522
    assert [tokenizer.cls_token_id, tokenizer.sep_token_id, tokenizer.pad_token_id,
            tokenizer.unk_token_id] == [101, 102, 0, 100]
    assert tokenizer.num_special_tokens_to_add(pair=False) == 2
    indexed, _, manifest, input_report = model_inputs.read_validated(mvp)
    groups = {p: manifest["split_case_ids"][p] for p in ("train", "development")}
    allowed = set(groups["train"] + groups["development"])
    assert len(allowed) == 97
    assert not allowed.intersection(manifest["split_case_ids"]["test"] + manifest["pending_case_ids"])
    per_case = []
    for partition, ids in groups.items():
        for cid in ids:
            for variant in ("FULL", "MASKED"):
                text = indexed[variant][cid]["text"]
                token_ids = tokenizer.encode(text, add_special_tokens=False, truncation=False, verbose=False)
                assert token_ids, f"Empty tokenized output: {cid} {variant}; resolve before statistics release"
                lengths = chunk_lengths(len(token_ids))
                assert sum(lengths) == len(token_ids) and all(1 <= n <= CONTENT_SIZE for n in lengths)
                # Check the tokenizer's actual special-token construction for every chunk.
                for start in range(0, len(token_ids), CONTENT_SIZE):
                    chunk = token_ids[start:start + CONTENT_SIZE]
                    prepared = tokenizer.build_inputs_with_special_tokens(chunk)
                    assert prepared == [101] + chunk + [102] and len(prepared) <= 512
                per_case.append({"case_id": cid, "split": partition, "variant": variant,
                    "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "words": len(text.split()), "content_tokens": len(token_ids),
                    "exceeds_one_input": len(token_ids) > CONTENT_SIZE,
                    "chunks": len(lengths), "chunk_content_lengths": lengths,
                    "final_chunk_content_tokens": lengths[-1],
                    "total_unpadded_input_tokens": len(token_ids) + 2 * len(lengths)})
    assert len(per_case) == 194 and {r["case_id"] for r in per_case} == allowed
    by_id = {(r["case_id"], r["variant"]): r for r in per_case}
    paired = []
    for partition, ids in groups.items():
        for cid in ids:
            full, masked = by_id[cid, "FULL"], by_id[cid, "MASKED"]
            item = {"case_id": cid, "split": partition}
            for metric in ("words", "content_tokens", "chunks"):
                change = full[metric] - masked[metric]
                item.update({f"{metric}_removed": change,
                             f"{metric}_removed_fraction": change / full[metric]})
            item["crossed_to_one_input"] = full["exceeds_one_input"] and not masked["exceeds_one_input"]
            paired.append(item)
    summaries, changes = [], []
    for scope in ("train", "development", "combined"):
        for variant in ("FULL", "MASKED"):
            selected = [r for r in per_case if r["variant"] == variant and (scope == "combined" or r["split"] == scope)]
            exceed = sum(r["exceeds_one_input"] for r in selected)
            summaries.append({"scope": scope, "variant": variant, "cases": len(selected),
                **{metric: describe([r[metric] for r in selected]) for metric in ("words", "content_tokens", "chunks")},
                "exceeding_one_input": exceed, "fraction_exceeding_one_input": exceed / len(selected),
                "total_chunks": sum(r["chunks"] for r in selected)})
        selected = [r for r in paired if scope == "combined" or r["split"] == scope]
        change = {"scope": scope, "cases": len(selected),
                  "cases_crossing_to_one_input": sum(r["crossed_to_one_input"] for r in selected)}
        for metric in ("words", "content_tokens", "chunks"):
            change[metric] = {"absolute_reduction": describe([r[f"{metric}_removed"] for r in selected]),
                             "fractional_reduction": describe([r[f"{metric}_removed_fraction"] for r in selected])}
            total_full = sum(by_id[r["case_id"], "FULL"][metric] for r in selected)
            total_masked = sum(by_id[r["case_id"], "MASKED"][metric] for r in selected)
            change[metric].update(full_total=total_full, masked_total=total_masked,
                                 total_reduction=total_full-total_masked,
                                 corpus_reduction_fraction=(total_full-total_masked)/total_full)
        changes.append(change)
    # Match the saved masking audit for the same selected IDs, without viewing labels/evidence.
    audits = {r["case_id"]: r for r in (json.loads(line) for line in (mvp / "data/masked_v2/removal_audit.jsonl").read_text().splitlines())}
    assert all(r["words_removed"] == audits[r["case_id"]]["removed_words"] for r in paired)
    report = {"version": VERSION, "summary": summaries, "masking_changes": changes,
              "scope": "81 training + 16 development cases; no test/pending tokenization",
              "word_definition": "Whitespace-separated words, matching preprocessing audits",
              "token_definition": "Untruncated content token IDs, before CLS/SEP and padding",
              "p90_definition": "Linear interpolation at 0.90 * (n - 1) on sorted values (type 7)",
              "empty_word_or_token_outputs": [],
              "near_empty_under_50_words": [r["case_id"] + ":" + r["variant"] for r in per_case if r["words"] < 50],
              "all_chunk_checks_passed": True,
              "label_or_split_changes": False}
    files = {"per_case.jsonl": per_case, "paired_changes.jsonl": paired}
    outputs = {name: "".join(json.dumps(r) + "\n" for r in records).encode() for name, records in files.items()}
    jb = lambda obj: (json.dumps(obj, indent=2, allow_nan=False) + "\n").encode()
    outputs["summary.json"] = jb(report)
    outputs["manifest.json"] = jb({"version": VERSION, "model": MODEL, "revision": REVISION,
        "tokenizer_class": type(tokenizer).__name__, "use_fast": False, "content_chunk_size": CONTENT_SIZE,
        "overlap": 0, "selected_case_ids": groups, "excluded_test_case_count": 16, "excluded_pending_case_ids": manifest["pending_case_ids"],
        "inputs": {**input_report["input_sha256"],
                   "experiments/provisional_a/encoder_settings.json": sha(settings_path),
                   "preprocessing/length_statistics.py": sha(Path(__file__)),
                   "preprocessing/model_inputs.py": sha(mvp / "preprocessing/model_inputs.py"),
                   "data/masked_v2/removal_audit.jsonl": sha(mvp / "data/masked_v2/removal_audit.jsonl")},
        "tokenizer_files_sha256": {p.name: sha(p) for p in sorted(snapshot.iterdir()) if p.is_file()},
        "software": {"python": platform.python_version(), **{name: importlib.metadata.version(name) for name in ("transformers", "huggingface-hub", "tokenizers", "nbformat", "nbclient", "ipykernel")}},
        "outputs": {name: hashlib.sha256(data).hexdigest() for name, data in outputs.items()},
        "rerun_policy": "New data/tokenizer/chunk settings require a new statistics version and rerunning affected experiments."})
    out = mvp / "data" / VERSION
    for name, data in outputs.items():
        if (out / name).exists() and (out / name).read_bytes() != data:
            raise ValueError("Existing statistics differ; create a new version")
    out.mkdir(parents=True, exist_ok=True)
    for name, data in outputs.items():
        if not (out / name).exists():
            (out / name).write_bytes(data)
    return report, per_case, paired
