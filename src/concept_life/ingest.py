"""Load cached Acemap responses into the ``Paper`` contract."""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Iterable

from .schema import Paper, parse_work


def matches_domain(paper: Paper, domain: str | None, keep_unknown: bool = True) -> bool:
    """Return True when the paper belongs to the requested domain.

    A paper whose topic taxonomy is empty is treated as unknown. Keeping
    unknown papers is the safer default for a first crawl; record the count in
    the data report before deciding to drop them.
    """
    if not domain:
        return True
    if not paper.fields:
        return keep_unknown
    needle = domain.lower()
    return any(needle in field.lower() for field in paper.fields)


def load_cache(
    cache_dir: str | Path,
    *,
    top_k: int = 10,
    min_level: int | None = 2,
    min_score: float | None = 0.0,
    domain: str | None = None,
    keep_unknown_domain: bool = True,
    stoplist: set[str] | None = None,
) -> list[Paper]:
    """Read every ``*.json`` response in ``cache_dir`` and deduplicate by id.

    The first occurrence of a paper wins. The pilot cache is small enough for
    a dictionary; a full crawl may need a streaming or on-disk dedup step.

    ``stoplist`` removes concept names that are known to be ambiguous or
    cross-domain. It is a data-cleaning band-aid, not a domain classifier.
    """
    cache_dir = Path(cache_dir)
    by_id: dict[str, Paper] = {}
    stop = {name.lower() for name in stoplist} if stoplist else set()

    for path in sorted(cache_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for work in data.get("results") or []:
            paper = parse_work(
                work, top_k=top_k, min_level=min_level, min_score=min_score
            )
            if paper is None or paper.id in by_id:
                continue
            if not matches_domain(paper, domain, keep_unknown_domain):
                continue
            if stop:
                kept = tuple(
                    concept
                    for concept in paper.concepts
                    if concept.name.lower() not in stop
                )
                if not kept:
                    continue
                if len(kept) != len(paper.concepts):
                    paper = replace(paper, concepts=kept)
            by_id[paper.id] = paper

    return list(by_id.values())


def write_jsonl(papers: Iterable[Paper], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for paper in papers:
            handle.write(json.dumps(paper.to_dict(), ensure_ascii=False) + "\n")
