"""Temporal trend prediction: which concepts will rise in the next two years.

The task is retrospective: given features at year T, rank concepts by future
share growth in T+1..T+horizon. The evaluation is leave-one-window-out across
2016, 2018 and 2020, so a model trained on two windows is tested on the third.
Baselines are historical frequency, historical growth and random.

The model is a small L2 logistic regression implemented with numpy. It is
deliberately simple: the point is a clean temporal split and a fair baseline
comparison, not a leaderboard score.
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import numpy as np


FEATURE_NAMES = [
    "share_T",
    "share_mean_3",
    "growth_1",
    "growth_3",
    "burst_z",
    "log_degree",
    "neighbor_growth",
    "age",
    "log_total",
]


def share_at(
    series: dict[int, int], totals: dict[int, int], year: int
) -> float:
    denominator = totals.get(year, 0)
    return series.get(year, 0) / denominator if denominator else 0.0


def mean_share(
    series: dict[int, int], totals: dict[int, int], years: range | list[int]
) -> float:
    years = list(years)
    return sum(share_at(series, totals, year) for year in years) / len(years)


def build_degree(support: dict[tuple[str, str], int]) -> dict[str, int]:
    degree: dict[str, int] = defaultdict(int)
    for left, right in support:
        degree[left] += 1
        degree[right] += 1
    return dict(degree)


def build_neighbours(
    support: dict[tuple[str, str], int], top_k: int = 5
) -> dict[str, list[tuple[str, int]]]:
    neighbours: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for (left, right), value in support.items():
        neighbours[left].append((right, value))
        neighbours[right].append((left, value))
    for concept_id in neighbours:
        neighbours[concept_id].sort(key=lambda item: -item[1])
        neighbours[concept_id] = neighbours[concept_id][:top_k]
    return dict(neighbours)


def build_features(
    series: dict[str, dict[int, int]],
    totals: dict[int, int],
    degree: dict[str, int],
    neighbours: dict[str, list[tuple[str, int]]],
    year: int,
    config: dict[str, Any],
) -> tuple[list[str], np.ndarray]:
    start_year = int(config["start_year"])
    min_total = int(config["min_total_count_T"])
    min_share = float(config.get("min_share_T", 0.0))
    ids: list[str] = []
    rows: list[list[float]] = []

    for concept_id, counts in series.items():
        share_t = share_at(counts, totals, year)
        if share_t <= 0 or share_t < min_share:
            continue
        total_t = sum(counts.get(value, 0) for value in range(start_year, year + 1))
        if total_t < min_total:
            continue

        share_prev = share_at(counts, totals, year - 1)
        share_prev3 = share_at(counts, totals, year - 3)
        mean3 = mean_share(counts, totals, range(year - 2, year + 1))
        growth1 = share_t - share_prev
        growth3 = (share_t - share_prev3) / (share_prev3 + 1e-9)
        growth3 = max(min(growth3, 10.0), -10.0)

        previous = [share_at(counts, totals, value) for value in range(year - 3, year)]
        mean = sum(previous) / len(previous)
        variance = sum((value - mean) ** 2 for value in previous) / len(previous)
        std = variance ** 0.5
        burst_z = (share_t - mean) / (std + 1e-9)
        burst_z = max(min(burst_z, 10.0), -10.0)

        log_degree = math.log1p(degree.get(concept_id, 0))
        neighbour_growth = []
        for neighbour, _ in neighbours.get(concept_id, []):
            neighbour_counts = series.get(neighbour, {})
            neighbour_growth.append(
                share_at(neighbour_counts, totals, year)
                - share_at(neighbour_counts, totals, year - 1)
            )
        neighbour_growth_value = (
            sum(neighbour_growth) / len(neighbour_growth)
            if neighbour_growth
            else 0.0
        )

        first_year = min(
            (value for value, count in counts.items() if count > 0), default=year
        )
        age = min(max(0, year - first_year), 30)
        log_total = math.log1p(total_t)

        ids.append(concept_id)
        rows.append(
            [
                share_t,
                mean3,
                growth1,
                growth3,
                burst_z,
                log_degree,
                neighbour_growth_value,
                age,
                log_total,
            ]
        )

    return ids, np.asarray(rows, dtype=float)


def future_growth(
    series: dict[str, dict[int, int]],
    totals: dict[int, int],
    ids: list[str],
    year: int,
    horizon: int,
    *,
    mode: str = "absolute",
    min_future_share: float = 0.0,
) -> dict[str, float]:
    """Future growth label per concept.

    ``absolute`` is share(T+1..T+h) - share(T). ``relative`` divides by the
    current share, which is closer to "new focus" but noisy for tiny concepts;
    ``min_future_share`` drops concepts that never reach a meaningful share.
    Concepts below the threshold get -1.0 and never enter the top-k labels.
    """
    growth: dict[str, float] = {}
    for concept_id in ids:
        counts = series[concept_id]
        current = share_at(counts, totals, year)
        future = mean_share(counts, totals, range(year + 1, year + horizon + 1))
        if future < min_future_share:
            growth[concept_id] = -1.0
        elif mode == "relative":
            growth[concept_id] = (future - current) / (current + 1e-4)
        else:
            growth[concept_id] = future - current
    return growth


def top_k_labels(growth: dict[str, float], k: int) -> set[str]:
    ordered = sorted(growth.items(), key=lambda item: (-item[1], item[0]))
    return {concept_id for concept_id, _ in ordered[:k]}


def standardize(matrix: np.ndarray) -> np.ndarray:
    mean = matrix.mean(axis=0)
    std = matrix.std(axis=0)
    std[std == 0] = 1.0
    return (matrix - mean) / std


def train_logistic(
    matrix: np.ndarray,
    labels: np.ndarray,
    *,
    l2: float = 0.01,
    lr: float = 0.05,
    epochs: int = 1200,
) -> tuple[np.ndarray, float]:
    n, d = matrix.shape
    weights = np.zeros(d)
    bias = 0.0
    positives = float(labels.sum())
    negatives = float(n - positives)
    pos_weight = min(negatives / max(positives, 1.0), 10.0)
    sample_weight = np.where(labels == 1, pos_weight, 1.0)

    for _ in range(epochs):
        logits = matrix @ weights + bias
        probabilities = 1.0 / (1.0 + np.exp(-np.clip(logits, -50, 50)))
        error = sample_weight * (probabilities - labels)
        gradient_w = matrix.T @ error / n + l2 * weights
        gradient_b = error.mean()
        weights -= lr * gradient_w
        bias -= lr * gradient_b
        if np.max(np.abs(gradient_w)) < 1e-7:
            break
    return weights, bias


def score(matrix: np.ndarray, weights: np.ndarray, bias: float) -> np.ndarray:
    logits = matrix @ weights + bias
    return 1.0 / (1.0 + np.exp(-np.clip(logits, -50, 50)))


def precision_at_k(scores: np.ndarray, labels: np.ndarray, k: int) -> float:
    order = np.argsort(-scores)[:k]
    return float(labels[order].sum() / k)


def ndcg_at_k(scores: np.ndarray, labels: np.ndarray, k: int) -> float:
    order = np.argsort(-scores)[:k]
    gains = labels[order]
    discounts = 1.0 / np.log2(np.arange(2, k + 2))
    dcg = float((gains * discounts).sum())
    ideal = np.sort(labels)[::-1][:k]
    idcg = float((ideal * discounts[: len(ideal)]).sum())
    return dcg / idcg if idcg > 0 else 0.0


def evaluate_windows(
    series: dict[str, dict[int, int]],
    totals: dict[int, int],
    graphs: dict[int, tuple[dict[str, int], dict[str, list[tuple[str, int]]]]],
    config: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    windows = [int(value) for value in config["windows"]]
    horizon = int(config["horizon_years"])
    top_k = int(config["top_k"])
    eval_ks = [int(value) for value in config["eval_k"]]
    max_k = max(eval_ks)

    prepared: dict[int, dict[str, Any]] = {}
    label_mode = str(config.get("label_mode", "absolute"))
    min_future_share = float(config.get("min_future_share", 0.0))
    for year in windows:
        degree, neighbours = graphs[year]
        ids, matrix = build_features(series, totals, degree, neighbours, year, config)
        growth = future_growth(
            series,
            totals,
            ids,
            year,
            horizon,
            mode=label_mode,
            min_future_share=min_future_share,
        )
        labels = top_k_labels(growth, top_k)
        prepared[year] = {
            "ids": ids,
            "X": matrix,
            "growth": growth,
            "labels": labels,
            "y": np.array([1.0 if concept_id in labels else 0.0 for concept_id in ids]),
        }

    per_window: dict[str, Any] = {}
    predictions: list[dict[str, Any]] = []
    latest = max(windows)

    for year in windows:
        train_matrices = []
        train_labels = []
        for other in windows:
            if other == year:
                continue
            train_matrices.append(standardize(prepared[other]["X"]))
            train_labels.append(prepared[other]["y"])
        train_matrix = np.vstack(train_matrices)
        train_y = np.concatenate(train_labels)

        weights, bias = train_logistic(
            train_matrix,
            train_y,
            l2=float(config["l2"]),
            lr=float(config["lr"]),
            epochs=int(config["epochs"]),
        )

        test_matrix = standardize(prepared[year]["X"])
        model_scores = score(test_matrix, weights, bias)
        test_y = prepared[year]["y"]

        baselines = {
            "frequency": prepared[year]["X"][:, 1],
            "growth": prepared[year]["X"][:, 3],
            "random": np.random.default_rng(42 + year).random(len(test_y)),
        }

        row: dict[str, Any] = {
            "candidates": len(test_y),
            "positives": int(test_y.sum()),
        }
        for name, scores in {"model": model_scores, **baselines}.items():
            row[name] = {
                f"precision@{k}": round(precision_at_k(scores, test_y, k), 4)
                for k in eval_ks
            }
            row[name][f"ndcg@{max_k}"] = round(ndcg_at_k(scores, test_y, max_k), 4)
        per_window[str(year)] = row

        if year == latest:
            order = np.argsort(-model_scores)
            for rank, index in enumerate(order[:top_k], 1):
                concept_id = prepared[year]["ids"][index]
                predictions.append(
                    {
                        "rank": rank,
                        "concept_id": concept_id,
                        "score": round(float(model_scores[index]), 6),
                        "actual_future_growth": round(
                            float(prepared[year]["growth"][concept_id]), 8
                        ),
                        "in_top_k": concept_id in prepared[year]["labels"],
                    }
                )

    names = ["model", "frequency", "growth", "random"]
    metric_names = [f"precision@{k}" for k in eval_ks] + [f"ndcg@{max_k}"]
    mean: dict[str, Any] = {}
    for name in names:
        mean[name] = {
            metric: round(
                sum(per_window[str(year)][name][metric] for year in windows)
                / len(windows),
                4,
            )
            for metric in metric_names
        }

    return {"per_window": per_window, "mean": mean, "windows": windows}, predictions
