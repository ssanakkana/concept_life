#!/usr/bin/env python3
"""M5: cluster concepts by lifecycle shape.

Outputs:
  data/processed/lifecycle_clusters.csv
  runs/m5/clusters_summary.json
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from concept_life.cluster import (  # noqa: E402
    FEATURE_NAMES,
    build_feature_rows,
    choose_k,
    label_clusters,
    standardize,
)
from concept_life.config import load_config  # noqa: E402


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
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "m5.json")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data" / "processed" / "lifecycle_clusters.csv",
    )
    parser.add_argument(
        "--summary", type=Path, default=ROOT / "runs" / "m5" / "clusters_summary.json"
    )
    args = parser.parse_args()

    config = load_config(args.config)
    analysis = config["analysis"]
    cluster_config = config["cluster"]
    start_year = int(analysis["start_year"])
    end_year = int(analysis["end_year"])

    series, names = load_series(args.series)
    totals = load_totals(args.totals)
    events = load_events(args.events)

    rows = build_feature_rows(
        series,
        names,
        totals,
        events,
        start_year=start_year,
        end_year=end_year,
        min_total_count=int(cluster_config["min_total_count"]),
        active_min_count=int(cluster_config["active_min_count"]),
        min_year_total=int(cluster_config["min_year_total"]),
    )
    if not rows:
        raise SystemExit("no concepts to cluster")

    matrix = np.asarray([[row[name] for name in FEATURE_NAMES] for row in rows])
    matrix = standardize(matrix)
    k, labels, _centers, results = choose_k(
        matrix,
        [int(value) for value in cluster_config["k_values"]],
        seed=int(cluster_config["seed"]),
        n_init=int(cluster_config["n_init"]),
        max_iter=int(cluster_config["max_iter"]),
    )
    label_names, centroids = label_clusters(rows, labels, k)
    for row, label in zip(rows, labels):
        row["cluster"] = int(label)
        row["label"] = label_names[int(label)]

    fields = [
        "concept_id", "name", "cluster", "label", "total_count",
        "first_year", "last_active", "peak_year", "span", "active_ratio",
        "peak_position", "peak_share", "decline_speed", "recent_to_peak",
        "volatility", "years_since_peak", "burst_flag", "decline_flag",
        "revival_flag",
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in sorted(rows, key=lambda item: (item["cluster"], -item["total_count"])):
            writer.writerow({field: row[field] for field in fields})

    sizes = Counter(row["label"] for row in rows)
    clusters_summary = {}
    for index in range(k):
        members = [row for row in rows if row["cluster"] == index]
        members.sort(key=lambda item: -item["total_count"])
        clusters_summary[label_names[index]] = {
            "cluster": index,
            "size": len(members),
            "centroid": {
                name: round(value, 4) for name, value in centroids[index].items()
            },
            "examples": [
                {
                    "name": member["name"],
                    "total_count": member["total_count"],
                    "peak_year": member["peak_year"],
                }
                for member in members[:8]
            ],
        }
    summary = {
        "k": k,
        "silhouette": {
            str(key): value["silhouette"] for key, value in results.items()
        },
        "clusters": clusters_summary,
        "features": FEATURE_NAMES,
        "concepts": len(rows),
        "analysis": {"start_year": start_year, "end_year": end_year},
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps({"k": k, "silhouette": summary["silhouette"], "sizes": dict(sizes)}, ensure_ascii=False, indent=2))
    for label, info in sorted(clusters_summary.items(), key=lambda item: -item[1]["size"]):
        examples = "，".join(example["name"] for example in info["examples"][:5])
        print(f"{label} ({info['size']}): {examples}")
    print(f"wrote {args.out}")
    print(f"wrote {args.summary}")


if __name__ == "__main__":
    main()
