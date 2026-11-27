"""Render the same offline research map for Streamlit and standalone HTML."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


EXPERIMENTS = Path(__file__).resolve().parents[2] / "experiments"


def inline_map_d3(html: str) -> str:
    source = (EXPERIMENTS / "d3.v7.min.js").read_text(encoding="utf-8")
    source = source.replace("</script", "<\\/script")
    return html.replace(
        '<script src="d3.v7.min.js"></script>',
        f"<script>\n{source}\n</script>",
        1,
    )


def render_map_html(
    nodes_path: Path,
    edges_path: Path,
    summary: dict[str, Any],
    *,
    inline_d3: bool = False,
) -> str:
    with nodes_path.open(encoding="utf-8-sig", newline="") as handle:
        nodes = [
            {
                "id": row["concept_id"],
                "name": row["name"],
                "community": int(row["community"]),
                "total": int(row["total_count"]),
                "betweenness": float(row["betweenness"]),
                "degree": int(row["degree"]),
                "x": float(row["x"]),
                "y": float(row["y"]),
            }
            for row in csv.DictReader(handle)
        ]
    with edges_path.open(encoding="utf-8-sig", newline="") as handle:
        links = [
            {
                "source": row["source"],
                "target": row["target"],
                "support": int(row["support"]),
            }
            for row in csv.DictReader(handle)
        ]
    payload = {
        "nodes": nodes,
        "links": links,
        "communities": summary["communities"],
        "stats": {
            "nodes": len(nodes),
            "edges": len(links),
            "communities": summary["n_communities"],
            "modularity": summary["modularity"],
        },
    }
    data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    template = (EXPERIMENTS / "map_template.html").read_text(encoding="utf-8")
    if inline_d3:
        template = inline_map_d3(template)
    return template.replace("__DATA_JSON__", data_json, 1)
