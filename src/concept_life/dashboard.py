"""Data loading helpers for the Streamlit demo.

The demo is read-only: it consumes the standard artifacts produced by M0-M3
and never calls an API. Keeping the loading logic here lets the app stay a
thin presentation layer.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed"
LABELS_DIR = ROOT / "data" / "labels"
RUNS_DIR = ROOT / "runs"


def require(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def load_json(path: Path) -> Any:
    return json.loads(require(path).read_text(encoding="utf-8"))


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(require(path), encoding="utf-8-sig")


def load_series(path: Path | None = None) -> pd.DataFrame:
    return load_csv(path or DATA_DIR / "concept_series.csv")


def load_rising(path: Path | None = None) -> pd.DataFrame:
    return load_csv(path or DATA_DIR / "top_rising.csv")


def load_replacements(path: Path | None = None) -> pd.DataFrame:
    return load_csv(path or DATA_DIR / "replacements.csv")


def load_predictions(path: Path | None = None) -> pd.DataFrame:
    return load_csv(path or DATA_DIR / "trend_predictions.csv")


def load_clusters(path: Path | None = None) -> pd.DataFrame:
    return load_csv(path or DATA_DIR / "lifecycle_clusters.csv")


def _normalize_label(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value).strip()
    if text in {"1", "1.0", "True", "true"}:
        return 1
    if text in {"0", "0.0", "False", "false"}:
        return 0
    return None


def load_review(
    replacements_path: Path | None = None,
    review_path: Path | None = None,
    limit: int = 20,
) -> pd.DataFrame:
    """Merge replacement candidates with human labels by rank.

    Human labels live in ``data/labels/replacement_review.csv`` and are tracked
    by git. If that file does not exist yet, fall back to the generated template
    in ``runs/m3/``.
    """
    replacements = load_replacements(replacements_path)
    labels_path = LABELS_DIR / "replacement_review.csv"
    template_path = RUNS_DIR / "m3" / "replacement_review.csv"
    if review_path is None:
        review_path = labels_path if labels_path.exists() else template_path
    if review_path.exists():
        review = pd.read_csv(review_path, encoding="utf-8-sig")
        keep = review[["rank", "valid_1_0", "notes"]].copy()
        replacements = replacements.merge(keep, on="rank", how="left")
    else:
        replacements["valid_1_0"] = None
        replacements["notes"] = ""
    replacements = replacements[replacements["rank"] <= limit].copy()
    replacements["valid_1_0"] = replacements["valid_1_0"].apply(_normalize_label)
    replacements["notes"] = replacements["notes"].fillna("").astype(str)
    return replacements


def review_precision(review: pd.DataFrame, k: int) -> dict[str, object]:
    """Precision over labeled rows only, for the top-k candidates."""
    subset = review[review["rank"] <= k]
    labeled = subset[subset["valid_1_0"].notna()]
    if labeled.empty:
        return {"k": k, "labeled": 0, "total": len(subset), "precision": None}
    return {
        "k": k,
        "labeled": len(labeled),
        "total": len(subset),
        "precision": float(labeled["valid_1_0"].sum() / len(labeled)),
    }


def load_events(path: Path | None = None) -> pd.DataFrame:
    path = require(path or DATA_DIR / "events.jsonl")
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return pd.DataFrame(rows)


def load_summaries() -> dict[str, Any]:
    return {
        "m1": load_json(RUNS_DIR / "m1" / "report" / "summary.json"),
        "m2": load_json(RUNS_DIR / "m2" / "summary.json"),
        "m3": load_json(RUNS_DIR / "m3" / "trend_metrics.json"),
        "replacement": load_json(RUNS_DIR / "m3" / "replacement_summary.json"),
    }


def concept_options(series: pd.DataFrame, limit: int = 300) -> list[tuple[str, str]]:
    totals = series.groupby("concept_id", as_index=False).agg(
        name=("name", "last"), total=("count", "sum")
    )
    totals = totals.sort_values("total", ascending=False).head(limit)
    return list(zip(totals["concept_id"], totals["name"]))


def timeline(
    series: pd.DataFrame, concept_id: str, start: int = 1995, end: int = 2023
) -> pd.DataFrame:
    rows = series[series["concept_id"] == concept_id].set_index("year")
    rows = rows.reindex(range(start, end + 1))
    rows["count"] = rows["count"].fillna(0).astype(int)
    rows["share"] = rows["share"].fillna(0.0)
    rows["name"] = rows["name"].ffill().bfill()
    return rows.rename_axis("year").reset_index()


def concept_events(events: pd.DataFrame, concept_id: str) -> pd.DataFrame:
    return events[events["concept_id"] == concept_id].sort_values(
        ["year", "type"]
    ).reset_index(drop=True)


def event_counts(events: pd.DataFrame) -> pd.DataFrame:
    return (
        events["type"]
        .value_counts()
        .rename_axis("type")
        .reset_index(name="events")
    )


def check_artifacts() -> list[Path]:
    required = [
        DATA_DIR / "concept_series.csv",
        DATA_DIR / "events.jsonl",
        DATA_DIR / "top_rising.csv",
        DATA_DIR / "replacements.csv",
        DATA_DIR / "trend_predictions.csv",
        DATA_DIR / "lifecycle_clusters.csv",
        LABELS_DIR / "replacement_review.csv",
        RUNS_DIR / "m1" / "report" / "year_histogram.csv",
        RUNS_DIR / "m1" / "report" / "summary.json",
        RUNS_DIR / "m2" / "summary.json",
        RUNS_DIR / "m3" / "trend_metrics.json",
        RUNS_DIR / "m3" / "replacement_summary.json",
    ]
    return [path for path in required if not path.exists()]
