#!/usr/bin/env python3
"""M1: crawl Acemap work search responses with caching and resume.

Every response is written as one JSON file under ``--out``. Existing valid
files are skipped, so an interrupted crawl can be restarted. A JSONL manifest
records every request, including cached, missing and failed ones.

Usage:
    python scripts/crawl.py --pages 4 --size 100
    python scripts/crawl.py --max-queries 5 --pages 1   # smoke test
    python scripts/crawl.py --offline                    # count cached only
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
API_URL = "https://acemap.info/api/v1/work/search"
USER_AGENT = "AI3602-ConceptLife/1.0"


def query_key(query: str) -> str:
    """Stable file key. A hash avoids slug collisions between similar queries."""
    return hashlib.sha1(query.encode("utf-8")).hexdigest()[:12]


def load_queries(path: Path) -> list[tuple[str, str]]:
    """Return (query, category) pairs, deduplicated case-insensitively."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [(str(item).strip(), "all") for item in data if str(item).strip()]

    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for category, items in data.items():
        if not isinstance(items, list):
            continue
        for item in items:
            query = str(item).strip()
            key = query.lower()
            if not query or key in seen:
                continue
            seen.add(key)
            out.append((query, str(category)))
    return out


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def append_manifest(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_cached(path: Path) -> dict[str, Any] | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or "results" not in data:
        return None
    return data


def fetch(
    session: requests.Session,
    query: str,
    page: int,
    size: int,
    timeout: float,
    retries: int,
) -> dict[str, Any]:
    params = {"keyword": query, "order": "desc", "page": page, "size": size}
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = session.get(API_URL, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # noqa: BLE001 - retry on any transport/parse error
            last_error = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"{query!r} page {page}: {last_error}") from last_error


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, default=ROOT / "configs" / "queries.json")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "raw" / "acemap")
    parser.add_argument(
        "--manifest", type=Path, default=ROOT / "data" / "raw" / "acemap_manifest.jsonl"
    )
    parser.add_argument(
        "--summary", type=Path, default=ROOT / "data" / "raw" / "crawl_summary.json"
    )
    parser.add_argument("--pages", type=int, default=4)
    parser.add_argument("--size", type=int, default=100)
    parser.add_argument("--delay", type=float, default=0.7)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--max-queries", type=int, default=0)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()

    queries = load_queries(args.queries)
    if args.max_queries:
        queries = queries[: args.max_queries]
    args.out.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    stats: dict[str, Any] = {
        "queries": len(queries),
        "requests": 0,
        "cached": 0,
        "fetched": 0,
        "failed": 0,
        "missing": 0,
        "records": 0,
        "files": 0,
    }
    started = time.time()

    for index, (query, category) in enumerate(queries, 1):
        key = query_key(query)
        query_records = 0
        for page in range(1, args.pages + 1):
            filename = f"{key}_p{page}_s{args.size}.json"
            path = args.out / filename
            stats["requests"] += 1

            data = read_cached(path)
            if data is not None:
                stats["cached"] += 1
                count = len(data.get("results") or [])
                query_records += count
                append_manifest(
                    args.manifest,
                    {
                        "query": query,
                        "category": category,
                        "page": page,
                        "size": args.size,
                        "file": filename,
                        "status": "cached",
                        "result_count": count,
                        "total_count": (data.get("meta") or {}).get("count"),
                        "fetched_at": None,
                    },
                )
                if count < args.size:
                    break
                continue

            if args.offline:
                stats["missing"] += 1
                append_manifest(
                    args.manifest,
                    {
                        "query": query,
                        "category": category,
                        "page": page,
                        "size": args.size,
                        "file": filename,
                        "status": "missing",
                        "result_count": 0,
                        "total_count": None,
                        "fetched_at": None,
                    },
                )
                continue

            try:
                data = fetch(
                    session, query, page, args.size, args.timeout, args.retries
                )
            except RuntimeError as exc:
                stats["failed"] += 1
                append_manifest(
                    args.manifest,
                    {
                        "query": query,
                        "category": category,
                        "page": page,
                        "size": args.size,
                        "file": filename,
                        "status": "error",
                        "result_count": 0,
                        "total_count": None,
                        "fetched_at": now(),
                        "error": str(exc),
                    },
                )
                break

            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            stats["fetched"] += 1
            count = len(data.get("results") or [])
            query_records += count
            append_manifest(
                args.manifest,
                {
                    "query": query,
                    "category": category,
                    "page": page,
                    "size": args.size,
                    "file": filename,
                    "status": "ok",
                    "result_count": count,
                    "total_count": (data.get("meta") or {}).get("count"),
                    "fetched_at": now(),
                },
            )
            time.sleep(args.delay)
            if count < args.size:
                break

        stats["records"] += query_records
        if index % 10 == 0 or index == len(queries):
            print(
                f"[{index}/{len(queries)}] {category}: {query} -> {query_records} records",
                flush=True,
            )

    stats["files"] = len(list(args.out.glob("*.json")))
    stats["elapsed_sec"] = round(time.time() - started, 1)
    summary = {"out": str(args.out), "queries_file": str(args.queries), **stats}
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
