#!/usr/bin/env python3
"""Inline D3 into the standalone map so it can be shared as one file.

Run after scripts/build_map_html.py:
    uv run python scripts/build_map_standalone.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from concept_life.research_map import inline_map_d3  # noqa: E402


SOURCE = ROOT / "experiments" / "map_interactive.html"
OUT = ROOT / "experiments" / "map_standalone.html"


def main() -> None:
    html = inline_map_d3(SOURCE.read_text(encoding="utf-8"))
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({len(html) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
