#!/usr/bin/env python3
"""Build a standalone interactive research map.

The HTML embeds the top-300 nodes and pruned co-occurrence edges. It uses a
local D3 copy in experiments/d3.v7.min.js, so opening it does not need network.

Usage:
    uv run python scripts/build_map_html.py
    # open experiments/map_interactive.html in a browser
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "src"))

from concept_life.research_map import render_map_html  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
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
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "experiments" / "map_interactive.html",
    )
    args = parser.parse_args()

    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    html = render_map_html(args.nodes, args.edges, summary)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    print(f"wrote {args.out} ({len(html) / 1024:.1f} KB)")
    print(f"nodes={summary['map']['nodes']} links={summary['map']['edges']}")
    if not (args.out.parent / "d3.v7.min.js").exists():
        print("warning: d3.v7.min.js is missing next to the HTML", file=sys.stderr)


if __name__ == "__main__":
    main()
