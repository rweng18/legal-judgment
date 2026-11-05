"""Shared LEGAL-BERT tokenization, chunking and frozen opinion vectors."""
import json
import os
import tempfile
from importlib.metadata import version
from pathlib import Path

import numpy as np

from data import digest

HERE = Path(__file__).resolve().parent
SETTINGS = json.loads((HERE / "encoder_settings.json").read_text())
WIDTH = SETTINGS["content_tokens"]


def load_tokenizer():
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        SETTINGS["encoder"], revision=SETTINGS["revision"], use_fast=SETTINGS["use_fast"]
    )
    if (type(tokenizer).__name__ != SETTINGS["tokenizer"]
            or tokenizer.num_special_tokens_to_add(pair=False) != 2
            or tokenizer.padding_side != SETTINGS["padding_side"]):
        raise ValueError("Tokenizer differs from the pinned handoff settings.")
    return tokenizer


def content_chunks(tokenizer, text):
    ids = tokenizer.encode(text, add_special_tokens=False, truncation=False, verbose=False)
    if not ids:
        raise ValueError("Tokenization produced empty content. Review the source text.")
    return [ids[i:i + WIDTH] for i in range(0, len(ids), WIDTH)]


def pool_chunks(model, tokenizer, chunks):
    total = np.zeros(SETTINGS["hidden_size"], dtype=np.float64)
    count = 0
    size = SETTINGS["batch_size_chunks"]
    for start in range(0, len(chunks), size):
        batch = chunks[start:start + size]
        encoded = [tokenizer.prepare_for_model(ids, add_special_tokens=True,
                   return_special_tokens_mask=True) for ids in batch]
        inputs = tokenizer.pad(encoded, padding=True, return_tensors="pt")
        specials = np.asarray(inputs.pop("special_tokens_mask"), dtype=bool)
        content = np.asarray(inputs["attention_mask"], dtype=bool) & ~specials
        if inputs["input_ids"].shape[1] > 512 or content.sum(axis=1).tolist() != [len(ids) for ids in batch]:
            raise ValueError("Token coverage or model input length differs from the protocol.")
        # Inference runs on CPU. Sum over all content tokens so the short final
        # chunk receives exactly its share of the opinion's weight.
        hidden = np.asarray(model(**inputs).last_hidden_state)
        total += hidden[content].sum(axis=0, dtype=np.float64)
        count += int(content.sum())
    return (total / count).astype(np.float32)


def feature_vectors(rows, cache, seed):
    import torch
    from transformers import AutoModel

    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(SETTINGS["threads"])
    torch.manual_seed(seed)
    protocol = {"settings": SETTINGS, "encoder_code": digest(Path(__file__).read_bytes()),
                "software": {k: version(k) for k in ("torch", "transformers", "tokenizers", "numpy")}}
    prefix = json.dumps(protocol, sort_keys=True).encode()
    model = tokenizer = None
    features = {}
    for variant in ("MASKED", "FULL"):
        vectors = []
        for row in rows:
            text = row["texts"][variant]
            identity = digest(prefix + b"\0" + text.encode("utf-8"))
            target = cache / (identity + ".npy")
            if target.exists():
                vector = np.load(target, allow_pickle=False)
            else:
                if model is None:
                    tokenizer = load_tokenizer()
                    model = AutoModel.from_pretrained(SETTINGS["encoder"], revision=SETTINGS["revision"])
                    model.eval().requires_grad_(False)
                with torch.inference_mode():
                    vector = pool_chunks(model, tokenizer, content_chunks(tokenizer, text))
                if not np.isfinite(vector).all():
                    raise ValueError(f"Nonfinite embedding for {row['case_id']}")
                with tempfile.NamedTemporaryFile(dir=cache, delete=False) as temporary:
                    np.save(temporary, vector, allow_pickle=False)
                os.replace(temporary.name, target)
            if vector.shape != (SETTINGS["hidden_size"],) or vector.dtype != np.float32 or not np.isfinite(vector).all():
                raise ValueError(f"Invalid vector in cache: {target}")
            vectors.append(vector)
        features[variant] = np.stack(vectors)
    return features
