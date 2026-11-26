import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from concept_life.early import (  # noqa: E402
    accuracy,
    build_early_rows,
    macro_f1,
    predict_proba,
    standardize,
    train_softmax,
)


class EarlyTest(unittest.TestCase):
    def test_early_features_ignore_future_years(self):
        totals = {year: 100 for year in range(1995, 2024)}
        base = {"c": {2000: 5, 2001: 8, 2002: 12}}
        with_future = {"c": {2000: 5, 2001: 8, 2002: 12, 2010: 999}}
        clusters = [
            {
                "concept_id": "c",
                "name": "Demo",
                "first_year": "2000",
                "label": "DemoType",
            }
        ]
        rows_a = build_early_rows(base, totals, clusters, max_birth_year=2018)
        rows_b = build_early_rows(with_future, totals, clusters, max_birth_year=2018)
        self.assertEqual(rows_a, rows_b)

    def test_softmax_learns_three_blobs(self):
        rng = np.random.default_rng(0)
        matrix = np.vstack(
            [
                rng.normal(0, 0.3, (30, 2)),
                rng.normal(3, 0.3, (30, 2)),
                rng.normal(6, 0.3, (30, 2)),
            ]
        )
        labels = np.array([0] * 30 + [1] * 30 + [2] * 30)
        matrix, _mean, _std = standardize(matrix)
        weights, bias = train_softmax(matrix, labels, 3, l2=0.0, lr=0.1, epochs=2000)
        predicted = np.argmax(predict_proba(matrix, weights, bias), axis=1)
        self.assertGreater(accuracy(labels, predicted), 0.9)

    def test_macro_f1(self):
        labels = np.array([0, 1, 2, 0, 1, 2])
        self.assertAlmostEqual(macro_f1(labels, labels, 3), 1.0)
        predicted = np.array([0, 0, 2, 0, 1, 2])
        self.assertLess(macro_f1(labels, predicted, 3), 1.0)
        self.assertGreater(macro_f1(labels, predicted, 3), 0.5)


if __name__ == "__main__":
    unittest.main()
