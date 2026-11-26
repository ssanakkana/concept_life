"""Early-lifecycle prediction.

Predict the M5 lifecycle type from features observed in the first three years
after a concept's birth. Features never touch years after the early window;
labels come from the full-trajectory clustering, which is the target, not a
feature.

The evaluation has two settings:

- stratified 5-fold cross-validation, a same-era test
- a temporal split: train on concepts born <= 2012, test on 2013-2018

The temporal split is a stress test. Later cohorts have shorter observation
windows, so their label distribution drifts toward "emerging" and "flash".
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np


FEATURE_NAMES = [
    "log_total_early",
    "early_share_mean",
    "early_share_max",
    "early_growth",
    "early_slope",
    "early_volatility",
    "early_active_ratio",
    "first_share",
    "last_early_share",
    "early_peak_position",
    "early_decline",
]


def build_early_rows(
    series: dict[str, dict[int, int]],
    totals: dict[int, int],
    clusters: list[dict[str, Any]],
    *,
    early_window_years: int = 3,
    min_early_count: int = 5,
    active_min_count: int = 3,
    max_birth_year: int = 2018,
    start_year: int = 1995,
    end_year: int = 2023,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cluster in clusters:
        concept_id = cluster["concept_id"]
        birth = int(cluster["first_year"])
        if birth < start_year or birth > max_birth_year:
            continue
        if birth + early_window_years - 1 > end_year:
            continue
        counts = series.get(concept_id, {})
        years = list(range(birth, birth + early_window_years))
        early_counts = [counts.get(year, 0) for year in years]
        if sum(early_counts) < min_early_count:
            continue
        shares = [
            counts.get(year, 0) / totals.get(year, 1) if totals.get(year, 0) else 0.0
            for year in years
        ]
        mean_share = sum(shares) / len(shares)
        if mean_share <= 0:
            continue

        peak_share = max(shares)
        last_share = shares[-1]
        growth = (last_share - shares[0]) / (shares[0] + 1e-6)
        slope = (last_share - shares[0]) / max(1, len(shares) - 1)
        variance = sum((value - mean_share) ** 2 for value in shares) / len(shares)
        volatility = min(2.0, (variance ** 0.5) / mean_share)
        active_ratio = sum(
            1 for count in early_counts if count >= active_min_count
        ) / len(early_counts)
        peak_position = shares.index(peak_share) / max(1, len(shares) - 1)
        decline = (peak_share - last_share) / peak_share if peak_share > 0 else 0.0

        rows.append(
            {
                "concept_id": concept_id,
                "name": cluster["name"],
                "birth_year": birth,
                "label": cluster["label"],
                "log_total_early": math.log1p(sum(early_counts)),
                "early_share_mean": mean_share,
                "early_share_max": peak_share,
                "early_growth": max(-1.0, min(5.0, growth)),
                "early_slope": slope,
                "early_volatility": volatility,
                "early_active_ratio": active_ratio,
                "first_share": shares[0],
                "last_early_share": last_share,
                "early_peak_position": peak_position,
                "early_decline": min(1.0, max(0.0, decline)),
            }
        )
    return rows


def standardize(
    matrix: np.ndarray, mean: np.ndarray | None = None, std: np.ndarray | None = None
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if mean is None:
        mean = matrix.mean(axis=0)
    if std is None:
        std = matrix.std(axis=0)
        std[std == 0] = 1.0
    return (matrix - mean) / std, mean, std


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)


def train_softmax(
    matrix: np.ndarray,
    labels: np.ndarray,
    n_classes: int,
    *,
    l2: float = 0.01,
    lr: float = 0.1,
    epochs: int = 1500,
) -> tuple[np.ndarray, np.ndarray]:
    n, d = matrix.shape
    weights = np.zeros((d, n_classes))
    bias = np.zeros(n_classes)
    counts = np.bincount(labels, minlength=n_classes).astype(float)
    class_weight = n / (n_classes * np.maximum(counts, 1))
    one_hot = np.eye(n_classes)[labels]
    for _ in range(epochs):
        probabilities = softmax(matrix @ weights + bias)
        error = (probabilities - one_hot) * class_weight
        gradient_w = matrix.T @ error / n + l2 * weights
        gradient_b = error.mean(axis=0)
        weights -= lr * gradient_w
        bias -= lr * gradient_b
    return weights, bias


def predict_proba(
    matrix: np.ndarray, weights: np.ndarray, bias: np.ndarray
) -> np.ndarray:
    return softmax(matrix @ weights + bias)


def accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float((y_true == y_pred).mean())


def macro_f1(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int) -> float:
    scores = []
    for index in range(n_classes):
        true_positive = int(((y_pred == index) & (y_true == index)).sum())
        false_positive = int(((y_pred == index) & (y_true != index)).sum())
        false_negative = int(((y_pred != index) & (y_true == index)).sum())
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        scores.append(
            2 * precision * recall / (precision + recall) if precision + recall else 0.0
        )
    return float(np.mean(scores))


def confusion_matrix(
    y_true: np.ndarray, y_pred: np.ndarray, n_classes: int
) -> list[list[int]]:
    matrix = np.zeros((n_classes, n_classes), dtype=int)
    for true, pred in zip(y_true, y_pred):
        matrix[int(true), int(pred)] += 1
    return matrix.tolist()


def per_class_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, labels: list[str]
) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for index, label in enumerate(labels):
        true_positive = int(((y_pred == index) & (y_true == index)).sum())
        false_positive = int(((y_pred == index) & (y_true != index)).sum())
        false_negative = int(((y_pred != index) & (y_true == index)).sum())
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        result[label] = {
            "support": int((y_true == index).sum()),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }
    return result


def majority_accuracy(y_train: np.ndarray, y_test: np.ndarray) -> float:
    values, counts = np.unique(y_train, return_counts=True)
    majority = int(values[int(np.argmax(counts))])
    return float((y_test == majority).mean())


def stratified_folds(
    labels: np.ndarray, folds: int, seed: int
) -> list[tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(seed)
    buckets: list[list[int]] = [[] for _ in range(folds)]
    for label in np.unique(labels):
        indices = np.where(labels == label)[0].tolist()
        rng.shuffle(indices)
        for position, index in enumerate(indices):
            buckets[position % folds].append(index)
    all_indices = set(range(len(labels)))
    result = []
    for test_indices in buckets:
        test = np.array(sorted(test_indices))
        train = np.array(sorted(all_indices - set(test_indices)))
        result.append((train, test))
    return result
