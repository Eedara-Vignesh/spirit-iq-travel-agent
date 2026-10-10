"""
backend/tools/route_tool.py
===========================
Route and itinerary path optimization tool.
Assigned to: Member 3 (Routing, Dijkstra, Transport and Budget)

Generates main routes and alternate paths between origins, destinations, and waypoints
using OpenStreetMap / OSRM, Dijkstra's algorithm, and optional Google Maps Routes.
Clearly distinguishes road transit corridors from scheduled rail, bus, and flight services.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from backend.schemas import AlternateRoute, ToolResult
from backend.services.maps_service import MapsService
from backend.tools.dijkstra import find_corridor_routes

maps_service = MapsService()


def compute_route_options(
    origin: str,
    destination: str,
    waypoints: Optional[List[str]] = None,
    origin_coords: Optional[Dict[str, float]] = None,
    dest_coords: Optional[Dict[str, float]] = None,
) -> ToolResult:
    """
    Compute primary and alternative routes between origin and destination.
    Uses OpenStreetMap OSRM road routing engine (or Google Routes when configured),
    and gracefully falls back to calibrated Dijkstra regional corridor network.
    Clearly marks routes as road transit (distinct from scheduled train or air services).
    """
    if not origin or not origin.strip() or not destination or not destination.strip():
        return ToolResult.fail("Origin and destination are required for route calculations.")

    waypoints = waypoints or []

    # 1. Dijkstra graph computation on regional highway network
    graph_routes = find_corridor_routes(origin, destination)

    result_routes: List[AlternateRoute] = []

    # 2. Query road route details (OSRM or Google Maps Routes)
    live_res = maps_service.get_route_details(
        origin=origin,
        destination=destination,
        waypoints=waypoints,
        origin_coords=origin_coords,
        dest_coords=dest_coords,
    )

    if live_res.get("success") and live_res.get("routes"):
        is_osrm = live_res.get("source") == "osrm_road"
        for gr in live_res["routes"]:
            summary_label = gr.get("summary") or f"{origin} → {destination}"
            if is_osrm:
                r_name = f"Road Route: OpenStreetMap via OSRM ({summary_label})"
                algo_notes = (
                    "OpenStreetMap OSRM Road Routing Engine. "
                    "Note: Road routes represent highway driving trajectories and are distinct "
                    "from scheduled rail, bus, and flight services."
                )
                r_highlights = [
                    "Real-time road corridor calculated via OpenStreetMap / OSRM",
                    "Highway transit (Car / Taxi / Bus corridor) — distinct from scheduled rail or air",
                ]
                r_source = "osrm_road"
            else:
                r_name = f"Live Google Route ({summary_label})"
                algo_notes = "Live Google Routes API (Real-time road network & travel duration)"
                r_highlights = ["Live traffic-optimized road navigation (Google Maps Platform)"]
                r_source = gr.get("source") or "google_routes"

            result_routes.append(
                AlternateRoute(
                    route_name=r_name,
                    via_waypoints=gr.get("via_waypoints", waypoints),
                    total_distance_km=gr.get("total_distance_km"),
                    estimated_duration_hours=gr.get("estimated_duration_hours"),
                    highlights=r_highlights,
                    algorithm_notes=algo_notes,
                    polyline=gr.get("polyline"),
                    source=r_source,
                )
            )

        # Append Dijkstra corridor as calibrated scenic alternate if available
        if graph_routes:
            r = graph_routes[0]
            result_routes.append(
                AlternateRoute(
                    route_name=f"Dijkstra Highway Corridor ({r['route_name']})",
                    via_waypoints=r["via_waypoints"],
                    total_distance_km=r["total_distance_km"],
                    estimated_duration_hours=r["estimated_duration_hours"],
                    highlights=r["highlights"],
                    algorithm_notes=r["algorithm_notes"],
                    source="dijkstra_graph",
                )
            )

        status_label = (
            "OpenStreetMap OSRM live road route calculation active"
            if is_osrm
            else "Google Maps live route calculation active"
        )
        return ToolResult.ok(
            data={"routes": [r.model_dump() for r in result_routes]},
            metadata={
                "tool": "route_tool",
                "maps_service_status": status_label,
                "is_live_maps_data": True,
                "dijkstra_calculated": bool(graph_routes),
            },
        )

    # If live request was not successful, signal fallback and assemble Dijkstra routes
    fallback_msg = live_res.get("error") or live_res.get("message") or "service unavailable"
    maps_status = f"Road routing fallback: using calibrated Dijkstra estimates ({fallback_msg})"

    # 3. Dijkstra Fallback Assembly
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
                    source="dijkstra_graph",
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
                source="dijkstra_graph",
            )
        )

    return ToolResult.ok(
        data={"routes": [r.model_dump() for r in result_routes]},
        metadata={
            "tool": "route_tool",
            "maps_service_status": maps_status,
            "is_live_maps_data": False,
            "dijkstra_calculated": bool(graph_routes),
        },
    )
