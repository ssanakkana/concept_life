import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from concept_life.predict import (  # noqa: E402
    build_features,
    ndcg_at_k,
    precision_at_k,
)


class PredictTest(unittest.TestCase):
    def test_precision_and_ndcg(self):
        scores = np.array([0.9, 0.8, 0.7, 0.6, 0.5])
        labels = np.array([1.0, 0.0, 1.0, 0.0, 0.0])
        self.assertAlmostEqual(precision_at_k(scores, labels, 2), 0.5)
        self.assertGreater(ndcg_at_k(scores, labels, 2), 0.5)

    def test_features_do_not_use_future_years(self):
        totals = {year: 100 for year in range(2000, 2021)}
        counts = {2000: 1, 2001: 2, 2002: 3, 2003: 4, 2004: 5,
                  2005: 6, 2006: 7, 2007: 8, 2008: 9, 2009: 10, 2010: 11}
        base = {"c": dict(counts)}
        with_future = {"c": {**counts, 2015: 999}}
        config = {"start_year": 2000, "min_total_count_T": 1}
        ids_a, features_a = build_features(
            base, totals, {}, {}, 2010, config
        )
        ids_b, features_b = build_features(
            with_future, totals, {}, {}, 2010, config
        )
        self.assertEqual(ids_a, ids_b)
        np.testing.assert_allclose(features_a, features_b)


if __name__ == "__main__":
    unittest.main()
