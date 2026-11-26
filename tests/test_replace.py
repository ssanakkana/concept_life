import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from concept_life.replace import detect_replacements, jaccard, pearson  # noqa: E402


class ReplaceTest(unittest.TestCase):
    def test_pearson_detects_opposite_trends(self):
        left = [5, 4, 3, 2, 1]
        right = [1, 2, 3, 4, 5]
        self.assertLess(pearson(left, right), -0.9)

    def test_jaccard(self):
        self.assertAlmostEqual(jaccard(10, 20, 30), 0.25)
        self.assertEqual(jaccard(0, 0, 0), 0.0)

    def test_synthetic_replacement(self):
        years = list(range(2000, 2021))
        old = {year: max(1, 50 - 2 * (year - 2005)) if year >= 2005 else year - 1995
               for year in years}
        new = {year: 0 if year < 2008 else (year - 2007) * 3 for year in years}
        series = {"old": old, "new": new}
        totals = {year: 100 for year in years}
        support = {("new", "old"): 10}
        config = {
            "start_year": 2000,
            "end_year": 2020,
            "neighbor_top_k": 10,
            "min_jaccard": 0.01,
            "min_overlap_years": 5,
            "top_k_per_old": 10,
            "max_candidates": 10,
        }
        rows = detect_replacements(
            series,
            totals,
            support,
            decline_ids={"old"},
            peak_years={"old": 2005},
            rising_ids={"new"},
            new_years={"new": 2008},
            config=config,
        )
        self.assertTrue(rows)
        self.assertEqual(rows[0]["old_id"], "old")
        self.assertEqual(rows[0]["new_id"], "new")
        self.assertLess(rows[0]["correlation"], 0)


if __name__ == "__main__":
    unittest.main()
