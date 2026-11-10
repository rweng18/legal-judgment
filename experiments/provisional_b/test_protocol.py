"""Synthetic checks for the B+C protocol. All output is temporary."""
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from data import load_release, sha_file
from encoder import SETTINGS, content_chunks, pool_chunks
from experiment import prepare, save_run
from lengths import measure
from modeling import BERT, LEXICAL, evaluate, grouped_folds


def fixture(directory):
    """Make a small mixed-batch release with one multi-case training family."""
    manifest, texts = [], []
    for i in range(17):
        period = "train" if i < 12 else "validation" if i < 16 else "test"
        year = {"train": 2016, "validation": 2022, "test": 2024}[period]
        batch = "B" if (i // 2) % 2 == 0 else "C"
        common = {"case_id": f"fake-{i}", "date_filed": f"{year}-03-02", "period": period, "batch": batch}
        label = int(i in (1, 3, 5, 7, 13, 15))
        manifest.append({**common, "family_id": "family-0" if i == 2 else f"family-{i}",
                         "eligibility": "include", "label": label, "review_status": "reviewed"})
        if period != "test":
            masked = "Earlier testimony disputed " + ("the notice evidence" if label else "the warning evidence")
            texts.append({**common, "texts": {"MASKED": masked, "FULL": masked + (" reversed" if label else " affirmed")}})
    for name, values in (("manifest.jsonl", manifest), ("development.jsonl", texts)):
        (directory / name).write_text("".join(json.dumps(v) + "\n" for v in values))
    release = {"status": "frozen", "reviewed_by": "synthetic test", "dataset_version": "fixture",
               "split_version": "fixture", "mask_version": "fixture",
               "sha256": {name: sha_file(directory / name) for name in ("manifest.jsonl", "development.jsonl")}}
    path = directory / "release.json"
    path.write_text(json.dumps(release))
    return path


class WordTokenizer:
    def encode(self, text, **kwargs):
        return list(range(len(text.split())))


class ProtocolTests(unittest.TestCase):
    def test_paired_lexical_run(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            release, rows, folds = prepare(fixture(root))
            training = [r for r in rows if r["period"] == "train"]
            self.assertEqual(len(folds), 3)
            for fit, hold in folds:
                self.assertTrue({training[i]["family_id"] for i in fit}.isdisjoint(
                                {training[i]["family_id"] for i in hold}))
                self.assertEqual({training[i]["label"] for i in hold}, {0, 1})
            results = [evaluate(name, rows, folds) for name in ("Majority", *LEXICAL)]
            self.assertTrue(all(r["prediction"] == 0 for r in results[0]["predictions"]))
            self.assertEqual(results[0]["metrics"][0]["balanced_accuracy"], .5)
            for model in results[1:]:
                self.assertEqual(model["selected_C"], .1)  # all three tie on this fixture
                self.assertEqual({p["C"] for p in model["predictions"]}, {model["selected_C"]})
            out = save_run(root / "run", release, rows, folds, results)
            self.assertTrue((out / "confusion_matrices.png").is_file())
            reporting = json.loads((out / "reporting_summary.json").read_text())
            counts = reporting["class_counts"]
            self.assertEqual([(c["label_0"], c["label_1"]) for c in counts[:2]], [(8, 4), (2, 2)])
            for fold in (1, 2, 3):
                pair = [c for c in counts if c["fold"] == fold]
                self.assertEqual(sum(c["label_0"] for c in pair), 8)
                self.assertEqual(sum(c["label_1"] for c in pair), 4)
            majority = reporting["conditions"][0]
            self.assertEqual(majority["counts"], [[2, 0], [2, 0]])
            self.assertEqual(majority["row_normalized"], [[1., 0.], [1., 0.]])
            self.assertEqual(json.loads((out / "run.json").read_text())["release"], release)
            with self.assertRaises(FileExistsError):
                save_run(out, release, rows, folds, results)

    def test_masked_training_only_selection(self):
        with tempfile.TemporaryDirectory() as folder:
            _, rows, folds = prepare(fixture(Path(folder)))
            original = evaluate("TFIDF_LR", rows, folds)
            for row in rows:
                row["texts"]["FULL"] = "changed full input for all rows"
                if row["period"] == "validation":
                    row["label"] = 1 - row["label"]
                    row["texts"]["MASKED"] = "changed validation"
            changed = evaluate("TFIDF_LR", rows, folds)
            self.assertEqual(original["cv"], changed["cv"])
            # Exercise the complete downstream encoder classifier with synthetic vectors.
            fake = np.array([[i % 2, i % 3] for i in range(len(rows))])
            bert = evaluate(BERT, rows, folds, {"FULL": fake, "MASKED": fake})
            self.assertEqual(len(bert["predictions"]), 8)

    def test_folds_reduce_or_refuse_by_family_count(self):
        rows = [{"family_id": f"g{i}", "label": y, "period": "train"}
                for i, y in enumerate((0, 0, 0, 1, 1))]
        self.assertEqual(len(grouped_folds(rows)), 2)
        with self.assertRaisesRegex(ValueError, "distinct training families"):
            grouped_folds(rows[:-1])

    def test_release_guards(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = fixture(root)
            release = json.loads(path.read_text())
            development = root / "development.jsonl"
            development.write_bytes(development.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "checksum"):
                load_release(path)
            fixture(root)
            manifest = root / "manifest.jsonl"
            records = [json.loads(line) for line in manifest.read_text().splitlines()]
            records[-1]["family_id"] = records[0]["family_id"]  # crosses into reserved period
            manifest.write_text("".join(json.dumps(r) + "\n" for r in records))
            release["sha256"]["manifest.jsonl"] = sha_file(manifest)
            path.write_text(json.dumps(release))
            with self.assertRaisesRegex(ValueError, "cross-period family"):
                load_release(path)
            fixture(root)
            rows = [json.loads(line) for line in development.read_text().splitlines()]
            rows[-1]["period"], rows[-1]["date_filed"] = "test", "2024-01-01"
            development.write_text("".join(json.dumps(r) + "\n" for r in rows))
            release = json.loads(path.read_text())
            release["sha256"]["development.jsonl"] = sha_file(development)
            path.write_text(json.dumps(release))
            with self.assertRaisesRegex(ValueError, "development case"):
                load_release(path)
            fixture(root)
            development.write_text(development.read_text().splitlines()[0] + "\n")
            release = json.loads(path.read_text())
            release["sha256"]["development.jsonl"] = sha_file(development)
            path.write_text(json.dumps(release))
            with self.assertRaisesRegex(ValueError, "ID mismatch"):
                load_release(path)

    def test_measured_chunk_boundaries(self):
        tokenizer = WordTokenizer()
        self.assertEqual([len(c) for c in content_chunks(tokenizer, "word " * 1100)], [510, 510, 80])
        rows = {"case": {"case_id": "case", "batch": "C", "period": "validation",
                          "texts": {"FULL": "word " * 511, "MASKED": "word " * 510}}}
        cases, summary = measure(rows, tokenizer)
        self.assertEqual(cases[0]["tokens_removed"], 1)
        self.assertEqual(cases[0]["chunks_removed"], 1)
        self.assertEqual(summary["validation"]["FULL"]["fraction_over_one_input"], 1)
        self.assertEqual(summary["validation"]["MASKED"]["fraction_over_one_input"], 0)
        self.assertEqual(summary["validation"]["MASKED"]["words"]["p90"], 510)

    def test_content_weighted_pooling(self):
        from types import SimpleNamespace

        class ToyTokenizer:
            def prepare_for_model(self, ids, **kwargs):
                return [100, *ids, 101]

            def pad(self, rows, **kwargs):
                width = max(map(len, rows))
                return {"input_ids": np.asarray([r + [99] * (width - len(r)) for r in rows]),
                        "attention_mask": np.asarray([[1] * len(r) + [0] * (width - len(r)) for r in rows]),
                        "special_tokens_mask": np.asarray([[1] + [0] * (len(r) - 2) + [1]
                                                            + [0] * (width - len(r)) for r in rows])}

        def model(input_ids, attention_mask):
            hidden = np.broadcast_to(input_ids[:, :, None], (*input_ids.shape, SETTINGS["hidden_size"]))
            return SimpleNamespace(last_hidden_state=hidden)

        vector = pool_chunks(model, ToyTokenizer(), [[2] * 510, [4]])
        np.testing.assert_allclose(vector, (510 * 2 + 4) / 511, rtol=1e-6)


if __name__ == "__main__":
    unittest.main()
