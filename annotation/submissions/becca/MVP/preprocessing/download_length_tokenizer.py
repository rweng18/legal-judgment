"""Fetch only the pinned tokenizer/configuration; never encoder weights."""
from pathlib import Path
import urllib.request
from huggingface_hub import snapshot_download
from length_statistics import MODEL, REVISION

if __name__ == "__main__":
    # Fail promptly on unavailable network before the hub client's retry loop.
    with urllib.request.urlopen(f"https://huggingface.co/{MODEL}/resolve/{REVISION}/config.json", timeout=10) as response:
        response.read()
    mvp = Path(__file__).resolve().parents[1]
    snapshot = snapshot_download(MODEL, revision=REVISION,
        cache_dir=str(mvp / ".cache/huggingface"),
        allow_patterns=["config.json", "vocab.txt", "tokenizer_config.json", "special_tokens_map.json"])
    print("Tokenizer snapshot:", snapshot)
