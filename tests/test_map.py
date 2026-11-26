import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    import networkx as nx
    from concept_life.community import bridge_scores, detect_communities
except ImportError:
    nx = None


@unittest.skipIf(nx is None, "networkx is only installed in the uv environment")
class CommunityTest(unittest.TestCase):
    def test_louvain_finds_two_blocks(self):
        graph = nx.Graph()
        for start in (0, 4):
            for left in range(start, start + 4):
                for right in range(left + 1, start + 4):
                    graph.add_edge(left, right, weight=5)
        graph.add_edge(0, 4, weight=1)
        mapping, communities, modularity = detect_communities(graph, seed=42)
        self.assertEqual(len(communities), 2)
        self.assertGreater(modularity, 0.3)
        self.assertNotEqual(mapping[0], mapping[4])

    def test_bridge_node_has_highest_betweenness(self):
        graph = nx.Graph()
        for start in (0, 4):
            for left in range(start, start + 4):
                for right in range(left + 1, start + 4):
                    graph.add_edge(left, right, weight=5)
        graph.add_edge(0, 4, weight=1)
        scores = bridge_scores(graph)
        self.assertEqual(max(scores, key=scores.get) in {0, 4}, True)


if __name__ == "__main__":
    unittest.main()
