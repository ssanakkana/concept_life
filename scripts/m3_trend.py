#!/usr/bin/env python3
"""M3: trend prediction with a strict temporal split.

Outputs:
  runs/m3/trend_metrics.json
  data/processed/trend_predictions.csv
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import sys
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from concept_life.config import load_config  # noqa: E402
from concept_life.predict import (  # noqa: E402
    build_degree,
    build_neighbours,
    evaluate_windows,
)


def load_series(path: Path) -> tuple[dict[str, dict[int, int]], dict[str, str]]:
    series: dict[str, dict[int, int]] = {}
    names: dict[str, str] = {}
    with path.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            concept_id = row["concept_id"]
            series.setdefault(concept_id, {})[int(row["year"])] = int(row["count"])
            names[concept_id] = row["name"]
    return series, names


def load_totals(path: Path) -> dict[int, int]:
    totals: dict[int, int] = {}
    with path.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            totals[int(row["year"])] = int(row["papers"])
    return totals


def load_paper_concepts(
    path: Path, candidate_ids: set[str]
) -> list[tuple[int | None, list[str]]]:
    rows: list[tuple[int | None, list[str]]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            paper = json.loads(line)
            rows.append(
                (
                    paper.get("year"),
                    [
                        concept["id"]
                        for concept in paper.get("concepts") or []
                        if concept.get("id") in candidate_ids
                    ],
                )
            )
    return rows


def build_support_upto(
    rows: list[tuple[int | None, list[str]]], min_support: int, max_year: int
) -> dict[tuple[str, str], int]:
    """Co-occurrence support using only papers up to ``max_year``.

    The trend model must not see future edges: degree and neighbour features
    would otherwise leak the future.
    """
    support: dict[tuple[str, str], int] = {}
    for year, ids in rows:
        if year is None or year > max_year:
            continue
        unique = sorted(set(ids))
        for left, right in itertools.combinations(unique, 2):
            key = (left, right)
            support[key] = support.get(key, 0) + 1
    return {key: value for key, value in support.items() if value >= min_support}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--series", type=Path, default=ROOT / "data" / "processed" / "concept_series.csv"
    )
    parser.add_argument(
        "--totals", type=Path, default=ROOT / "runs" / "m1" / "report" / "year_histogram.csv"
    )
    parser.add_argument(
        "--papers", type=Path, default=ROOT / "data" / "processed" / "papers.jsonl"
    )
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "m3.json")
    parser.add_argument(
        "--metrics", type=Path, default=ROOT / "runs" / "m3" / "trend_metrics.json"
    )
    parser.add_argument(
        "--predictions",
        type=Path,
        default=ROOT / "data" / "processed" / "trend_predictions.csv",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    analysis = config["analysis"]
    trend_config = config["trend"]
    flat_config = {
        "start_year": int(analysis["start_year"]),
        "end_year": int(analysis["end_year"]),
        **trend_config,
    }

    series, names = load_series(args.series)
    totals = load_totals(args.totals)
    candidate_ids = {
        concept_id
        for concept_id, counts in series.items()
        if sum(counts.values()) >= int(config["replacement"]["min_total_count"])
    }
    rows = load_paper_concepts(args.papers, candidate_ids)
    graphs: dict[int, tuple[dict[str, int], dict[str, list[tuple[str, int]]]]] = {}
    for year in flat_config["windows"]:
        support = build_support_upto(
            rows, int(config["replacement"]["min_support"]), int(year)
        )
        graphs[int(year)] = (
            build_degree(support),
            build_neighbours(support, top_k=5),
        )

    metrics, predictions = evaluate_windows(series, totals, graphs, flat_config)
    for row in predictions:
        row["name"] = names.get(row["concept_id"], row["concept_id"])

    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    args.metrics.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    args.predictions.parent.mkdir(parents=True, exist_ok=True)
    with args.predictions.open("w", encoding="utf-8-sig", newline="") as handle:
        fields = [
            "rank", "concept_id", "name", "score",
            "actual_future_growth", "in_top_k",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in predictions:
            writer.writerow(row)

    print("mean metrics across windows:")
    for name in ["model", "frequency", "growth", "random"]:
        row = metrics["mean"][name]
        print(
            f"  {name:<10} "
            + "  ".join(f"{key}={value:.3f}" for key, value in row.items())
        )
    print(f"\nwrote {args.metrics}")
    print(f"wrote {args.predictions}")


if __name__ == "__main__":
    main()
