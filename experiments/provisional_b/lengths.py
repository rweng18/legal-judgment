"""Hayden's tokenizer-only development length report. No classifier or labels required."""
import argparse
from importlib.metadata import version
from pathlib import Path

import numpy as np

from data import VARIANTS, development_texts, sha_file
from encoder import SETTINGS, WIDTH, content_chunks, load_tokenizer
from outputs import new_directory, write_csv, write_json


def stats(values):
    minimum, median, p90, maximum = np.percentile(values, [0, 50, 90, 100])
    return dict(min=float(minimum), median=float(median), mean=float(np.mean(values)),
                p90=float(p90), max=float(maximum))


def measure(rows, tokenizer):
    measurements = []
    for key, row in sorted(rows.items()):
        item = {name: row[name] for name in ("case_id", "batch", "period")}
        for variant in VARIANTS:
            text = row["texts"][variant]
            chunks = content_chunks(tokenizer, text)
            tokens = sum(map(len, chunks))
            item.update({f"{variant}_words": len(text.split()), f"{variant}_tokens": tokens,
                         f"{variant}_chunks": len(chunks), f"{variant}_final_chunk": len(chunks[-1]),
                         f"{variant}_over_one_input": tokens > WIDTH})
        for unit in ("words", "tokens", "chunks"):
            full = item[f"FULL_{unit}"]
            change = full - item[f"MASKED_{unit}"]
            item[f"{unit}_removed"] = change
            item[f"{unit}_removed_pct"] = 100 * change / full
        measurements.append(item)
    if not measurements:
        raise ValueError("No development cases to summarize.")
    summary = {}
    for period in sorted({r["period"] for r in measurements}):
        subset = [r for r in measurements if r["period"] == period]
        group = {"cases": len(subset)}
        for variant in VARIANTS:
            group[variant] = {unit: stats([r[f"{variant}_{unit}"] for r in subset])
                              for unit in ("words", "tokens", "chunks")}
            group[variant]["fraction_over_one_input"] = sum(r[f"{variant}_over_one_input"] for r in subset) / len(subset)
            group[variant]["total_chunks"] = sum(r[f"{variant}_chunks"] for r in subset)
        group["paired_change"] = {f"{unit}_{suffix}": stats([r[f"{unit}_{suffix}"] for r in subset])
                                  for unit in ("words", "tokens", "chunks") for suffix in ("removed", "removed_pct")}
        summary[period] = group
    return measurements, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    checksum = sha_file(args.development)
    rows = development_texts(args.development, checksum)
    measurements, summary = measure(rows, load_tokenizer())
    with new_directory(args.out) as out:
        write_csv(out / "case_lengths.csv", measurements)
        write_json(out / "length_summary.json", {"development_sha256": checksum, "encoder": SETTINGS,
                   "transformers": version("transformers"), "numpy": version("numpy"), "splits": summary})


if __name__ == "__main__":
    main()
