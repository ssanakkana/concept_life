import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from concept_life.ingest import matches_domain  # noqa: E402
from concept_life.schema import parse_work  # noqa: E402


class SchemaTest(unittest.TestCase):
    def test_filters_level_and_applies_top_k(self):
        work = {
            "id": "w1",
            "title": "A paper",
            "publication_year": 2020,
            "concepts": [
                {"id": "c0", "display_name": "Computer science", "level": 0, "score": 0.9},
                {"id": "c2", "display_name": "Machine learning", "level": 2, "score": 0.5},
                {"id": "c3", "display_name": "Deep learning", "level": 3, "score": 0.4},
            ],
        }
        paper = parse_work(work, top_k=1, min_level=2)
        self.assertIsNotNone(paper)
        self.assertEqual(len(paper.concepts), 1)
        self.assertEqual(paper.concepts[0].id, "c2")
        self.assertEqual(paper.year, 2020)

    def test_rejects_missing_year(self):
        work = {"id": "w1", "title": "x", "concepts": [{"id": "c", "display_name": "x", "level": 3}]}
        self.assertIsNone(parse_work(work))

    def test_rejects_paper_without_usable_concepts(self):
        work = {
            "id": "w1",
            "title": "x",
            "publication_year": 2020,
            "concepts": [{"id": "c0", "display_name": "Computer science", "level": 0}],
        }
        self.assertIsNone(parse_work(work, min_level=2))

    def test_extracts_topic_fields(self):
        work = {
            "id": "w1",
            "title": "x",
            "publication_year": 2020,
            "concepts": [{"id": "c2", "display_name": "Machine learning", "level": 2}],
            "topics": [
                {
                    "domain": {"display_name": "Computer Science"},
                    "field": {"display_name": "Artificial Intelligence"},
                    "subfield": {"display_name": "Machine Learning"},
                }
            ],
        }
        paper = parse_work(work)
        self.assertIsNotNone(paper)
        self.assertEqual(
            paper.fields,
            ("Artificial Intelligence", "Computer Science", "Machine Learning"),
        )

    def test_domain_filter(self):
        work = {
            "id": "w1",
            "title": "x",
            "publication_year": 2020,
            "concepts": [{"id": "c2", "display_name": "Machine learning", "level": 2}],
            "topics": [{"domain": {"display_name": "Computer Science"}}],
        }
        paper = parse_work(work)
        self.assertTrue(matches_domain(paper, "computer science"))
        self.assertFalse(matches_domain(paper, "medicine"))

        unknown = parse_work(
            {"id": "w2", "title": "y", "publication_year": 2020,
             "concepts": [{"id": "c2", "display_name": "Machine learning", "level": 2}]}
        )
        self.assertTrue(matches_domain(unknown, "computer science", keep_unknown=True))
        self.assertFalse(matches_domain(unknown, "computer science", keep_unknown=False))


if __name__ == "__main__":
    unittest.main()
