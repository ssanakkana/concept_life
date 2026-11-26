import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from concept_life.ingest import load_cache  # noqa: E402


class IngestTest(unittest.TestCase):
    def _write_cache(self, directory: Path, concepts: list[dict]) -> None:
        data = {
            "results": [
                {
                    "id": "w1",
                    "title": "A paper",
                    "publication_year": 2020,
                    "concepts": concepts,
                }
            ]
        }
        (directory / "a.json").write_text(json.dumps(data), encoding="utf-8")

    def test_stoplist_filters_concepts(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            self._write_cache(
                cache,
                [
                    {"id": "c1", "display_name": "Machine learning", "level": 2},
                    {"id": "c2", "display_name": "Field (mathematics)", "level": 2},
                ],
            )
            papers = load_cache(cache, stoplist={"field (mathematics)"})
            self.assertEqual(len(papers), 1)
            self.assertEqual(
                [concept.name for concept in papers[0].concepts],
                ["Machine learning"],
            )

    def test_paper_dropped_when_all_concepts_stopped(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            self._write_cache(
                cache,
                [{"id": "c1", "display_name": "Machine learning", "level": 2}],
            )
            papers = load_cache(cache, stoplist={"Machine learning"})
            self.assertEqual(papers, [])


if __name__ == "__main__":
    unittest.main()
