import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from concept_life.mine import detect_events  # noqa: E402


CONFIG = {
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
    "death_gap": 2,
    "revival_gap": 2,
}


class MineTest(unittest.TestCase):
    def test_full_lifecycle(self):
        counts = {
            2000: 1, 2001: 3, 2002: 5, 2003: 6, 2004: 8,
            2005: 50, 2006: 30, 2007: 10, 2008: 5,
            2009: 1, 2010: 0, 2011: 0, 2012: 0,
        }
        total = {year: 100 for year in range(1995, 2024)}
        events = detect_events("c1", "Demo", counts, total, 1995, 2023, CONFIG)
        by_type = {event.type: event for event in events}
        self.assertEqual(by_type["birth"].year, 2000)
        self.assertEqual(by_type["burst"].year, 2005)
        self.assertEqual(by_type["peak"].year, 2005)
        self.assertEqual(by_type["decline"].year, 2006)
        self.assertEqual(by_type["death"].year, 2009)

    def test_dormancy_and_revival(self):
        counts = {
            2000: 5, 2001: 8, 2002: 10, 2003: 8, 2004: 6,
            2005: 2, 2006: 0, 2007: 0, 2008: 3, 2009: 4, 2010: 6,
            2011: 5, 2012: 4, 2013: 4, 2014: 3, 2015: 3, 2016: 2,
            2017: 2, 2018: 2, 2019: 2, 2020: 2, 2021: 2, 2022: 2, 2023: 2,
        }
        total = {year: 100 for year in range(1995, 2024)}
        events = detect_events("c2", "Demo", counts, total, 1995, 2023, CONFIG)
        by_type = {event.type: event for event in events}
        self.assertEqual(by_type["dormancy"].year, 2006)
        self.assertEqual(by_type["revival"].year, 2008)
        self.assertNotIn("death", by_type)

    def test_short_series_is_skipped(self):
        counts = {2000: 1, 2001: 1}
        total = {year: 100 for year in range(1995, 2024)}
        events = detect_events("c3", "Tiny", counts, total, 1995, 2023, CONFIG)
        self.assertEqual(events, [])


if __name__ == "__main__":
    unittest.main()
