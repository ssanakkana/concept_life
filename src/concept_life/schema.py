"""Data contracts for papers and concepts.

The rest of the pipeline only sees ``Paper`` objects. Raw Acemap records are
parsed once, here, so that later stages do not depend on the API schema.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Concept:
    id: str
    name: str
    level: int | None
    score: float | None
    # Cross-source alignment key. Acemap and OpenAlex concepts both expose a
    # Wikidata URL for many concepts; it is the best merge key when present.
    wikidata: str | None = None


@dataclass(frozen=True)
class Paper:
    id: str
    title: str
    year: int
    doi: str | None
    cited_by_count: int | None
    concepts: tuple[Concept, ...]
    fields: tuple[str, ...] = ()
    source: str = "acemap"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["concepts"] = [asdict(concept) for concept in self.concepts]
        data["fields"] = list(self.fields)
        return data


def parse_work(
    work: dict[str, Any],
    *,
    top_k: int = 10,
    min_level: int | None = 2,
    min_score: float | None = 0.0,
) -> Paper | None:
    """Parse one Acemap work record.

    Returns ``None`` when the record has no id, no usable year, or no concept
    that passes the level/score filters. Concepts are deduplicated by id and
    kept in the order returned by the API, which is roughly by score.
    """
    work_id = work.get("id")
    year = work.get("publication_year")
    if not work_id or not isinstance(year, int):
        return None

    seen: set[str] = set()
    concepts: list[Concept] = []

    for raw in work.get("concepts") or []:
        concept_id = raw.get("id")
        name = raw.get("display_name")
        if not concept_id or not name or concept_id in seen:
            continue

        level = raw.get("level")
        if min_level is not None:
            if not isinstance(level, int) or level < min_level:
                continue

        score = raw.get("score")
        if min_score is not None and min_score > 0:
            if not isinstance(score, (int, float)) or score < min_score:
                continue

        seen.add(concept_id)
        wikidata = raw.get("wikidata")
        concepts.append(
            Concept(
                id=str(concept_id),
                name=str(name),
                level=level if isinstance(level, int) else None,
                score=float(score) if isinstance(score, (int, float)) else None,
                wikidata=str(wikidata) if wikidata else None,
            )
        )
        if len(concepts) >= top_k:
            break

    if not concepts:
        return None

    # Topic taxonomy is used only for domain filtering. Domain, field and
    # subfield are all kept because Acemap populates them inconsistently.
    fields: set[str] = set()
    for topic in work.get("topics") or []:
        for key in ("domain", "field", "subfield"):
            name = (topic.get(key) or {}).get("display_name")
            if name:
                fields.add(str(name))

    return Paper(
        id=str(work_id),
        title=str(work.get("title") or work.get("display_name") or ""),
        year=year,
        doi=work.get("doi"),
        cited_by_count=work.get("cited_by_count"),
        concepts=tuple(concepts),
        fields=tuple(sorted(fields)),
        source="acemap",
    )
