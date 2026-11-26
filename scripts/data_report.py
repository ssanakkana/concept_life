#!/usr/bin/env python3
"""M1 data quality report from papers.jsonl.

Outputs year histogram, field counts, concept level counts and a summary.
Uses only the standard library.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from concept_life.config import load_config  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--papers", type=Path, default=ROOT / "data" / "processed" / "papers.jsonl"
    )
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "m1.json")
    parser.add_argument("--out", type=Path, default=ROOT / "runs" / "m1" / "report")
    args = parser.parse_args()

    config = load_config(args.config)
    papers: list[dict] = []
    with args.papers.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                papers.append(json.loads(line))
    if not papers:
        raise SystemExit(f"no papers in {args.papers}")

    year_counts: Counter = Counter()
    field_counts: Counter = Counter()
    level_counts: Counter = Counter()
    concepts_per_paper: Counter = Counter()
    concept_ids: set[str] = set()
    concept_instances = 0
    missing_doi = 0
    missing_fields = 0

    for paper in papers:
        year_counts[paper.get("year")] += 1
        concepts = paper.get("concepts") or []
        concepts_per_paper[len(concepts)] += 1
        concept_instances += len(concepts)
        for concept in concepts:
            concept_ids.add(concept["id"])
            level_counts[concept.get("level")] += 1
        fields = paper.get("fields") or []
        if not fields:
            missing_fields += 1
        for field in fields:
            field_counts[field] += 1
        if not paper.get("doi"):
            missing_doi += 1

    years = sorted(year for year in year_counts if isinstance(year, int))
    args.out.mkdir(parents=True, exist_ok=True)

    with (args.out / "year_histogram.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(["year", "papers"])
        for year in range(years[0], years[-1] + 1):
            writer.writerow([year, year_counts.get(year, 0)])

    with (args.out / "field_counts.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(["field", "papers"])
        for field, count in field_counts.most_common():
            writer.writerow([field, count])

    with (args.out / "level_counts.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(["level", "concept_instances"])
        for level in sorted(level_counts, key=lambda value: (value is None, value)):
            writer.writerow([level, level_counts[level]])

    max_count = max((year_counts.get(year, 0) for year in years), default=0)
    lines = []
    for year in range(years[0], years[-1] + 1):
        count = year_counts.get(year, 0)
        bar = "#" * round(60 * count / max_count) if max_count else ""
        lines.append(f"{year} {count:>6} {bar}")
    (args.out / "year_histogram.txt").write_text("\n".join(lines), encoding="utf-8")

    summary = {
        "papers": len(papers),
        "years": {"min": years[0], "max": years[-1]},
        "concepts_unique": len(concept_ids),
        "concept_instances": concept_instances,
        "avg_concepts_per_paper": round(concept_instances / len(papers), 2),
        "missing_doi": missing_doi,
        "missing_fields": missing_fields,
        "top_fields": field_counts.most_common(20),
        "papers_by_window": {
            "prev": {
                str(year): year_counts.get(year, 0)
                for year in config["windows"]["prev"]
            },
            "curr": {
                str(year): year_counts.get(year, 0)
                for year in config["windows"]["curr"]
            },
        },
    }
    (args.out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
