"""Configuration loading.

The project uses a plain JSON file so that M0 has no third-party dependency.
Later stages can add more sections without changing the loader.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "data": {
        "cache_dir": "../kg_search/cache",
        "min_year": 1990,
        "max_year": 2025,
        # None disables domain filtering; M1 config sets "computer science".
        "domain": None,
        "keep_unknown_domain": True,
    },
    "concepts": {
        "top_k_per_paper": 10,
        "min_level": 2,
        "min_score": 0.0,
        # Ambiguous or cross-domain concept names to drop before aggregation.
        "stoplist": [],
    },
    "windows": {
        # Explicit year lists, not [start, end] ranges.
        "prev": [2015, 2016, 2017],
        "curr": [2018, 2019, 2020],
    },
    "rising": {
        "min_curr_count": 5,
        "top_k": 30,
    },
    "analysis": {
        "start_year": 1995,
        "end_year": 2023,
    },
    "events": {
        "min_total_count": 20,
        "birth_min_count": 1,
        "active_min_count": 2,
        "burst_window": 3,
        "burst_z": 2.0,
        "burst_min_count": 5,
        "burst_min_delta": 0.002,
        "burst_min_rel": 0.2,
        "min_year_total": 100,
        "peak_min_count": 5,
        "decline_ratio": 0.65,
        "decline_window": 2,
        "death_gap": 3,
        "revival_gap": 2,
    },
}


def _deep_update(base: dict[str, Any], override: dict[str, Any]) -> None:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load the default config, optionally merged with a JSON file.

    A missing explicit path is an error so that a typo does not silently fall
    back to defaults. Passing ``None`` returns the defaults.
    """
    config = deepcopy(DEFAULT_CONFIG)
    if path is None:
        return config

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"config not found: {path}")
    override = json.loads(path.read_text(encoding="utf-8"))
    _deep_update(config, override)
    return config
