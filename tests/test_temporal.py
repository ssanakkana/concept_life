import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from concept_life.rising import rising_table, window_share  # noqa: E402


class TemporalTest(unittest.TestCase):
    def test_window_share_is_corpus_normalized(self):
        series = {2015: 10, 2016: 10, 2018: 20, 2019: 20}
        total = {2015: 100, 2016: 100, 2018: 200, 2019: 200}
        self.assertAlmostEqual(window_share(series, [2015, 2016], total), 0.1)
        self.assertAlmostEqual(window_share(series, [2018, 2019], total), 0.1)

    def test_growth_does_not_reward_corpus_growth_alone(self):
        series = {"a": {2015: 10, 2016: 10, 2018: 20, 2019: 20}}
        total = {2015: 100, 2016: 100, 2018: 200, 2019: 200}
        rows = rising_table(
            series, {"a": "a"}, total, [2015, 2016], [2018, 2019],
            min_curr_count=1, top_k=10,
        )
        self.assertAlmostEqual(rows[0]["growth"], 1.0)
        self.assertAlmostEqual(rows[0]["delta_share"], 0.0)

    def test_new_concept_has_no_growth_ratio(self):
        series = {"a": {2018: 10, 2019: 10}}
        total = {2018: 100, 2019: 100}
        rows = rising_table(
            series, {"a": "a"}, total, [2015, 2016], [2018, 2019],
            min_curr_count=1, top_k=10,
        )
        self.assertTrue(rows[0]["is_new"])
        self.assertIsNone(rows[0]["growth"])

    def test_rising_table_drops_low_count_concepts(self):
        series = {
            "a": {2018: 1, 2019: 1},
            "b": {2018: 10, 2019: 10},
        }
        total = {2018: 100, 2019: 100}
        rows = rising_table(
            series, {"a": "a", "b": "b"}, total, [2018], [2019],
            min_curr_count=5, top_k=10,
        )
        self.assertEqual([row["concept_id"] for row in rows], ["b"])


if __name__ == "__main__":
    unittest.main()
