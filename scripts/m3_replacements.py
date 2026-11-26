#!/usr/bin/env python3
"""M3: candidate replacement detection.

Outputs:
  data/processed/replacements.jsonl
  data/processed/replacements.csv
  runs/m3/replacement_summary.json
  runs/m3/replacement_review.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from concept_life.config import load_config  # noqa: E402
from concept_life.predict import mean_share  # noqa: E402
from concept_life.replace import build_cooccurrence, detect_replacements  # noqa: E402


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


def load_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def iter_papers(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--series", type=Path, default=ROOT / "data" / "processed" / "concept_series.csv"
    )
    parser.add_argument(
        "--totals", type=Path, default=ROOT / "runs" / "m1" / "report" / "year_histogram.csv"
    )
    parser.add_argument(
        "--events", type=Path, default=ROOT / "data" / "processed" / "events.jsonl"
    )
    parser.add_argument(
        "--papers", type=Path, default=ROOT / "data" / "processed" / "papers.jsonl"
    )
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "m3.json")
    parser.add_argument(
        "--out", type=Path, default=ROOT / "data" / "processed" / "replacements.jsonl"
    )
    parser.add_argument(
        "--csv-out", type=Path, default=ROOT / "data" / "processed" / "replacements.csv"
    )
    parser.add_argument(
        "--summary", type=Path, default=ROOT / "runs" / "m3" / "replacement_summary.json"
    )
    parser.add_argument(
        "--review", type=Path, default=ROOT / "runs" / "m3" / "replacement_review.csv"
    )
    args = parser.parse_args()

    config = load_config(args.config)
    analysis = config["analysis"]
    replacement_config = config["replacement"]
    start_year = int(analysis["start_year"])
    end_year = int(analysis["end_year"])

    series, names = load_series(args.series)
    totals = load_totals(args.totals)
    events = load_events(args.events)
    candidate_ids = {
        concept_id
        for concept_id, counts in series.items()
        if sum(counts.values()) >= int(replacement_config["min_total_count"])
    }

    support = build_cooccurrence(
        iter_papers(args.papers),
        candidate_ids,
        min_support=int(replacement_config["min_support"]),
    )

    decline_ids = {event["concept_id"] for event in events if event["type"] == "decline"}
    peak_years = {
        event["concept_id"]: event["year"] for event in events if event["type"] == "peak"
    }
    burst_years = {
        event["concept_id"]: event["year"] for event in events if event["type"] == "burst"
    }

    late_start = 2018
    early_start = 2015
    rising_ids = set(burst_years)
    for concept_id in candidate_ids:
        late = mean_share(series[concept_id], totals, range(late_start, late_start + 3))
        early = mean_share(series[concept_id], totals, range(early_start, early_start + 3))
        if late - early > float(replacement_config["min_late_growth"]):
            rising_ids.add(concept_id)

    new_years = {
        concept_id: burst_years.get(concept_id, late_start) for concept_id in rising_ids
    }

    flat_config = {
        "start_year": start_year,
        "end_year": end_year,
        **replacement_config,
    }
    rows = detect_replacements(
        series,
        totals,
        support,
        decline_ids,
        peak_years,
        rising_ids,
        new_years,
        flat_config,
    )
    for row in rows:
        row["old_name"] = names.get(row["old_id"], row["old_id"])
        row["new_name"] = names.get(row["new_id"], row["new_id"])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    with args.csv_out.open("w", encoding="utf-8-sig", newline="") as handle:
        fields = [
            "rank", "old_id", "old_name", "new_id", "new_name",
            "old_peak_year", "new_year", "support", "jaccard",
            "correlation", "score", "old_peak_share", "old_last_share",
            "new_last_share", "overtake",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for rank, row in enumerate(rows, 1):
            writer.writerow({"rank": rank, **row})

    args.review.parent.mkdir(parents=True, exist_ok=True)
    with args.review.open("w", encoding="utf-8-sig", newline="") as handle:
        fields = [
            "rank", "old_name", "new_name", "old_peak_year", "new_year",
            "jaccard", "correlation", "overtake", "score", "valid_1_0", "notes",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for rank, row in enumerate(rows[:20], 1):
            writer.writerow(
                {
                    "rank": rank,
                    "old_name": row["old_name"],
                    "new_name": row["new_name"],
                    "old_peak_year": row["old_peak_year"],
                    "new_year": row["new_year"],
                    "jaccard": row["jaccard"],
                    "correlation": row["correlation"],
                    "overtake": row["overtake"],
                    "score": row["score"],
                    "valid_1_0": "",
                    "notes": "",
                }
            )

    summary = {
        "pairs": len(rows),
        "declining_concepts": len(decline_ids),
        "rising_concepts": len(rising_ids),
        "cooccurrence_pairs": len(support),
        "config": replacement_config,
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\ntop candidates:")
    for rank, row in enumerate(rows[:10], 1):
        print(
            f"{rank:>2}. {row['old_name']} -> {row['new_name']}  "
            f"peak={row['old_peak_year']} new={row['new_year']} "
            f"jac={row['jaccard']:.3f} corr={row['correlation']:+.3f} "
            f"score={row['score']:.3f}"
        )


if __name__ == "__main__":
    main()
