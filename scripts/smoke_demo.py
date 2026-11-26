#!/usr/bin/env python3
"""Smoke-test every Streamlit page with AppTest.

Run inside the uv environment:
    uv run python scripts/smoke_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "src" / "concept_life" / "app.py"
PAGES = ["总览", "概念时间线", "上升与替代", "趋势回测", "数据与方法"]


def main() -> int:
    app = AppTest.from_file(str(APP), default_timeout=60)
    app.run()
    failures = 0
    for page in PAGES:
        app.sidebar.radio[0].set_value(page)
        app.run()
        errors = list(app.exception)
        print(f"{page}: {len(errors)} exception(s)")
        for error in errors:
            print(f"  {error.value}")
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
