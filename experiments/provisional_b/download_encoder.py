"""Download the pinned LEGAL-BERT PyTorch checkpoint and tokenizer."""
from pathlib import Path

from huggingface_hub import snapshot_download

from encoder import HERE, SETTINGS


if __name__ == "__main__":
    snapshot = Path(snapshot_download(
        SETTINGS["encoder"], revision=SETTINGS["revision"],
        cache_dir=str(HERE / ".cache/huggingface"),
        allow_patterns=["config.json", "pytorch_model.bin", "vocab.txt",
                        "tokenizer_config.json", "special_tokens_map.json", "tokenizer.json"],
    ))
    for name in ("config.json", "pytorch_model.bin", "vocab.txt"):
        if not (snapshot / name).is_file():
            raise FileNotFoundError(f"Missing pinned encoder file: {name}")
    print(snapshot)
