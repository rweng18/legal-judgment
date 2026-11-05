"""Run the frozen B+C development experiment or its lexical stage."""
import argparse
import json
import platform
import subprocess
import sys
from collections import Counter
from importlib import metadata
from pathlib import Path

import numpy as np

from data import VARIANTS, load_release, sha_file
from encoder import HERE, SETTINGS, feature_vectors
from modeling import BERT, GRID, LEXICAL, SEED, estimator, evaluate, grouped_folds
from outputs import new_directory, write_csv, write_json


def prepare(path):
    release, rows = load_release(path)
    training = [r for r in rows if r["period"] == "train"]
    return release, rows, grouped_folds(training)


def software():
    versions = {}
    for package in ("numpy", "scipy", "scikit-learn", "matplotlib", "torch", "transformers",
                    "tokenizers", "huggingface-hub", "pandas", "nbformat", "nbclient", "ipykernel"):
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = None
    return versions


def confusion_plot(metrics, path):
    from matplotlib.figure import Figure

    names = list(dict.fromkeys(r["model"] for r in metrics))
    cells = {(r["model"], r["variant"]): np.asarray(r["confusion_matrix"]) for r in metrics}
    fig = Figure(figsize=(6.5, 2.7 * len(names)), constrained_layout=True)
    axes = fig.subplots(len(names), 2, squeeze=False)
    for i, name in enumerate(names):
        for j, variant in enumerate(VARIANTS):
            ax = axes[i, j]
            matrix = cells[name, variant]
            frac = matrix / matrix.sum(axis=1, keepdims=True)
            ax.imshow(frac, cmap="Blues", vmin=0, vmax=1)
            for a, b in np.ndindex(2, 2):
                ax.text(b, a, f"{matrix[a, b]}\n({frac[a, b]:.0%})", ha="center", va="center",
                        color="white" if frac[a, b] > .55 else "black")
            ax.set(title=f"{name} · {variant}", xlabel="Predicted", ylabel="Reviewed",
                   xticks=[0, 1], yticks=[0, 1])
    fig.suptitle("Development cases · 0 affirmed, 1 reversed/vacated")
    fig.savefig(path, dpi=150)


def parameters(result):
    if result["model"] == "Majority":
        return {"classifier": "DummyClassifier", "strategy": "most_frequent", "tie_label": 0}
    pipeline = estimator(result["model"], result["selected_C"])
    return {step: {k: (v.__name__ if isinstance(v, type) else v)
                   for k, v in obj.get_params(deep=False).items()} for step, obj in pipeline.steps}


def save_run(destination, release, rows, folds, results):
    expected = {r["case_id"]: r["label"] for r in rows if r["period"] == "validation"}
    for result in results:
        for variant in VARIANTS:
            pp = [p for p in result["predictions"] if p["variant"] == variant]
            if len(pp) != len(expected) or {p["case_id"]: p["label"] for p in pp} != expected:
                raise ValueError("Paired evaluation must use identical cases and labels.")
    training = [r for r in rows if r["period"] == "train"]
    membership = {training[i]["case_id"]: f for f, (_, hold) in enumerate(folds, 1) for i in hold}
    all_metrics = [metric for result in results for metric in result["metrics"]]
    files = sorted(HERE.glob("*.py")) + [HERE / n for n in ("encoder_settings.json", "requirements.txt", "provisional_b.ipynb")]
    git = subprocess.run(["git", "-C", str(HERE), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    with new_directory(destination) as out:
        write_json(out / "run.json", {
            "release": release, "evaluation": "2021–2022 development", "class_order": [0, 1],
            "class_names": ["affirmed", "reversed/vacated"], "seed": SEED, "C_grid": GRID,
            "selection": "MASKED only; mean fold balanced accuracy, mean macro F1, smaller C",
            "cv_folds": len(folds), "fold_method": "seeded family allocation balancing both classes",
            "training_class_counts": dict(Counter(str(r["label"]) for r in training)),
            "encoder_settings": SETTINGS, "models": {r["model"]: parameters(r) for r in results},
            "python": sys.version, "platform": platform.platform(), "software": software(),
            "git_commit": git.stdout.strip() or None, "code_sha256": {p.name: sha_file(p) for p in files},
        })
        write_csv(out / "splits.csv", [
            {k: row[k] for k in ("case_id", "family_id", "batch", "date_filed", "label", "period")}
            | {"held_out_cv_fold": membership.get(row["case_id"])} for row in rows])
        write_json(out / "selection.json", {r["model"]: {"selected_C": r["selected_C"], "grid": r["cv"]}
                                          for r in results})
        write_csv(out / "predictions.csv", [p for r in results for p in r["predictions"]])
        write_csv(out / "results.csv", [{k: v for k, v in r.items() if k != "confusion_matrix"}
                                        for r in all_metrics])
        write_json(out / "confusion_matrices.json", {"class_order": [0, 1], "axes": ["true", "predicted"],
                   "conditions": [{"model": r["model"], "variant": r["variant"], "counts": r["confusion_matrix"]}
                                  for r in all_metrics]})
        confusion_plot(all_metrics, out / "confusion_matrices.png")
    return Path(destination).resolve()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release", type=Path, help="Path to Hayden's release.json")
    parser.add_argument("out", type=Path, help="A fresh directory for this run")
    parser.add_argument("--lexical-only", action="store_true")
    parser.add_argument("--cache", type=Path, default=HERE / ".cache/vectors")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Use a new output directory.")
    release, rows, folds = prepare(args.release)
    results = [evaluate(name, rows, folds) for name in ("Majority", *LEXICAL)]
    if not args.lexical_only:
        results.append(evaluate(BERT, rows, folds, feature_vectors(rows, args.cache, SEED)))
    print(save_run(args.out, release, rows, folds, results))


if __name__ == "__main__":
    main()
