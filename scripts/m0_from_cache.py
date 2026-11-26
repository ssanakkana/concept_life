#!/usr/bin/env python3
"""M0: build a paper table and concept timelines from the pilot cache.

This is the smallest end-to-end slice: no network, no third-party packages.
It reads Acemap responses cached by the pilot project, deduplicates papers,
filters concepts by level, and writes:

  data/processed/papers.jsonl
  data/processed/concept_series.csv
  data/processed/top_rising.csv
  runs/m0/config.json
  runs/m0/summary.json
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
from concept_life.ingest import load_cache, write_jsonl  # noqa: E402
from concept_life.rising import rising_table  # noqa: E402
from concept_life.series import build_series  # noqa: E402


def write_series_csv(
    path: Path,
    series_by_id: dict[str, dict[int, int]],
    names: dict[str, str],
    total: dict[int, int],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["concept_id", "name", "year", "count", "share"])
        for concept_id in sorted(series_by_id):
            series = series_by_id[concept_id]
            for year in sorted(series):
                count = series[year]
                share = count / total[year] if total.get(year) else 0.0
                writer.writerow(
                    [concept_id, names[concept_id], year, count, f"{share:.8f}"]
                )


def write_rising_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "rank",
        "concept_id",
        "name",
        "prev_count",
        "curr_count",
        "prev_share",
        "curr_share",
        "delta_share",
        "growth",
        "is_new",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for rank, row in enumerate(rows, 1):
            out = dict(row)
            out["rank"] = rank
            out["prev_share"] = f"{row['prev_share']:.8f}"
            out["curr_share"] = f"{row['curr_share']:.8f}"
            out["delta_share"] = f"{row['delta_share']:.8f}"
            out["growth"] = "new" if row["growth"] is None else f"{row['growth']:.4f}"
            out["is_new"] = int(row["is_new"])
            writer.writerow(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.json")
    parser.add_argument("--cache", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--runs", type=Path, default=ROOT / "runs" / "m0")
    args = parser.parse_args()

    config = load_config(args.config)
    cache_dir = args.cache or (ROOT / config["data"]["cache_dir"]).resolve()
    if not cache_dir.exists():
        raise SystemExit(f"cache dir not found: {cache_dir}")

    papers = load_cache(
        cache_dir,
        top_k=config["concepts"]["top_k_per_paper"],
        min_level=config["concepts"]["min_level"],
        min_score=config["concepts"]["min_score"],
    )
    min_year = config["data"]["min_year"]
    max_year = config["data"]["max_year"]
    papers = [paper for paper in papers if min_year <= paper.year <= max_year]
    if not papers:
        raise SystemExit("no papers parsed; check the cache dir and filters")

    args.out.mkdir(parents=True, exist_ok=True)
    write_jsonl(papers, args.out / "papers.jsonl")

    series_by_id, names, total = build_series(papers)
    write_series_csv(args.out / "concept_series.csv", series_by_id, names, total)

    rows = rising_table(
        series_by_id,
        names,
        total,
        prev_years=config["windows"]["prev"],
        curr_years=config["windows"]["curr"],
        min_curr_count=config["rising"]["min_curr_count"],
        top_k=config["rising"]["top_k"],
    )
    write_rising_csv(args.out / "top_rising.csv", rows)

    year_counts = Counter(paper.year for paper in papers)
    summary = {
        "config": config,
        "papers": len(papers),
        "concepts": len(series_by_id),
        "years": {"min": min(year_counts), "max": max(year_counts)},
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
        "top_rising": [
            {
                "concept_id": row["concept_id"],
                "name": row["name"],
                "delta_share": round(row["delta_share"], 6),
                "growth": None if row["growth"] is None else round(row["growth"], 3),
                "is_new": row["is_new"],
                "curr_count": row["curr_count"],
            }
            for row in rows[:10]
        ],
    }

    args.runs.mkdir(parents=True, exist_ok=True)
    (args.runs / "config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (args.runs / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"papers: {len(papers)}")
    print(f"concepts: {len(series_by_id)}")
    print(f"years: {summary['years']}")
    print(f"wrote: {args.out}")
    print("top rising:")
    for index, row in enumerate(rows[:10], 1):
        growth = "new" if row["growth"] is None else f"{row['growth']:.2f}"
        print(
            f"  {index:>2}. {row['name']:<45} "
            f"delta_share={row['delta_share']:+.6f}  "
            f"growth={growth}  count={row['curr_count']}"
        )


if __name__ == "__main__":
    main()
