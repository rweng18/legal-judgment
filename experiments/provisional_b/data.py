"""Read Hayden's frozen release and keep reserved test text out of development."""
import hashlib
import json
from datetime import date
from pathlib import Path

PERIODS = {"train", "validation"}
VARIANTS = ("FULL", "MASKED")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return digest(Path(path).read_bytes())


def text_field(row, key):
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Expected nonempty {key} in {row.get('case_id', 'release')}")
    return value


def read_rows(path, expected_hash=None):
    data = Path(path).read_bytes()
    if expected_hash and digest(data) != expected_hash:
        raise ValueError(f"Content differs from frozen checksum: {path}")
    rows = {}
    for number, line in enumerate(data.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        key = text_field(row, "case_id")
        if key in rows:
            raise ValueError(f"Duplicate case {key} at {path}:{number}")
        rows[key] = row
    return rows


def period_for(date_filed):
    year = date.fromisoformat(date_filed).year
    if not 2010 <= year <= 2024:
        raise ValueError(f"Date outside project periods: {date_filed}")
    return "train" if year <= 2020 else "validation" if year <= 2022 else "test"


def development_texts(path, checksum=None):
    rows = read_rows(path, checksum)
    for key, row in rows.items():
        if row.get("period") not in PERIODS or row.get("period") != period_for(row["date_filed"]):
            raise ValueError(f"Expected a development case in the correct period: {key}")
        if row.get("batch") not in {"B", "C"}:
            raise ValueError(f"Expected batch B or C for {key}")
        for variant in VARIANTS:
            text_field(row["texts"], variant)
    return rows


def load_release(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Supply Hayden's frozen B+C release.json: {path}")
    release = json.loads(path.read_text(encoding="utf-8"))
    if release.get("status") != "frozen":
        raise ValueError("Wait for a release explicitly marked frozen.")
    for field in ("dataset_version", "split_version", "mask_version", "reviewed_by"):
        text_field(release, field)
    files = release["sha256"]
    for name in ("manifest.jsonl", "development.jsonl"):
        checksum = files.get(name, "")
        if len(checksum) != 64 or any(ch not in "0123456789abcdef" for ch in checksum):
            raise ValueError(f"Missing or invalid SHA-256 for {name}")
    manifest = read_rows(path.parent / "manifest.jsonl", files["manifest.jsonl"])
    expected = {}
    families = {}
    for key, meta in manifest.items():
        period = period_for(meta["date_filed"])
        if meta["period"] != period or meta["batch"] not in {"B", "C"}:
            raise ValueError(f"Unexpected split or batch for {key}")
        if meta["eligibility"] not in {"include", "review", "exclude"}:
            raise ValueError(f"Unknown eligibility for {key}")
        if meta["eligibility"] != "include":
            continue
        family = text_field(meta, "family_id")
        if families.setdefault(family, period) != period:
            raise ValueError(f"Resolve cross-period family {family} before freezing.")
        if meta.get("calibration_exposure") and period != "train":
            raise ValueError(f"Calibration-exposed case outside training: {key}")
        if period == "test":
            continue
        if meta.get("review_status") != "reviewed" or type(meta.get("label")) is not int or meta["label"] not in (0, 1):
            raise ValueError(f"Expected a reviewed binary label for {key}")
        expected[key] = meta
    if {r["batch"] for r in manifest.values()} != {"B", "C"}:
        raise ValueError("The release must cover both B and C.")
    texts = development_texts(path.parent / "development.jsonl", files["development.jsonl"])
    if expected.keys() != texts.keys():
        raise ValueError(f"Development ID mismatch: {sorted(expected.keys() ^ texts.keys())}")
    joined = []
    for key in sorted(expected):
        meta = expected[key]
        if any(meta[field] != texts[key][field] for field in ("period", "date_filed", "batch")):
            raise ValueError(f"Text metadata disagrees with manifest for {key}")
        joined.append({**meta, "texts": texts[key]["texts"]})
    for period in PERIODS:
        if {r["label"] for r in joined if r["period"] == period} != {0, 1}:
            raise ValueError(f"Both outcome classes are required in {period}.")
    return release, joined
