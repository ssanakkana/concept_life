"""Lifecycle clustering: group concepts by the shape of their share series.

The clustering uses shape features only, not total paper count or absolute
year, so the clusters describe *how* a concept lives rather than *how big* or
*how old* it is. K-means is implemented with numpy to keep the dependency
surface small; k is chosen by silhouette.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np


FEATURE_NAMES = [
    "span",
    "active_ratio",
    "peak_position",
    "peak_share",
    "decline_speed",
    "recent_to_peak",
    "volatility",
    "years_since_peak",
    "burst_flag",
    "decline_flag",
    "revival_flag",
]


def _share(counts: dict[int, int], totals: dict[int, int], year: int) -> float:
    denominator = totals.get(year, 0)
    return counts.get(year, 0) / denominator if denominator else 0.0


def build_feature_rows(
    series: dict[str, dict[int, int]],
    names: dict[str, str],
    totals: dict[int, int],
    events: list[dict[str, Any]],
    *,
    start_year: int,
    end_year: int,
    min_total_count: int,
    active_min_count: int,
    min_year_total: int,
) -> list[dict[str, Any]]:
    declined = {event["concept_id"] for event in events if event["type"] == "decline"}
    revived = {event["concept_id"] for event in events if event["type"] == "revival"}
    bursted = {event["concept_id"] for event in events if event["type"] == "burst"}

    rows: list[dict[str, Any]] = []
    for concept_id, counts in series.items():
        # Match M2: total is counted inside the analysis range, not all years.
        total = sum(
            counts.get(year, 0) for year in range(start_year, end_year + 1)
        )
        if total < min_total_count:
            continue
        shares = {
            year: _share(counts, totals, year)
            for year in range(start_year, end_year + 1)
        }
        active = [
            year for year in range(start_year, end_year + 1)
            if counts.get(year, 0) >= active_min_count
        ]
        if not active:
            continue
        first_year = active[0]
        last_active = active[-1]
        span = last_active - first_year + 1

        valid_years = [
            year for year in range(first_year, end_year + 1)
            if totals.get(year, 0) >= min_year_total
        ]
        if not valid_years:
            valid_years = list(range(first_year, end_year + 1))
        peak_year = max(valid_years, key=lambda year: shares[year])
        peak_share = shares[peak_year]
        if peak_share <= 0:
            continue

        last_share = shares[end_year]
        recent_share = sum(shares[year] for year in range(end_year - 2, end_year + 1)) / 3
        peak_position = (peak_year - first_year) / max(1, last_active - first_year)
        decline_speed = min(
            1.0, max(0.0, (peak_share - last_share) / peak_share)
        )
        recent_to_peak = min(2.0, max(0.0, recent_share / peak_share))
        active_shares = [shares[year] for year in active]
        mean_active = sum(active_shares) / len(active_shares)
        variance = sum((value - mean_active) ** 2 for value in active_shares) / len(
            active_shares
        )
        volatility = min(
            2.0, (variance ** 0.5) / mean_active if mean_active > 0 else 0.0
        )

        rows.append(
            {
                "concept_id": concept_id,
                "name": names.get(concept_id, concept_id),
                "total_count": total,
                "first_year": first_year,
                "last_active": last_active,
                "peak_year": peak_year,
                "span": span,
                "active_ratio": len(active) / span,
                "peak_position": round(peak_position, 6),
                "peak_share": round(peak_share, 8),
                "decline_speed": round(decline_speed, 6),
                "recent_to_peak": round(recent_to_peak, 6),
                "volatility": round(volatility, 6),
                "years_since_peak": end_year - peak_year,
                "burst_flag": 1 if concept_id in bursted else 0,
                "decline_flag": 1 if concept_id in declined else 0,
                "revival_flag": 1 if concept_id in revived else 0,
            }
        )
    return rows


def standardize(matrix: np.ndarray) -> np.ndarray:
    mean = matrix.mean(axis=0)
    std = matrix.std(axis=0)
    std[std == 0] = 1.0
    return (matrix - mean) / std


def kmeans(
    matrix: np.ndarray,
    k: int,
    *,
    seed: int = 42,
    n_init: int = 10,
    max_iter: int = 100,
) -> tuple[np.ndarray, np.ndarray, float]:
    rng = np.random.default_rng(seed)
    n = len(matrix)
    best_labels = np.zeros(n, dtype=int)
    best_centers = matrix[:k].copy()
    best_inertia = math.inf

    for _ in range(n_init):
        centers = matrix[rng.choice(n, k, replace=False)].copy()
        labels = np.full(n, -1, dtype=int)
        for _ in range(max_iter):
            distances = ((matrix[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
            new_labels = distances.argmin(axis=1)
            new_centers = centers.copy()
            for index in range(k):
                members = matrix[new_labels == index]
                if len(members):
                    new_centers[index] = members.mean(axis=0)
            if np.array_equal(new_labels, labels) and np.allclose(
                new_centers, centers
            ):
                labels = new_labels
                centers = new_centers
                break
            labels = new_labels
            centers = new_centers
        inertia = float(((matrix - centers[labels]) ** 2).sum())
        if inertia < best_inertia:
            best_inertia = inertia
            best_labels = labels.copy()
            best_centers = centers.copy()
    return best_labels, best_centers, best_inertia


def silhouette_from_distance(distance: np.ndarray, labels: np.ndarray) -> float:
    unique = np.unique(labels)
    if len(unique) < 2:
        return 0.0
    scores: list[float] = []
    for index in range(len(labels)):
        same = labels == labels[index]
        same[index] = False
        if not same.any():
            scores.append(0.0)
            continue
        a = float(distance[index, same].mean())
        b = min(
            float(distance[index, labels == cluster].mean())
            for cluster in unique
            if cluster != labels[index]
        )
        denominator = max(a, b)
        scores.append((b - a) / denominator if denominator > 0 else 0.0)
    return float(np.mean(scores))


def choose_k(
    matrix: np.ndarray,
    k_values: list[int],
    *,
    seed: int,
    n_init: int,
    max_iter: int,
) -> tuple[int, np.ndarray, np.ndarray, dict[int, dict[str, Any]]]:
    distance = np.sqrt(
        ((matrix[:, None, :] - matrix[None, :, :]) ** 2).sum(axis=2)
    )
    results: dict[int, dict[str, Any]] = {}
    best_k = k_values[0]
    best_score = -1.0
    best_labels = np.zeros(len(matrix), dtype=int)
    best_centers = matrix[: best_k].copy()

    for k in k_values:
        labels, centers, inertia = kmeans(
            matrix, k, seed=seed, n_init=n_init, max_iter=max_iter
        )
        score = silhouette_from_distance(distance, labels)
        results[k] = {
            "silhouette": round(score, 4),
            "inertia": round(inertia, 4),
            "labels": labels,
            "centers": centers,
        }
        if score > best_score:
            best_score = score
            best_k = k
            best_labels = labels
            best_centers = centers
    return best_k, best_labels, best_centers, results


def label_clusters(
    rows: list[dict[str, Any]], labels: np.ndarray, k: int
) -> tuple[dict[int, str], dict[int, dict[str, float]]]:
    centroids: dict[int, dict[str, float]] = {}
    for index in range(k):
        members = [
            row for row, label in zip(rows, labels) if int(label) == index
        ]
        centroids[index] = {
            name: float(np.mean([member[name] for member in members]))
            for name in FEATURE_NAMES
        }

    rules = [
        ("复活型", lambda c: c["revival_flag"] > 0.35),
        ("昙花一现", lambda c: c["span"] < 12 and c["decline_speed"] > 0.5),
        ("新兴型", lambda c: c["years_since_peak"] < 6 and c["recent_to_peak"] > 0.65),
        ("爆发后衰退", lambda c: c["burst_flag"] > 0.7 and c["decline_flag"] > 0.5),
        ("衰退型", lambda c: c["decline_speed"] > 0.5),
        ("慢热型", lambda c: c["peak_position"] > 0.55),
    ]
    sizes = {
        index: sum(1 for label in labels if int(label) == index)
        for index in range(k)
    }
    ordered = sorted(range(k), key=lambda index: -sizes[index])
    names: dict[int, str] = {}
    used: set[str] = set()
    for index in ordered:
        assigned = None
        for name, rule in rules:
            if name in used:
                continue
            if rule(centroids[index]):
                assigned = name
                break
        if assigned is None:
            assigned = f"其他-{index}"
        used.add(assigned)
        names[index] = assigned
    return names, centroids
