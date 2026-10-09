"""
tests/test_routes.py
====================
Unit tests for routing tools, Dijkstra corridor computation, and transport options.
"""

from backend.tools.dijkstra import build_india_transit_graph, dijkstra_shortest_path, find_corridor_routes
from backend.tools.route_tool import compute_route_options
from backend.tools.transport_tool import compare_transport_options
from backend.schemas import TransportMode


def test_dijkstra_calibrated_graph_path():
    """Verify Dijkstra finds shortest path on calibrated Indian transit corridors."""
    g = build_india_transit_graph()

    # Bengaluru to Coorg: Direct via Hassan (250km) vs via Mysore (145 + 120 = 265km)
    path, dist = dijkstra_shortest_path(g, "Bengaluru", "Coorg")
    assert path is not None
    assert dist == 250.0  # Hassan route is shortest (250km vs 265km)
    assert path[0] == "Bengaluru"
    assert path[-1] == "Coorg"


def test_find_corridor_alternative_routes():
    """Verify alternative scenic route calculation."""
    # Delhi to Udaipur has alternative paths in the graph
    routes = find_corridor_routes("Delhi", "Udaipur")
    assert len(routes) >= 1
    assert routes[0]["total_distance_km"] > 0
    assert "Optimal Path" in routes[0]["route_name"]


def test_compare_transport_options():
    """Verify multi-modal transit comparison returns Flight, Train, Bus, Cab options."""
    res = compare_transport_options(
        origin="Bengaluru",
        destination="Goa",
        distance_km=560.0,
        preferences=[TransportMode.ANY],
        num_travellers=2,
    )

    assert res.success is True
    opts = res.data["transport_options"]
    modes = [o["mode"] for o in opts]
    assert "flight" in modes
    assert "train" in modes
    assert "bus" in modes
    assert "cab" in modes

    # Fares must be positive and benchmarked
    for opt in opts:
        assert opt["estimated_cost_inr"] > 0
        assert opt["duration_hours"] > 0
