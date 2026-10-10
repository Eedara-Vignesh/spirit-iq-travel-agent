"""
tests/test_routes.py
====================
Mocked offline unit tests for routing tools, OpenStreetMap OSRM driving routes,
Places autocomplete (Photon / Open-Meteo), and multi-modal transport comparisons.
Completely offline: 0 external paid requests or Groq quota consumed.
"""

from unittest.mock import MagicMock, patch
import pytest
import requests

from backend.schemas import TransportMode
from backend.services.maps_service import MapsService
from backend.services.places_service import PlacesService
from backend.tools import route_tool
from backend.tools.dijkstra import build_india_transit_graph, dijkstra_shortest_path, find_corridor_routes
from backend.tools.route_tool import compute_route_options
from backend.tools.transport_tool import compare_transport_options


# -----------------------------------------------------------------------------
# 1. Dijkstra & Transit Graph Benchmarks
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# 2. OSRM Road Routing (100% Free / Keyless)
# -----------------------------------------------------------------------------
def test_compute_route_options_with_mocked_osrm_road_routes():
    """Verify compute_route_options computes road routes via OpenStreetMap OSRM without a Maps key."""
    mock_osrm_json = {
        "code": "Ok",
        "routes": [
            {
                "distance": 252100.0,
                "duration": 12600.0,
                "geometry": "mock_osrm_encoded_polyline_abc123",
                "legs": [
                    {
                        "summary": "NH 75 / SH 88",
                        "distance": 252100.0,
                        "duration": 12600.0,
                    }
                ],
            }
        ],
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_osrm_json

    orig_service = route_tool.maps_service
    try:
        route_tool.maps_service = MapsService(api_key="")
        with patch("requests.get", return_value=mock_resp):
            res = compute_route_options(
                origin="Bengaluru",
                destination="Coorg",
                origin_coords={"lat": 12.9716, "lon": 77.5946},
                dest_coords={"lat": 12.3375, "lon": 75.7382},
            )

        assert res.success is True
        assert res.metadata["is_live_maps_data"] is True
        assert "OpenStreetMap" in res.metadata["maps_service_status"]
        assert "OSRM" in res.metadata["maps_service_status"]

        routes = res.data["routes"]
        assert len(routes) >= 1
        r0 = routes[0]
        assert "Road Route: OpenStreetMap via OSRM" in r0["route_name"]
        assert r0["total_distance_km"] == 252.1
        assert r0["estimated_duration_hours"] == 3.5
        assert r0["polyline"] == "mock_osrm_encoded_polyline_abc123"
        assert r0["source"] == "osrm_road"
        # Verify distinction from rail or air
        assert any("distinct" in h.lower() for h in r0["highlights"])
    finally:
        route_tool.maps_service = orig_service


def test_compute_route_options_fallback_when_osrm_offline():
    """Verify compute_route_options produces clear fallback status and Dijkstra routes when OSRM is offline."""
    orig_service = route_tool.maps_service
    try:
        route_tool.maps_service = MapsService(api_key="")
        with patch("requests.get", side_effect=requests.exceptions.Timeout("OSRM connection timeout")):
            res = compute_route_options(origin="Bengaluru", destination="Coorg")

        assert res.success is True
        assert len(res.data["routes"]) >= 1
        assert "fallback" in res.metadata["maps_service_status"].lower()
        assert "Dijkstra" in res.metadata["maps_service_status"]
        assert res.metadata["dijkstra_calculated"] is True
        assert res.metadata["is_live_maps_data"] is False
    finally:
        route_tool.maps_service = orig_service


def test_maps_service_google_error_graceful_fallback_to_osrm():
    """Verify that if an optional Google Maps key fails (e.g. 403 billing error), it seamlessly falls back to OSRM."""
    mock_osrm_json = {
        "code": "Ok",
        "routes": [
            {
                "distance": 560000.0,
                "duration": 36000.0,
                "geometry": "mock_osrm_goa_polyline",
                "legs": [{"summary": "NH 48"}],
            }
        ],
    }

    # Google Routes POST returns 403 (BillingNotEnabled / KeyExpired)
    google_err_resp = MagicMock()
    google_err_resp.status_code = 403

    # OSRM GET returns 200 OK
    osrm_resp = MagicMock()
    osrm_resp.status_code = 200
    osrm_resp.json.return_value = mock_osrm_json

    service = MapsService(api_key="AIzaSyMockKeyWithoutBilling")
    with patch("requests.post", return_value=google_err_resp), \
         patch("requests.get", return_value=osrm_resp):
        res = service.get_route_details(
            origin="Bengaluru",
            destination="Goa",
            origin_coords={"lat": 12.9716, "lon": 77.5946},
            dest_coords={"lat": 15.2993, "lon": 74.1240},
        )

    assert res["success"] is True
    assert res["source"] == "osrm_road"
    assert res["is_live_google_maps"] is False
    assert res["routes"][0]["total_distance_km"] == 560.0


def test_maps_service_osrm_in_memory_caching():
    """Verify that repeated OSRM queries reuse in-memory cache to respect provider rate limits."""
    mock_osrm_json = {
        "code": "Ok",
        "routes": [
            {
                "distance": 150000.0,
                "duration": 10800.0,
                "geometry": "poly_cached_123",
                "legs": [{"summary": "SH 17"}],
            }
        ],
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_osrm_json

    service = MapsService(api_key="")
    with patch("requests.get", return_value=mock_resp) as mock_get:
        # First call: hits network
        res1 = service.get_route_details(
            origin="Bengaluru",
            destination="Mysore",
            origin_coords={"lat": 12.9716, "lon": 77.5946},
            dest_coords={"lat": 12.2958, "lon": 76.6394},
        )
        assert res1["success"] is True
        assert mock_get.call_count == 1

        # Second call: served from in-memory cache
        res2 = service.get_route_details(
            origin="Bengaluru",
            destination="Mysore",
            origin_coords={"lat": 12.9716, "lon": 77.5946},
            dest_coords={"lat": 12.2958, "lon": 76.6394},
        )
        assert res2["success"] is True
        # Request count must remain 1
        assert mock_get.call_count == 1


# -----------------------------------------------------------------------------
# 3. Optional Google Maps Routes API (When Key Is Explicitly Configured)
# -----------------------------------------------------------------------------
def test_compute_route_options_with_mocked_live_google_routes():
    """Verify compute_route_options correctly integrates live Google Routes API output when configured."""
    mock_routes_resp = {
        "routes": [
            {
                "distanceMeters": 248000,
                "duration": "18000s",
                "description": "via NH 75 Express Highway",
                "polyline": {"encodedPolyline": "abcde_live_polyline_test"},
            }
        ]
    }

    mock_http_resp = MagicMock()
    mock_http_resp.status_code = 200
    mock_http_resp.json.return_value = mock_routes_resp

    orig_service = route_tool.maps_service
    try:
        route_tool.maps_service = MapsService(api_key="AIzaSyMockMapsApiKeyForTests12345")
        with patch("requests.post", return_value=mock_http_resp):
            res = compute_route_options(origin="Bengaluru", destination="Coorg")

        assert res.success is True
        assert res.metadata["is_live_maps_data"] is True
        assert "Google Maps live route calculation active" in res.metadata["maps_service_status"]

        routes = res.data["routes"]
        assert len(routes) >= 1
        live_r = routes[0]
        assert "Live Google Route" in live_r["route_name"]
        assert live_r["total_distance_km"] == 248.0
        assert live_r["estimated_duration_hours"] == 5.0
        assert live_r["source"] == "google_routes"
        assert live_r["polyline"] == "abcde_live_polyline_test"
    finally:
        route_tool.maps_service = orig_service


def test_maps_service_directions_api_fallback():
    """Verify fallback from Routes API v2 to Directions API when v2 is unavailable."""
    v2_resp = MagicMock()
    v2_resp.status_code = 404

    dir_resp = MagicMock()
    dir_resp.status_code = 200
    dir_resp.json.return_value = {
        "status": "OK",
        "routes": [
            {
                "summary": "NH 48",
                "legs": [
                    {
                        "distance": {"value": 560000},
                        "duration": {"value": 36000},
                    }
                ],
                "overview_polyline": {"points": "dir_polyline_123"},
            }
        ],
    }

    service = MapsService(api_key="AIzaSyMockMapsApiKey12345")
    with patch("requests.post", return_value=v2_resp), \
         patch("requests.get", return_value=dir_resp):
        res = service.get_route_details("Bengaluru", "Goa")

    assert res["success"] is True
    assert res["is_live_google_maps"] is True
    assert res["source"] == "google_directions_api"
    assert res["routes"][0]["total_distance_km"] == 560.0
    assert res["routes"][0]["estimated_duration_hours"] == 10.0


# -----------------------------------------------------------------------------
# 4. OpenStreetMap Autocomplete (Photon by Komoot) & Geocoding
# -----------------------------------------------------------------------------
def test_places_service_photon_autocomplete_mocked():
    """Verify PlacesService parses Photon OpenStreetMap autocomplete GeoJSON predictions."""
    mock_photon_json = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "coordinates": [73.8567, 18.5204],
                    "type": "Point",
                },
                "properties": {
                    "name": "Pune",
                    "city": "Pune",
                    "state": "Maharashtra",
                    "country": "India",
                    "type": "city",
                    "osm_id": 987654,
                },
            }
        ],
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_photon_json

    service = PlacesService(api_key="")
    # Use a city not in local catalog to exercise Photon branch
    with patch("requests.get", return_value=mock_resp):
        preds = service.get_place_predictions("PunexyzTest")

    assert len(preds) == 1
    assert preds[0]["main_text"] == "Pune"
    assert preds[0]["lat"] == 18.5204
    assert preds[0]["lon"] == 73.8567
    assert preds[0]["source"] == "openstreetmap_photon"


