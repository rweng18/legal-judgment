"""Run the complete Batch B comparison with frozen LEGAL-BERT."""
import argparse
import csv
import json
import subprocess
import sys
import time
import warnings
from pathlib import Path

from sklearn.exceptions import ConvergenceWarning

from data import sha_file
from encoder import HERE, SETTINGS, feature_vectors, load_tokenizer
from experiment import save_run
from lengths import measure
from modeling import BERT, SEED, evaluate
from outputs import new_directory, write_csv, write_json
from run_svm import load_reference


def run(package, lexical_run, destination, assume_labels_reviewed=False):
    if destination.exists():
        raise FileExistsError(f"Choose a fresh output directory: {destination}")
    release, rows, folds, previous = load_reference(package, lexical_run, assume_labels_reviewed)
    saved_selection = json.loads((lexical_run / "selection.json").read_text())
    with (lexical_run / "predictions.csv").open(newline="", encoding="utf-8") as stream:
        old_predictions = list(csv.DictReader(stream))
    started = time.perf_counter()
    results = []
    reproduction = {}
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        for name in ("Majority", "TFIDF_LR", "TFIDF_SVM"):
            result = evaluate(name, rows, folds)
            if saved_selection[name] != {"selected_C": result["selected_C"], "grid": result["cv"]}:
                raise ValueError(f"{name} selection differs from the saved lexical run.")
            old = [r for r in old_predictions if r["model"] == name]
            if len(old) != len(result["predictions"]):
                raise ValueError(f"Prediction coverage changed for {name}.")
            score_differences = []
            for prior, current in zip(old, result["predictions"]):
                for field in ("case_id", "variant", "label", "prediction"):
                    if prior[field] != str(current[field]):
                        raise ValueError(f"{name} prediction differs for {current['case_id']}.")
                if current["decision_score"] is not None:
                    score_differences.append(abs(float(prior["decision_score"]) - current["decision_score"]))
            reproduction[name] = {"predictions_and_cv_identical": True,
                                  "maximum_decision_score_difference": max(score_differences, default=0)}
            results.append(result)
            print(f"Reproduced {name}", flush=True)
        tokenizer = load_tokenizer()
        lengths, length_summary = measure({r["case_id"]: r for r in rows}, tokenizer)
        length_reference = package / "B_v2_exact_token_lengths/case_lengths.csv"
        with length_reference.open(newline="", encoding="utf-8") as stream:
            prior_lengths = {r["case_id"]: r for r in csv.DictReader(stream)}
        count_fields = [f"{variant}_{unit}" for variant in ("FULL", "MASKED")
                        for unit in ("words", "tokens", "chunks", "final_chunk")]
        if (set(prior_lengths) != {r["case_id"] for r in lengths}
                or any(r[key] != int(prior_lengths[r["case_id"]][key])
                       for r in lengths for key in count_fields)):
            raise ValueError("Tokenization differs from the package's pinned-tokenizer report.")
        tokenizer_details = {
            "class": type(tokenizer).__name__, "do_lower_case": tokenizer.do_lower_case,
            "vocab_size": tokenizer.vocab_size, "padding_side": tokenizer.padding_side,
            "cls_token_id": tokenizer.cls_token_id, "sep_token_id": tokenizer.sep_token_id,
            "pad_token_id": tokenizer.pad_token_id,
        }
        encoder_start = time.perf_counter()
        vectors = feature_vectors(rows, HERE / ".cache/vectors", SEED)
        encoder_seconds = time.perf_counter() - encoder_start
        results.append(evaluate(BERT, rows, folds, vectors))
    release["lexical_reference"] = {
        name: sha_file(lexical_run / name)
        for name in ("run.json", "splits.csv", "selection.json", "predictions.csv")
    }
    release["majority_reference"] = previous["release"]["majority_reference"]
    snapshot = (HERE / ".cache/huggingface" / ("models--" + SETTINGS["encoder"].replace("/", "--"))
                / "snapshots" / SETTINGS["revision"])
    checkpoint_hashes = {p.name: sha_file(p) for p in snapshot.iterdir() if p.is_file()}
    # Build the entire package before publishing its destination directory.
    with new_directory(destination) as staging:
        bundle = save_run(staging / "bundle", release, rows, folds, results, vectors=vectors)
        write_csv(bundle / "case_lengths.csv", lengths)
        write_json(bundle / "length_summary.json", {"encoder": SETTINGS, "splits": length_summary})
        write_json(bundle / "verification.json", {
            "reference_lexical_results": reproduction, "saved_folds_reused": True,
            "encoder_frozen": True, "content_tokens_per_chunk": 510,
            "tokenizer": tokenizer_details, "checkpoint_files_sha256": checkpoint_hashes,
            "supplied_length_counts_match": True, "length_reference_sha256": sha_file(length_reference),
            "encoder_seconds": encoder_seconds, "total_seconds": time.perf_counter() - started,
            "development_cases": len(rows), "evaluation_cases": sum(r["period"] == "validation" for r in rows),
        })
        installed = subprocess.run([sys.executable, "-m", "pip", "freeze"], check=True,
                                   text=True, capture_output=True).stdout
        (bundle / "requirements-lock.txt").write_text(installed, encoding="utf-8")
        for path in bundle.iterdir():
            path.rename(staging / path.name)
        bundle.rmdir()
    print(json.dumps({"output": str(destination), "selected_C": results[-1]["selected_C"],
                      "metrics": results[-1]["metrics"]}, indent=2))
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("lexical_run", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--assume-labels-reviewed", action="store_true", required=True)
    args = parser.parse_args()
    run(args.package, args.lexical_run, args.out, args.assume_labels_reviewed)
