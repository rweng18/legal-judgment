"""Family-grouped training folds, MASKED-only selection and paired evaluation."""
from collections import defaultdict

import numpy as np
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

from data import VARIANTS

SEED = 20261023
GRID = (0.1, 1.0, 10.0)
LEXICAL = ("TFIDF_LR", "TFIDF_SVM")
BERT = "LEGAL_BERT_LR"


def grouped_folds(rows, seed=SEED):
    if any(r["period"] != "train" for r in rows):
        raise ValueError("Only training-period cases can enter cross-validation.")
    by_family = defaultdict(list)
    for i, row in enumerate(rows):
        by_family[row["family_id"]].append(i)
    y = np.array([r["label"] for r in rows])
    counts = {g: np.bincount(y[indices], minlength=2) for g, indices in by_family.items()}
    k = min(3, *(sum(c[label] > 0 for c in counts.values()) for label in (0, 1)))
    if k < 2:
        raise ValueError("Each outcome must occur in at least two distinct training families.")
    totals = np.sum(list(counts.values()), axis=0)
    rng = np.random.default_rng(seed)
    best_cost = float("inf")
    best = None
    # Seed both classes in every fold. A mixed family supplies both at once.
    # Allocate remaining families to balance each fold's share of each class.
    for attempt in range(16):
        order = list(counts)
        rng.shuffle(order)
        order.sort(key=lambda g: max(counts[g] / totals), reverse=True)
        loads = np.zeros((k, 2), dtype=int)
        assigned = {}

        def assign(group, fold):
            assigned[group] = fold
            loads[fold] += counts[group]

        mixed = [g for g in order if all(counts[g])]
        for fold, group in enumerate(mixed[:k]):
            assign(group, fold)
        for label in (0, 1):
            available = [g for g in order if g not in assigned and counts[g][label] > 0]
            for fold, group in zip(np.flatnonzero(loads[:, label] == 0), available):
                assign(group, fold)
        for group in order:
            if group in assigned:
                continue
            before = np.square(loads / totals).sum(axis=1)
            after = np.square((loads + counts[group]) / totals).sum(axis=1)
            assign(group, int(np.argmin(after - before)))
        cost = np.square(loads / totals - 1 / k).sum()
        if cost < best_cost:
            best_cost, best = cost, assigned
    membership = np.array([best[r["family_id"]] for r in rows])
    folds = [(np.flatnonzero(membership != f), np.flatnonzero(membership == f)) for f in range(k)]
    for fit, hold in folds:
        if set(y[fit]) != {0, 1} or set(y[hold]) != {0, 1}:
            raise RuntimeError("Grouped fold lacks a class.")
    return folds


def estimator(name, c):
    if name == "TFIDF_SVM":
        clf = LinearSVC(C=c, class_weight="balanced", dual="auto", random_state=SEED, max_iter=20000)
    elif name in ("TFIDF_LR", BERT):
        clf = LogisticRegression(C=c, penalty="l2", solver="liblinear", class_weight="balanced",
                                 max_iter=10000, random_state=SEED)
    else:
        raise ValueError(f"Unknown model: {name}")
    transform = (StandardScaler() if name == BERT else
                 TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=30000, norm="l2"))
    return make_pipeline(transform, clf)


def scores(y, prediction):
    matrix = confusion_matrix(y, prediction, labels=[0, 1])
    return {
        "accuracy": float(accuracy_score(y, prediction)),
        "balanced_accuracy": float(balanced_accuracy_score(y, prediction)),
        "macro_f1": float(f1_score(y, prediction, labels=[0, 1], average="macro", zero_division=0)),
        "recall_0": float(matrix[0, 0] / matrix[0].sum()),
        "recall_1": float(matrix[1, 1] / matrix[1].sum()),
        "confusion_matrix": matrix.tolist(),
    }


def select_c(name, masked_train, y, folds):
    trials = []
    for c in GRID:
        template = estimator(name, c)
        results = []
        for number, (fit, hold) in enumerate(folds, start=1):
            pipeline = clone(template).fit(masked_train[fit], y[fit])
            result = scores(y[hold], pipeline.predict(masked_train[hold]))
            results.append({"fold": number, **result})
        trials.append({"C": c, "folds": results,
                       **{m: float(np.mean([r[m] for r in results]))
                          for m in ("balanced_accuracy", "macro_f1")}})
    winner = max(trials, key=lambda t: (round(t["balanced_accuracy"], 12),
                                        round(t["macro_f1"], 12), -t["C"]))
    return winner["C"], trials


def evaluate(name, rows, folds, features=None):
    train = np.array([r["period"] == "train" for r in rows])
    dev = [r for r in rows if r["period"] == "validation"]
    labels = np.array([r["label"] for r in rows])
    y = labels[train]
    majority = name == "Majority"
    if majority:
        dummy = DummyClassifier(strategy="most_frequent").fit(np.zeros((len(y), 1)), y)
        selected, trials = None, []
    else:
        if features is None:
            features = {v: np.array([r["texts"][v] for r in rows], dtype=object) for v in VARIANTS}
        selected, trials = select_c(name, features["MASKED"][train], y, folds)
    metrics, predictions = [], []
    for variant in VARIANTS:
        if majority:
            yp = dummy.predict(np.zeros((len(dev), 1)))
            decisions = [None] * len(dev)
        else:
            pipeline = estimator(name, selected).fit(features[variant][train], y)
            yp = pipeline.predict(features[variant][~train])
            decisions = pipeline.decision_function(features[variant][~train]).tolist()
        metrics.append({"model": name, "variant": variant, "C": selected,
                        "n": len(dev), **scores(labels[~train], yp)})
        for row, pred, decision in zip(dev, yp, decisions):
            predictions.append({k: row[k] for k in ("case_id", "batch", "family_id", "period")}
                               | {"model": name, "variant": variant, "C": selected,
                                  "label": row["label"], "prediction": int(pred), "decision_score": decision})
    return {"model": name, "selected_C": selected, "cv": trials, "metrics": metrics, "predictions": predictions}