def test_places_service_public_nominatim_is_never_called():
    """Verify that public Nominatim is never invoked for autocomplete queries (strict policy compliance)."""
    service = PlacesService(api_key="")

    with patch("requests.get") as mock_get:
        service.get_place_predictions("Kochi")
        for call_args in mock_get.call_args_list:
            called_url = call_args[0][0] if call_args[0] else ""
            assert "nominatim.openstreetmap.org" not in called_url, "Public Nominatim must never be called for autocomplete"


def test_places_service_attractions_search():
    """Verify PlacesService retrieves attractions from curated catalog or search."""
    service = PlacesService(api_key="")
    attractions = service.search_attractions("Waterfalls", location="Coorg")

    assert len(attractions) >= 1
    assert any("abbey" in a["name"].lower() or "falls" in a["name"].lower() for a in attractions)


def test_places_service_quota_error_and_malformed_handling():
    """Verify safe handling of network errors and non-existent queries without unhandled exceptions."""
    service = PlacesService(api_key="")

    # Network HTTP error
    with patch("requests.get", side_effect=requests.exceptions.HTTPError("429 Too Many Requests")):
        # Query that is not in the curated local catalog
        unknown_preds = service.get_place_predictions("UnknownForeignPlace999XYZ")
        assert unknown_preds == []

    # Connection timeout
    with patch("requests.get", side_effect=requests.exceptions.Timeout("Connection timed out")):
        unknown_coords = service.resolve_coordinates("UnknownForeignPlace999XYZ")
        assert unknown_coords is None
