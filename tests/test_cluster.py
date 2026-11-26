import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from concept_life.cluster import (  # noqa: E402
    build_feature_rows,
    kmeans,
    silhouette_from_distance,
    standardize,
)


class ClusterTest(unittest.TestCase):
    def test_kmeans_separates_two_blobs(self):
        rng = np.random.default_rng(0)
        matrix = np.vstack(
            [rng.normal(0, 0.3, (20, 2)), rng.normal(5, 0.3, (20, 2))]
        )
        matrix = standardize(matrix)
        labels, _centers, _inertia = kmeans(matrix, 2, seed=1, n_init=5)
        self.assertEqual(len(set(labels[:20])), 1)
        self.assertEqual(len(set(labels[20:])), 1)
        self.assertNotEqual(labels[0], labels[20])

    def test_silhouette_separates_two_blobs(self):
        rng = np.random.default_rng(0)
        matrix = np.vstack(
            [rng.normal(0, 0.3, (20, 2)), rng.normal(5, 0.3, (20, 2))]
        )
        matrix = standardize(matrix)
        labels = np.array([0] * 20 + [1] * 20)
        distance = np.sqrt(
            ((matrix[:, None, :] - matrix[None, :, :]) ** 2).sum(axis=2)
        )
        self.assertGreater(silhouette_from_distance(distance, labels), 0.7)

    def test_flash_features(self):
        series = {
            "c": {
                1995: 1, 1996: 5, 1997: 10, 1998: 8,
                1999: 6, 2000: 4, 2001: 2, 2002: 1,
            }
        }
        totals = {year: 100 for year in range(1995, 2024)}
        rows = build_feature_rows(
            series,
            {"c": "Demo"},
            totals,
            [],
            start_year=1995,
            end_year=2023,
            min_total_count=20,
            active_min_count=3,
            min_year_total=100,
        )
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertGreater(row["decline_speed"], 0.8)
        self.assertLess(row["peak_position"], 0.3)
        self.assertEqual(row["revival_flag"], 0)


if __name__ == "__main__":
    unittest.main()
