"""Rule-based lifecycle events from a concept's yearly series.

The rules are deliberately simple and explainable. They use share of papers,
not raw counts, because the corpus grows over time. "Birth", "death" and
"revival" always mean "in this corpus", never "in the world".

Event types:

- birth: first year with at least ``birth_min_count`` papers in the range
- burst: first year whose share is at least ``burst_z`` standard deviations
  above the previous ``burst_window`` years
- peak: year with the largest share, if it has at least ``peak_min_count`` papers
- decline: first post-peak year whose next ``decline_window`` years average
  below ``decline_ratio`` times the peak share
- dormancy: start of a post-peak gap of at least ``revival_gap`` years
- revival: first active year after a dormancy
- death: start of a post-peak gap that reaches the end of the analysis range
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


EVENT_TYPES = (
    "birth",
    "burst",
    "peak",
    "decline",
    "dormancy",
    "revival",
    "death",
)


@dataclass(frozen=True)
class Event:
    concept_id: str
    name: str
    type: str
    year: int
    score: float
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "name": self.name,
            "type": self.type,
            "year": self.year,
            "score": round(float(self.score), 6),
            "evidence": self.evidence,
        }


def _years(start: int, end: int) -> list[int]:
    return list(range(start, end + 1))


def _shares(
    counts: dict[int, int], total: dict[int, int], start: int, end: int
) -> dict[int, float]:
    shares: dict[int, float] = {}
    for year in _years(start, end):
        denominator = total.get(year, 0)
        shares[year] = counts.get(year, 0) / denominator if denominator else 0.0
    return shares


def _detect_burst(
    shares: dict[int, float],
    counts: dict[int, int],
    total: dict[int, int],
    years: list[int],
    config: dict[str, Any],
) -> dict[str, Any] | None:
    window = int(config["burst_window"])
    z_min = float(config["burst_z"])
    min_count = int(config["burst_min_count"])
    min_delta = float(config.get("burst_min_delta", 0.0))
    min_relative = float(config.get("burst_min_rel", 0.0))
    min_year_total = int(config.get("min_year_total", 0))

    runs: list[list[tuple[int, float]]] = []
    current: list[tuple[int, float]] = []

    for index, year in enumerate(years):
        if index < window:
            continue
        previous = [shares[value] for value in years[index - window:index]]
        mean = sum(previous) / len(previous)
        variance = sum((value - mean) ** 2 for value in previous) / len(previous)
        std = variance ** 0.5
        z = (shares[year] - mean) / (std + 1e-9)

        # A high z-score on a flat, tiny series is not a burst. Require a
        # minimum absolute and relative increase over the previous year.
        previous_share = shares[years[index - 1]]
        delta = shares[year] - previous_share
        relative = delta / (previous_share + 1e-12) if previous_share > 0 else float("inf")

        if (
            z >= z_min
            and counts[year] >= min_count
            and delta >= min_delta
            and relative >= min_relative
            and total.get(year, 0) >= min_year_total
        ):
            current.append((year, z))
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    if not runs:
        return None

    # Pick the strongest run, not the first one: an early noisy spike should
    # not hide a later, much larger burst.
    best_run = max(runs, key=lambda run: max(z for _, z in run))
    best_year, best_z = max(best_run, key=lambda item: item[1])
    return {
        # The burst year is the strongest year in the run, not the onset.
        # A gradual ramp followed by a spike should be dated at the spike.
        "year": best_year,
        "z": round(best_z, 4),
        "run_years": [year for year, _ in best_run],
        "burst_count": counts[best_year],
    }


def _detect_decline(
    shares: dict[int, float],
    years: list[int],
    peak_year: int,
    config: dict[str, Any],
) -> dict[str, Any] | None:
    ratio = float(config["decline_ratio"])
    window = int(config["decline_window"])
    peak_share = shares[peak_year]
    if peak_share <= 0:
        return None

    for index, year in enumerate(years):
        if year <= peak_year:
            continue
        window_years = years[index:index + window]
        if len(window_years) < window:
            break
        average = sum(shares[value] for value in window_years) / len(window_years)
        if average <= ratio * peak_share:
            return {
                "year": year,
                "avg_share": round(average, 8),
                "peak_share": round(peak_share, 8),
                "ratio": round(average / peak_share, 4),
            }
    return None


def _gaps(
    active: Iterable[int], years: list[int]
) -> list[tuple[int, int, int | None]]:
    active_set = set(active)
    gaps: list[tuple[int, int, int | None]] = []
    index = 0
    while index < len(years):
        if years[index] in active_set:
            index += 1
            continue
        start_index = index
        while index < len(years) and years[index] not in active_set:
            index += 1
        length = index - start_index
        next_active = years[index] if index < len(years) else None
        gaps.append((years[start_index], length, next_active))
    return gaps


def detect_events(
    concept_id: str,
    name: str,
    counts: dict[int, int],
    total: dict[int, int],
    start: int,
    end: int,
    config: dict[str, Any],
) -> list[Event]:
    """Return lifecycle events for one concept, sorted by year then type."""
    years = _years(start, end)
    yearly_counts = {year: int(counts.get(year, 0)) for year in years}
    total_count = sum(yearly_counts.values())
    if total_count < int(config["min_total_count"]):
        return []

    shares = _shares(yearly_counts, total, start, end)
    events: list[Event] = []

    birth_year = next(
        (year for year in years if yearly_counts[year] >= int(config["birth_min_count"])),
        None,
    )
    if birth_year is None:
        return []
    events.append(
        Event(
            concept_id, name, "birth", birth_year, yearly_counts[birth_year],
            {
                "count": yearly_counts[birth_year],
                "share": round(shares[birth_year], 8),
                "left_censored": birth_year == start,
            },
        )
    )

    burst = _detect_burst(shares, yearly_counts, total, years, config)
    if burst is not None:
        events.append(
            Event(concept_id, name, "burst", burst["year"], burst["z"], burst)
        )

    # Early years have very few papers, so a 5-paper concept can look like a
    # 7% share. Only consider peak years with a large enough corpus.
    min_year_total = int(config.get("min_year_total", 0))
    valid_years = [year for year in years if total.get(year, 0) >= min_year_total]
    if not valid_years:
        events.sort(key=lambda event: (event.year, event.type))
        return events

    peak_year = max(valid_years, key=lambda year: (shares[year], yearly_counts[year]))
    peak_count = yearly_counts[peak_year]
    if peak_count >= int(config["peak_min_count"]):
        events.append(
            Event(
                concept_id, name, "peak", peak_year, shares[peak_year],
                {
                    "count": peak_count,
                    "share": round(shares[peak_year], 8),
                    "prev_share": round(shares.get(peak_year - 1, 0.0), 8),
                    "next_share": round(shares.get(peak_year + 1, 0.0), 8),
                },
            )
        )
    else:
        peak_year = None

    if peak_year is not None:
        decline = _detect_decline(shares, years, peak_year, config)
        if decline is not None:
            events.append(
                Event(
                    concept_id, name, "decline", decline["year"],
                    decline["ratio"], decline,
                )
            )

        active = [
            year for year in years
            if yearly_counts[year] >= int(config["active_min_count"])
        ]
        for gap_start, gap_length, next_active in _gaps(active, years):
            if gap_start <= peak_year:
                continue
            if next_active is None and gap_length >= int(config["death_gap"]):
                events.append(
                    Event(
                        concept_id, name, "death", gap_start, gap_length,
                        {
                            "gap_years": gap_length,
                            "last_active": max(
                                (year for year in active if year < gap_start),
                                default=None,
                            ),
                        },
                    )
                )
            elif next_active is not None and gap_length >= int(config["revival_gap"]):
                events.append(
                    Event(
                        concept_id, name, "dormancy", gap_start, gap_length,
                        {"gap_years": gap_length},
                    )
                )
                events.append(
                    Event(
                        concept_id, name, "revival", next_active,
                        yearly_counts[next_active],
                        {
                            "gap_years": gap_length,
                            "count": yearly_counts[next_active],
                            "share": round(shares[next_active], 8),
                        },
                    )
                )

    events.sort(key=lambda event: (event.year, event.type))
    return events
