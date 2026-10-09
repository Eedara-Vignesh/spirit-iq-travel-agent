"""
backend/tools/dijkstra.py
=========================
Dijkstra's shortest path algorithm and regional transit network implementation.
Assigned to: Member 3 (Routing, Dijkstra, Transport and Budget)

Calculates optimal highway / rail corridors across real Indian waypoints,
and produces primary and scenic alternative paths.
"""

from __future__ import annotations

import heapq
from typing import Dict, List, Optional, Tuple


class Graph:
    """
    Weighted directed/undirected graph representation for routing.
    """

    def __init__(self) -> None:
        # adjacency list: node -> list of (neighbor, weight)
        self.adjacency: Dict[str, List[Tuple[str, float]]] = {}

    def add_edge(self, u: str, v: str, weight: float, bidirectional: bool = True) -> None:
        """Add a weighted edge between node u and node v."""
        if weight < 0:
            raise ValueError(f"Edge weight cannot be negative: {weight}")
        u_norm = u.strip().title()
        v_norm = v.strip().title()
        if u_norm not in self.adjacency:
            self.adjacency[u_norm] = []
        if v_norm not in self.adjacency:
            self.adjacency[v_norm] = []
        self.adjacency[u_norm].append((v_norm, weight))
        if bidirectional:
            self.adjacency[v_norm].append((u_norm, weight))

    def get_nodes(self) -> List[str]:
        return list(self.adjacency.keys())


def dijkstra_shortest_path(
    graph: Graph,
    start_node: str,
    end_node: str,
    avoid_edge: Optional[Tuple[str, str]] = None,
) -> Tuple[Optional[List[str]], float]:
    """
    Compute shortest path and total distance between start_node and end_node.

    Returns:
        (path, total_weight) where path is a list of node names from start to end,
        or (None, float('inf')) if no path exists.
    """
    start = start_node.strip().title()
    end = end_node.strip().title()

    if start not in graph.adjacency or end not in graph.adjacency:
        return None, float("inf")

    if start == end:
        return [start], 0.0

    # min-heap priority queue: (cumulative_distance, current_node)
    pq: List[Tuple[float, str]] = [(0.0, start)]
    distances: Dict[str, float] = {node: float("inf") for node in graph.adjacency}
    distances[start] = 0.0
    previous_nodes: Dict[str, Optional[str]] = {node: None for node in graph.adjacency}

    while pq:
        current_distance, current_node = heapq.heappop(pq)

        if current_node == end:
            break

        if current_distance > distances[current_node]:
            continue

        for neighbor, weight in graph.adjacency.get(current_node, []):
            # Check edge avoidance if computing alternative routes
            if avoid_edge:
                if (current_node == avoid_edge[0] and neighbor == avoid_edge[1]) or (
                    current_node == avoid_edge[1] and neighbor == avoid_edge[0]
                ):
                    continue

            distance = current_distance + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous_nodes[neighbor] = current_node
                heapq.heappush(pq, (distance, neighbor))

    if distances[end] == float("inf"):
        return None, float("inf")

    # Reconstruct path backwards from end
    path: List[str] = []
    curr: Optional[str] = end
    while curr is not None:
        path.append(curr)
        curr = previous_nodes[curr]
    path.reverse()

    return path, distances[end]


def build_india_transit_graph() -> Graph:
    """
    Build calibrated graph of major Indian travel corridors with actual highway distances in km.
    """
    g = Graph()

    # Southern Heritage & Hills Corridor
    g.add_edge("Bengaluru", "Mysore", 145.0)
    g.add_edge("Mysore", "Coorg", 120.0)
    g.add_edge("Bengaluru", "Coorg", 250.0)  # via Hassan
    g.add_edge("Mysore", "Ooty", 125.0)     # via Bandipur
    g.add_edge("Mysore", "Wayanad", 115.0)  # via Gundlupet
    g.add_edge("Ooty", "Coimbatore", 85.0)
    g.add_edge("Wayanad", "Kozhikode", 85.0)
    g.add_edge("Bengaluru", "Chennai", 350.0)
    g.add_edge("Bengaluru", "Hyderabad", 570.0)
    g.add_edge("Bengaluru", "Goa", 560.0)

    # Western Corridor
    g.add_edge("Mumbai", "Lonavala", 85.0)
    g.add_edge("Lonavala", "Pune", 65.0)
    g.add_edge("Pune", "Mahabaleshwar", 120.0)
    g.add_edge("Pune", "Goa", 440.0)
    g.add_edge("Mumbai", "Goa", 580.0)  # Coastal NH66

    # Northern Golden Triangle & Rajasthan Corridor
    g.add_edge("Delhi", "Agra", 230.0)      # Yamuna Expressway
    g.add_edge("Delhi", "Jaipur", 280.0)    # NH48
    g.add_edge("Agra", "Jaipur", 240.0)     # NH21 via Bharatpur
    g.add_edge("Jaipur", "Pushkar", 145.0)
    g.add_edge("Jaipur", "Jodhpur", 330.0)
    g.add_edge("Pushkar", "Jodhpur", 185.0)
    g.add_edge("Jodhpur", "Udaipur", 250.0)  # via Ranakpur
    g.add_edge("Jaipur", "Udaipur", 395.0)   # via Chittorgarh
    g.add_edge("Delhi", "Chandigarh", 245.0)
    g.add_edge("Chandigarh", "Shimla", 110.0)
    g.add_edge("Chandigarh", "Manali", 270.0)
    g.add_edge("Delhi", "Manali", 515.0)

    return g


def find_corridor_routes(
    origin: str,
    destination: str,
) -> List[Dict[str, Any]]:
    """
    Query calibrated graph for shortest path and scenic alternative paths using Dijkstra.
    Returns list of route descriptions with distance, waypoints, and algorithm notes.
    """
    g = build_india_transit_graph()
    routes: List[Dict[str, Any]] = []

    # 1. Primary shortest path
    primary_path, primary_dist = dijkstra_shortest_path(g, origin, destination)
    if primary_path and primary_dist < float("inf"):
        routes.append({
            "route_name": f"Optimal Path: {' → '.join(primary_path)}",
            "via_waypoints": primary_path[1:-1] if len(primary_path) > 2 else [],
            "total_distance_km": primary_dist,
            "estimated_duration_hours": round(primary_dist / 60.0, 1),  # ~60 km/h average highway transit
            "highlights": [f"Direct corridor via {', '.join(primary_path[1:-1])}" if len(primary_path) > 2 else "Direct highway express route"],
            "algorithm_notes": "Computed via Dijkstra shortest path algorithm on calibrated regional road network graph.",
        })

        # 2. Compute alternative route by penalizing first intermediate edge
        if len(primary_path) >= 3:
            first_edge = (primary_path[0], primary_path[1])
            alt_path, alt_dist = dijkstra_shortest_path(g, origin, destination, avoid_edge=first_edge)
            if alt_path and alt_dist < float("inf") and alt_path != primary_path:
                routes.append({
                    "route_name": f"Alternative Scenic Route: {' → '.join(alt_path)}",
                    "via_waypoints": alt_path[1:-1],
                    "total_distance_km": alt_dist,
                    "estimated_duration_hours": round(alt_dist / 55.0, 1),
                    "highlights": [f"Scenic detour bypassing {first_edge[1]}"],
                    "algorithm_notes": "Alternative route computed by Dijkstra edge-penalty heuristic.",
                })

    return routes
