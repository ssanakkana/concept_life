"""Build per-concept yearly series.

All downstream frequency reasoning should use shares (concept papers divided
by total papers in the same year), not raw counts. The corpus grows over time,
so raw counts would mistake corpus growth for concept growth.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterable

from .schema import Paper


def build_series(
    papers: Iterable[Paper],
) -> tuple[dict[str, dict[int, int]], dict[str, str], dict[int, int]]:
    """Return (concept_id -> {year: count}, concept_id -> display name, year -> paper count).

    The display name is the most frequent name observed for that id. Names can
    change over time, so they are labels only; ids are the keys.
    """
    counts: dict[str, Counter[int]] = defaultdict(Counter)
    name_counts: dict[str, Counter[str]] = defaultdict(Counter)
    total: Counter[int] = Counter()

    for paper in papers:
        total[paper.year] += 1
        for concept in paper.concepts:
            counts[concept.id][paper.year] += 1
            name_counts[concept.id][concept.name] += 1

    names = {
        concept_id: counter.most_common(1)[0][0]
        for concept_id, counter in name_counts.items()
    }
    return {key: dict(value) for key, value in counts.items()}, names, dict(total)
