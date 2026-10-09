"""
backend/tools/route_tool.py
===========================
Route and itinerary path optimization tool.
Assigned to: Member 3 (Routing, Dijkstra, Transport and Budget)

Generates main routes and alternate paths between origins, destinations, and waypoints
using Dijkstra's algorithm and Google Maps Routes (when configured).
"""

from __future__ import annotations

from typing import List, Optional
from backend.schemas import AlternateRoute, ToolResult
from backend.services.maps_service import MapsService
from backend.tools.dijkstra import find_corridor_routes

maps_service = MapsService()


def compute_route_options(
    origin: str,
    destination: str,
    waypoints: Optional[List[str]] = None,
) -> ToolResult:
    """
    Compute primary and alternative routes between origin and destination.
    Uses Dijkstra on regional transit corridors, and labels live Maps data status.
    """
    waypoints = waypoints or []

    # 1. Dijkstra graph computation on regional highway network
    graph_routes = find_corridor_routes(origin, destination)

    result_routes: List[AlternateRoute] = []

    if graph_routes:
        for r in graph_routes:
            result_routes.append(
                AlternateRoute(
                    route_name=r["route_name"],
                    via_waypoints=r["via_waypoints"],
                    total_distance_km=r["total_distance_km"],
                    estimated_duration_hours=r["estimated_duration_hours"],
                    highlights=r["highlights"],
                    algorithm_notes=r["algorithm_notes"],
                )
            )
    else:
        # Default estimated intercity route when nodes are outside calibrated graph
        result_routes.append(
            AlternateRoute(
                route_name=f"Standard Intercity Corridor ({origin} → {destination})",
                via_waypoints=waypoints,
                highlights=["Major national highway / standard transit corridor"],
                algorithm_notes="Standard estimate (Direct Dijkstra node not in pre-calibrated regional graph).",
            )
        )

    # 2. Check Maps service status
    has_maps_key = bool(maps_service.api_key and maps_service.api_key.strip())
    maps_status = "Google Maps API live integration ready" if has_maps_key else "Google Maps API key not configured (using calibrated Dijkstra estimates)"

    return ToolResult.ok(
        data={"routes": [r.model_dump() for r in result_routes]},
        metadata={
            "tool": "route_tool",
            "maps_service_status": maps_status,
            "dijkstra_calculated": bool(graph_routes),
        },
    )
