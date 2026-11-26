import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    import pandas as pd
    from concept_life.dashboard import (
        concept_events,
        concept_options,
        event_counts,
        review_precision,
        timeline,
    )
except ImportError:
    pd = None


@unittest.skipIf(pd is None, "pandas is only installed in the uv environment")
class DashboardTest(unittest.TestCase):
    def test_timeline_fills_missing_years(self):
        series = pd.DataFrame(
            [
                {"concept_id": "c", "name": "Demo", "year": 2000, "count": 2, "share": 0.02},
                {"concept_id": "c", "name": "Demo", "year": 2002, "count": 3, "share": 0.03},
            ]
        )
        frame = timeline(series, "c", start=2000, end=2002)
        self.assertEqual(list(frame["year"]), [2000, 2001, 2002])
        self.assertEqual(list(frame["count"]), [2, 0, 3])
        self.assertAlmostEqual(float(frame.loc[1, "share"]), 0.0)

    def test_concept_options_sorted_by_total(self):
        series = pd.DataFrame(
            [
                {"concept_id": "a", "name": "Small", "year": 2000, "count": 1, "share": 0.01},
                {"concept_id": "b", "name": "Big", "year": 2000, "count": 9, "share": 0.09},
            ]
        )
        options = concept_options(series, limit=2)
        self.assertEqual([name for _, name in options], ["Big", "Small"])

    def test_review_precision_ignores_unlabeled(self):
        review = pd.DataFrame(
            [
                {"rank": 1, "valid_1_0": 1},
                {"rank": 2, "valid_1_0": 0},
                {"rank": 3, "valid_1_0": None},
                {"rank": 11, "valid_1_0": 1},
            ]
        )
        metrics = review_precision(review, 10)
        self.assertEqual(metrics["labeled"], 2)
        self.assertEqual(metrics["total"], 3)
        self.assertAlmostEqual(metrics["precision"], 0.5)

    def test_event_counts_and_filter(self):
        events = pd.DataFrame(
            [
                {"concept_id": "a", "type": "birth", "year": 2000, "score": 1},
                {"concept_id": "a", "type": "peak", "year": 2005, "score": 2},
                {"concept_id": "b", "type": "birth", "year": 2001, "score": 1},
            ]
        )
        counts = event_counts(events).set_index("type")["events"].to_dict()
        self.assertEqual(counts, {"birth": 2, "peak": 1})
        filtered = concept_events(events, "a")
        self.assertEqual(list(filtered["type"]), ["birth", "peak"])


if __name__ == "__main__":
    unittest.main()
