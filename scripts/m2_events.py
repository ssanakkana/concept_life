#!/usr/bin/env python3
"""M2: detect lifecycle events from concept_series.csv.

Outputs:
  data/processed/events.jsonl
  data/processed/concept_events.csv
  runs/m2/summary.json
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from concept_life.config import load_config  # noqa: E402
from concept_life.mine import detect_events  # noqa: E402


def load_series(path: Path) -> tuple[dict[str, dict[int, int]], dict[str, str]]:
    series: dict[str, dict[int, int]] = defaultdict(dict)
    names: dict[str, str] = {}
    with path.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            concept_id = row["concept_id"]
            series[concept_id][int(row["year"])] = int(row["count"])
            names[concept_id] = row["name"]
    return dict(series), names


def load_totals(path: Path) -> dict[int, int]:
    totals: dict[int, int] = {}
    with path.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            totals[int(row["year"])] = int(row["papers"])
    return totals


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--series", type=Path, default=ROOT / "data" / "processed" / "concept_series.csv"
    )
    parser.add_argument(
        "--totals", type=Path, default=ROOT / "runs" / "m1" / "report" / "year_histogram.csv"
    )
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "m2.json")
    parser.add_argument(
        "--out", type=Path, default=ROOT / "data" / "processed" / "events.jsonl"
    )
    parser.add_argument(
        "--csv-out", type=Path, default=ROOT / "data" / "processed" / "concept_events.csv"
    )
    parser.add_argument("--summary", type=Path, default=ROOT / "runs" / "m2" / "summary.json")
    args = parser.parse_args()

    config = load_config(args.config)
    start = int(config["analysis"]["start_year"])
    end = int(config["analysis"]["end_year"])
    events_config = config["events"]

    series, names = load_series(args.series)
    totals = load_totals(args.totals)

    all_events = []
    for concept_id, counts in series.items():
        all_events.extend(
            detect_events(
                concept_id,
                names.get(concept_id, concept_id),
                counts,
                totals,
                start,
                end,
                events_config,
            )
        )
    all_events.sort(key=lambda event: (event.year, event.type, event.name))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for event in all_events:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    with args.csv_out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["concept_id", "name", "type", "year", "score", "evidence"])
        for event in all_events:
            writer.writerow(
                [
                    event.concept_id,
                    event.name,
                    event.type,
                    event.year,
                    f"{event.score:.6f}",
                    json.dumps(event.evidence, ensure_ascii=False, sort_keys=True),
                ]
            )

    by_type = Counter(event.type for event in all_events)
    summary = {
        "analysis": {"start_year": start, "end_year": end},
        "concepts": len(series),
        "concepts_with_events": len({event.concept_id for event in all_events}),
        "events": len(all_events),
        "events_by_type": dict(by_type),
        "config": events_config,
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
