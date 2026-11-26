#!/usr/bin/env python3
"""Compute precision@10 and precision@20 from human-labeled replacements.

Run the demo's 替代复核 page first, or fill
runs/m3/replacement_review.csv's valid_1_0 column manually.

Usage:
    uv run python scripts/evaluate_replacements.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from concept_life.dashboard import load_review, review_precision  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "runs" / "m3" / "replacement_metrics.json",
    )
    args = parser.parse_args()

    review = load_review()
    metrics = {
        "labeled": int(review["valid_1_0"].notna().sum()),
        "total": len(review),
        "precision@10": review_precision(review, 10),
        "precision@20": review_precision(review, 20),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"labeled {metrics['labeled']}/{metrics['total']}")
    for key in ("precision@10", "precision@20"):
        row = metrics[key]
        if row["precision"] is None:
            print(f"{key}: no labels")
        else:
            print(
                f"{key}: {row['precision']:.3f} "
                f"({row['labeled']}/{row['total']} labeled)"
            )
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
