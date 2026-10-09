"""
tests/test_dijkstra.py
======================
Unit tests for Dijkstra shortest path algorithm in backend/tools/dijkstra.py.
Assigned to: Member 3 (Routing, Dijkstra, Transport and Budget)
Compatible with both pytest and python -m unittest.
"""

import unittest
from backend.tools.dijkstra import Graph, dijkstra_shortest_path


class TestDijkstra(unittest.TestCase):

    def test_dijkstra_simple_path(self):
        graph = Graph()
        graph.add_edge("A", "B", 4.0)
        graph.add_edge("A", "C", 2.0)
        graph.add_edge("C", "B", 1.0)
        graph.add_edge("B", "D", 5.0)
        graph.add_edge("C", "D", 8.0)

        path, distance = dijkstra_shortest_path(graph, "A", "D")

        # Shortest path: A -> C (2) -> B (1) -> D (5) = 8.0
        self.assertEqual(path, ["A", "C", "B", "D"])
        self.assertEqual(distance, 8.0)

    def test_dijkstra_same_node(self):
        graph = Graph()
        graph.add_edge("Delhi", "Agra", 200.0)

        path, distance = dijkstra_shortest_path(graph, "Delhi", "Delhi")
        self.assertEqual(path, ["Delhi"])
        self.assertEqual(distance, 0.0)

    def test_dijkstra_disconnected_nodes(self):
        graph = Graph()
        graph.add_edge("A", "B", 10.0)
        graph.add_edge("C", "D", 15.0)

        path, distance = dijkstra_shortest_path(graph, "A", "D")
        self.assertIsNone(path)
        self.assertEqual(distance, float("inf"))

    def test_dijkstra_negative_edge_rejected(self):
        graph = Graph()
        with self.assertRaises(ValueError):
            graph.add_edge("A", "B", -5.0)


if __name__ == "__main__":
    unittest.main()
