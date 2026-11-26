#!/usr/bin/env python3
"""M8: Louvain communities, bridge concepts, and a pruned research map.

Outputs:
  data/processed/communities.csv
  data/processed/research_map_nodes.csv
  data/processed/research_map_edges.csv
  runs/m8/community_summary.json
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterator

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from concept_life.community import bridge_scores, detect_communities  # noqa: E402
from concept_life.config import load_config  # noqa: E402


def load_totals(path: Path) -> tuple[dict[str, int], dict[str, str]]:
    totals: dict[str, int] = defaultdict(int)
    names: dict[str, str] = {}
    with path.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            concept_id = row["concept_id"]
            totals[concept_id] += int(row["count"])
            names[concept_id] = row["name"]
    return dict(totals), names


def iter_papers(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def build_support(
    papers: Iterator[dict[str, Any]], candidate_ids: set[str], min_support: int
) -> dict[tuple[str, str], int]:
    support: dict[tuple[str, str], int] = {}
    for paper in papers:
        ids = sorted(
            {
                concept["id"]
                for concept in paper.get("concepts") or []
                if concept.get("id") in candidate_ids
            }
        )
        for left, right in itertools.combinations(ids, 2):
            key = (left, right)
            support[key] = support.get(key, 0) + 1
    return {key: value for key, value in support.items() if value >= min_support}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--series", type=Path, default=ROOT / "data" / "processed" / "concept_series.csv"
    )
    parser.add_argument(
        "--papers", type=Path, default=ROOT / "data" / "processed" / "papers.jsonl"
    )
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "m8.json")
    parser.add_argument(
        "--communities",
        type=Path,
        default=ROOT / "data" / "processed" / "communities.csv",
    )
    parser.add_argument(
        "--nodes",
        type=Path,
        default=ROOT / "data" / "processed" / "research_map_nodes.csv",
    )
    parser.add_argument(
        "--edges",
        type=Path,
        default=ROOT / "data" / "processed" / "research_map_edges.csv",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=ROOT / "runs" / "m8" / "community_summary.json",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    graph_config = config["graph"]
    totals, names = load_totals(args.series)
    top_ids = [
        concept_id
        for concept_id, _ in sorted(totals.items(), key=lambda item: -item[1])
        if totals[concept_id] >= int(graph_config["min_total_count"])
    ][: int(graph_config["top_concepts"])]
    candidate_ids = set(top_ids)

    support = build_support(
        iter_papers(args.papers),
        candidate_ids,
        int(graph_config["min_support"]),
    )
    graph = nx.Graph()
    for concept_id in top_ids:
        graph.add_node(
            concept_id, name=names.get(concept_id, concept_id), total=totals[concept_id]
        )
    for (left, right), weight in support.items():
        graph.add_edge(left, right, weight=weight)

    isolates = list(nx.isolates(graph))
    graph.remove_nodes_from(isolates)
    if graph.number_of_nodes() < 2:
        raise SystemExit("graph too small after removing isolates")

    mapping, communities, modularity = detect_communities(
        graph,
        resolution=float(graph_config["louvain_resolution"]),
        seed=int(graph_config["seed"]),
    )
    betweenness = bridge_scores(graph)

    args.communities.parent.mkdir(parents=True, exist_ok=True)
    with args.communities.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["concept_id", "name", "community", "total_count", "degree", "betweenness"]
        )
        for concept_id in sorted(graph.nodes, key=lambda cid: -totals[cid]):
            writer.writerow(
                [
                    concept_id,
                    names.get(concept_id, concept_id),
                    mapping[concept_id],
                    totals[concept_id],
                    graph.degree(concept_id),
                    round(betweenness[concept_id], 6),
                ]
            )

    map_ids = [
        concept_id
        for concept_id in top_ids
        if concept_id in graph and totals[concept_id] > 0
    ][: int(graph_config["map_nodes"])]
    subgraph = graph.subgraph(map_ids).copy()
    keep_edges: set[tuple[str, str]] = set()
    for node in subgraph.nodes:
        strongest = sorted(
            subgraph.edges(node, data=True),
            key=lambda item: -item[2].get("weight", 0),
        )[: int(graph_config["edges_per_node"])]
        for left, right, _data in strongest:
            keep_edges.add((left, right))
    subgraph = subgraph.edge_subgraph(keep_edges).copy()
    subgraph.remove_nodes_from(list(nx.isolates(subgraph)))
    positions = nx.spring_layout(
        subgraph, weight="weight", seed=int(graph_config["seed"]), k=0.5, iterations=100
    )
    xs = [position[0] for position in positions.values()]
    ys = [position[1] for position in positions.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max_x - min_x if max_x > min_x else 1.0
    span_y = max_y - min_y if max_y > min_y else 1.0

    args.nodes.parent.mkdir(parents=True, exist_ok=True)
    with args.nodes.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["concept_id", "name", "community", "x", "y", "total_count", "betweenness", "degree"]
        )
        for concept_id in subgraph.nodes:
            x = (positions[concept_id][0] - min_x) / span_x
            y = (positions[concept_id][1] - min_y) / span_y
            writer.writerow(
                [
                    concept_id,
                    names.get(concept_id, concept_id),
                    mapping[concept_id],
                    round(x, 6),
                    round(y, 6),
                    totals[concept_id],
                    round(betweenness[concept_id], 6),
                    subgraph.degree(concept_id),
                ]
            )

    with args.edges.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source", "target", "support"])
        for left, right, data in subgraph.edges(data=True):
            writer.writerow([left, right, data.get("weight", 1)])

    community_rows = []
    for index, members in enumerate(communities):
        members_sorted = sorted(members, key=lambda cid: -totals[cid])
        community_rows.append(
            {
                "community": index,
                "size": len(members),
                "top_concepts": [
                    names.get(concept_id, concept_id)
                    for concept_id in members_sorted[:5]
                ],
            }
        )
    bridges = sorted(
        (
            {
                "concept_id": concept_id,
                "name": names.get(concept_id, concept_id),
                "community": mapping[concept_id],
                "betweenness": round(betweenness[concept_id], 6),
                "total_count": totals[concept_id],
            }
            for concept_id in graph.nodes
        ),
        key=lambda row: -row["betweenness"],
    )

    summary = {
        "n_nodes_full": graph.number_of_nodes(),
        "n_edges_full": graph.number_of_edges(),
        "n_communities": len(communities),
        "modularity": round(float(modularity), 4),
        "communities": community_rows,
        "top_bridges": bridges[:15],
        "map": {
            "nodes": subgraph.number_of_nodes(),
            "edges": subgraph.number_of_edges(),
        },
        "removed_isolates": len(isolates),
        "config": graph_config,
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "nodes": graph.number_of_nodes(),
                "edges": graph.number_of_edges(),
                "communities": len(communities),
                "modularity": round(float(modularity), 4),
                "map_nodes": subgraph.number_of_nodes(),
                "map_edges": subgraph.number_of_edges(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    print("top bridges:")
    for row in bridges[:8]:
        print(f"  {row['betweenness']:.4f} {row['name']} (community {row['community']})")
    print(f"wrote {args.communities}")
    print(f"wrote {args.nodes}")
    print(f"wrote {args.edges}")
    print(f"wrote {args.summary}")


if __name__ == "__main__":
    main()
