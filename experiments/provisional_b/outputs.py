"""Publish complete output directories and retain earlier runs."""
import csv
import json
import tempfile
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def new_directory(destination):
    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"Choose a new output directory: {destination}")
    with tempfile.TemporaryDirectory(dir=destination.parent) as temp:
        staging = Path(temp) / "ready"
        staging.mkdir()
        yield staging
        if destination.exists():
            raise FileExistsError(destination)
        staging.rename(destination)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
