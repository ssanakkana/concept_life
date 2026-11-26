"""Candidate replacement detection.

A candidate replacement is a pair (old, new) where:

- ``old`` has a detected decline and is below its peak at the end of the range
- ``new`` is rising, with a burst or strong late-window growth
- the two concepts co-occur enough to be in the same neighbourhood
- their share series are negatively correlated after the old concept's peak

The output is a *candidate* pair, not a causal claim. A human review column is
written alongside so precision@10 can be filled in later.
"""
from __future__ import annotations

import itertools
import math
from collections import defaultdict
from typing import Any, Iterable


def build_cooccurrence(
    papers: Iterable[dict[str, Any]],
    candidate_ids: set[str],
    min_support: int = 3,
) -> dict[tuple[str, str], int]:
    """Count concept pairs that co-occur in at least ``min_support`` papers."""
    support: dict[tuple[str, str], int] = {}
    for paper in papers:
        ids = sorted(
            {
                concept["id"]
                for concept in paper.get("concepts") or []
                if concept.get("id") in candidate_ids
            }
        )
        for left, right in itertools.combinations(ids, 2):
            key = (left, right)
            support[key] = support.get(key, 0) + 1
    return {key: value for key, value in support.items() if value >= min_support}


def pearson(left: list[float], right: list[float]) -> float:
    if len(left) < 3 or len(left) != len(right):
        return 0.0
    n = len(left)
    mean_left = sum(left) / n
    mean_right = sum(right) / n
    var_left = sum((value - mean_left) ** 2 for value in left)
    var_right = sum((value - mean_right) ** 2 for value in right)
    if var_left <= 0 or var_right <= 0:
        return 0.0
    covariance = sum(
        (a - mean_left) * (b - mean_right) for a, b in zip(left, right)
    )
    return covariance / math.sqrt(var_left * var_right)


def jaccard(support: int, count_left: int, count_right: int) -> float:
    union = count_left + count_right - support
    return support / union if union > 0 else 0.0


def detect_replacements(
    series: dict[str, dict[int, int]],
    totals: dict[int, int],
    support: dict[tuple[str, str], int],
    decline_ids: set[str],
    peak_years: dict[str, int],
    rising_ids: set[str],
    new_years: dict[str, int],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    start_year = int(config["start_year"])
    end_year = int(config["end_year"])
    counts = {concept_id: sum(years.values()) for concept_id, years in series.items()}

    neighbours: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for (left, right), value in support.items():
        neighbours[left].append((right, value))
        neighbours[right].append((left, value))

    results: list[dict[str, Any]] = []
    for old_id in decline_ids:
        old_peak = peak_years.get(old_id)
        if old_peak is None or old_peak >= end_year:
            continue
        old_series = series.get(old_id, {})
        old_shares = {
            year: old_series.get(year, 0) / totals.get(year, 1)
            for year in range(start_year, end_year + 1)
        }
        peak_share = old_shares.get(old_peak, 0.0)
        last_share = old_shares.get(end_year, 0.0)
        max_last_ratio = float(config.get("max_old_last_ratio", 1.0))
        if peak_share <= 0 or last_share >= max_last_ratio * peak_share:
            continue

        local: list[dict[str, Any]] = []
        for new_id, pair_support in sorted(
            neighbours.get(old_id, []), key=lambda item: -item[1]
        )[: int(config["neighbor_top_k"])]:
            if new_id == old_id or new_id not in rising_ids:
                continue
            new_year = new_years.get(new_id)
            if new_year is None or new_year < old_peak - 2:
                continue
            similarity = jaccard(
                pair_support, counts.get(old_id, 0), counts.get(new_id, 0)
            )
            if similarity < float(config["min_jaccard"]):
                continue

            new_series = series.get(new_id, {})
            years = list(range(old_peak, end_year + 1))
            left = [old_shares.get(year, 0.0) for year in years]
            right = [
                new_series.get(year, 0) / totals.get(year, 1) for year in years
            ]
            active_years = sum(1 for a, b in zip(left, right) if a > 0 or b > 0)
            if active_years < int(config["min_overlap_years"]):
                continue
            correlation = pearson(left, right)
            if correlation >= 0:
                continue

            new_last_share = new_series.get(end_year, 0) / totals.get(end_year, 1)
            if bool(config.get("require_overtake", True)) and new_last_share <= last_share:
                continue
            overtake = new_last_share / (new_last_share + last_share + 1e-12)

            score = (-correlation) * similarity * overtake * (
                1.0 if new_year >= old_peak else 0.5
            )
            local.append(
                {
                    "old_id": old_id,
                    "new_id": new_id,
                    "old_peak_year": old_peak,
                    "new_year": new_year,
                    "support": pair_support,
                    "jaccard": round(similarity, 6),
                    "correlation": round(correlation, 6),
                    "score": round(score, 6),
                    "old_peak_share": round(peak_share, 8),
                    "old_last_share": round(last_share, 8),
                    "new_last_share": round(new_last_share, 8),
                    "overtake": round(overtake, 6),
                }
            )

        local.sort(key=lambda row: -row["score"])
        results.extend(local[: int(config["top_k_per_old"])])

    results.sort(key=lambda row: -row["score"])
    return results[: int(config["max_candidates"])]
