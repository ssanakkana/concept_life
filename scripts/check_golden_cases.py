#!/usr/bin/env python3
"""Check golden cases against generated lifecycle events.

Usage:
    python scripts/check_golden_cases.py
    python scripts/check_golden_cases.py --events data/processed/events.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_events(path: Path) -> list[dict]:
    events: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases", type=Path, default=ROOT / "configs" / "golden_cases.json"
    )
    parser.add_argument(
        "--events", type=Path, default=ROOT / "data" / "processed" / "events.jsonl"
    )
    args = parser.parse_args()

    cases = json.loads(args.cases.read_text(encoding="utf-8"))["cases"]
    events = load_events(args.events)
    by_key: dict[tuple[str, str], list[int]] = defaultdict(list)
    for event in events:
        by_key[(event["concept_id"], event["type"])].append(event["year"])

    failures = 0
    rows: list[tuple[str, str, str, str, str]] = []
    for case in cases:
        concept_id = case["concept_id"]
        for event_type, (low, high) in case["expected"].items():
            years = sorted(by_key.get((concept_id, event_type), []))
            actual = years[0] if years else None
            ok = actual is not None and low <= actual <= high
            failures += 0 if ok else 1
            rows.append(
                (
                    case["name"],
                    event_type,
                    f"{low}-{high}",
                    str(actual) if actual is not None else "missing",
                    "OK" if ok else "FAIL",
                )
            )

    widths = [max(len(row[index]) for row in rows) for index in range(5)]
    for row in rows:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))
    print(f"\n{len(rows) - failures}/{len(rows)} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
