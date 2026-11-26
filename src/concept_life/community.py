"""Community detection and bridge scoring on the co-occurrence graph."""
from __future__ import annotations

from typing import Any

import networkx as nx


def detect_communities(
    graph: nx.Graph,
    *,
    resolution: float = 1.0,
    seed: int = 42,
) -> tuple[dict[str, int], list[set[str]], float]:
    """Run Louvain and return (node -> community, communities, modularity).

    Communities are sorted by size then by their smallest node id, so the
    integer ids are stable across runs with the same seed.
    """
    communities = nx.community.louvain_communities(
        graph, weight="weight", resolution=resolution, seed=seed
    )
    communities = sorted(
        communities, key=lambda members: (-len(members), min(members))
    )
    mapping: dict[str, int] = {}
    for index, members in enumerate(communities):
        for node in members:
            mapping[node] = index
    modularity = nx.community.modularity(graph, communities, weight="weight")
    return mapping, communities, modularity


def bridge_scores(graph: nx.Graph) -> dict[str, float]:
    """Betweenness centrality, a proxy for concepts that connect communities."""
    return nx.betweenness_centrality(graph, normalized=True)
