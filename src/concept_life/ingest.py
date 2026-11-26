"""Load cached Acemap responses into the ``Paper`` contract."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .schema import Paper, parse_work


def load_cache(
    cache_dir: str | Path,
    *,
    top_k: int = 10,
    min_level: int | None = 2,
    min_score: float | None = 0.0,
) -> list[Paper]:
    """Read every ``*.json`` response in ``cache_dir`` and deduplicate by id.

    The first occurrence of a paper wins. The pilot cache is small enough for
    a dictionary; a full crawl may need a streaming or on-disk dedup step.
    """
    cache_dir = Path(cache_dir)
    by_id: dict[str, Paper] = {}

    for path in sorted(cache_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for work in data.get("results") or []:
            paper = parse_work(
                work, top_k=top_k, min_level=min_level, min_score=min_score
            )
            if paper is not None and paper.id not in by_id:
                by_id[paper.id] = paper

    return list(by_id.values())


def write_jsonl(papers: Iterable[Paper], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for paper in papers:
            handle.write(json.dumps(paper.to_dict(), ensure_ascii=False) + "\n")
