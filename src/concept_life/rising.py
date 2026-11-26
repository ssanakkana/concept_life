"""Rising-concept scores based on share of papers, not raw counts."""
from __future__ import annotations

from typing import Iterable


def window_count(series: dict[int, int], years: Iterable[int]) -> int:
    return sum(series.get(year, 0) for year in years)


def window_share(
    series: dict[int, int], years: Iterable[int], total: dict[int, int]
) -> float:
    """Share of the window's papers that mention the concept."""
    numerator = window_count(series, years)
    denominator = sum(total.get(year, 0) for year in years)
    return numerator / denominator if denominator else 0.0


def rising_table(
    series_by_id: dict[str, dict[int, int]],
    names: dict[str, str],
    total: dict[int, int],
    prev_years: Iterable[int],
    curr_years: Iterable[int],
    *,
    min_curr_count: int = 5,
    top_k: int | None = 30,
) -> list[dict]:
    """Rank concepts by the change in share between two windows.

    ``delta_share`` is the primary key because it is robust when a concept had
    zero mentions in the previous window. ``growth`` is reported alongside for
    relative comparison. Concepts below ``min_curr_count`` are dropped to keep
    one-off mentions out of the ranking.
    """
    prev_years = list(prev_years)
    curr_years = list(curr_years)
    rows: list[dict] = []

    for concept_id, series in series_by_id.items():
        prev_count = window_count(series, prev_years)
        curr_count = window_count(series, curr_years)
        if curr_count < min_curr_count:
            continue

        prev_share = window_share(series, prev_years, total)
        curr_share = window_share(series, curr_years, total)
        is_new = prev_count == 0
        growth = None if is_new else curr_share / max(prev_share, 1e-12)

        rows.append(
            {
                "concept_id": concept_id,
                "name": names.get(concept_id, concept_id),
                "prev_count": prev_count,
                "curr_count": curr_count,
                "prev_share": prev_share,
                "curr_share": curr_share,
                "delta_share": curr_share - prev_share,
                "growth": growth,
                "is_new": is_new,
            }
        )

    def growth_key(row: dict) -> float:
        # A brand-new concept has no meaningful ratio; treat it as the largest
        # growth for tie-breaking, but delta_share remains the primary key.
        return float("inf") if row["growth"] is None else row["growth"]

    rows.sort(key=lambda row: (-row["delta_share"], -growth_key(row), row["name"]))
    return rows[:top_k] if top_k is not None else rows
