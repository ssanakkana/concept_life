#!/usr/bin/env python3
"""Inline D3 into the standalone map so it can be shared as one file.

Run after scripts/build_map_html.py:
    uv run python scripts/build_map_standalone.py
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments" / "map_interactive.html"
D3 = ROOT / "experiments" / "d3.v7.min.js"
OUT = ROOT / "experiments" / "map_standalone.html"


def main() -> None:
    html = SOURCE.read_text(encoding="utf-8")
    d3 = D3.read_text(encoding="utf-8").replace("</script", "<\\/script")
    html = html.replace(
        '<script src="d3.v7.min.js"></script>',
        f"<script>\n{d3}\n</script>",
    )
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({len(html) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
