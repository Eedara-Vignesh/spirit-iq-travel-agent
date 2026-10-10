"""
backend/services/maps_service.py
================================
OpenStreetMap / OSRM and Google Maps Routes service integration.
Assigned to: Member 3 (Routing, Dijkstra, Transport and Budget)

Provides road route calculation (distance, driving duration, and encoded polylines).
Primary Engine: OpenStreetMap road routing via OSRM (100% free, keyless, open data).
Optional Override: Google Maps Routes API (ComputeRoutes v2 / Directions API) if key is present.
Baseline Engine: Dijkstra shortest-path highway graph when offline or unconfigured.

NOTE: Road routing represents highway and driving corridors only.
Train schedules, flight services, and ticket prices are handled distinctly by
SpiritIQ's transit benchmarks and official booking handoffs (IRCTC, MakeMyTrip, RedBus).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
import requests

from backend.config import get_settings, mask_secret, sanitize_text
from backend.services.places_service import places_service

logger = logging.getLogger(__name__)

DEFAULT_OSRM_USER_AGENT = "SpiritIQ-Travel-Agent/1.0 (OpenStreetMap Road Routing; hackathon-build)"


class MapsService:
    """
    Service client for OpenStreetMap (OSRM) road routing with optional Google Maps integration.
    Fully operates without a paid Google Maps API key or billing account.
    """

    OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"
    ROUTES_API_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
    DIRECTIONS_API_URL = "https://maps.googleapis.com/maps/api/directions/json"

    def __init__(self, api_key: Optional[str] = None, timeout: float = 4.5) -> None:
        self.settings = get_settings()
        self._explicit_key = api_key
        self.timeout = timeout
        self._route_cache: Dict[str, List[Dict[str, Any]]] = {}

    @property
    def api_key(self) -> Optional[str]:
        """Dynamically read configured Google Maps API key from settings or explicit override."""
        if self._explicit_key is not None:
            return self._explicit_key
        return self.settings.google_maps_api_key

    @api_key.setter
    def api_key(self, value: Optional[str]) -> None:
        self._explicit_key = value

    @property
    def is_configured(self) -> bool:
        """
        Check if Maps service is ready.
        Always True because OpenStreetMap & OSRM require no API key or billing.
        """
        return True

    @property
    def is_google_maps_active(self) -> bool:
        """Check whether Google Maps key is optionally configured."""
        key = self.api_key
        return bool(key and key.strip())

    def get_status(self) -> Dict[str, Any]:
        """
        Return clear status, active engines, and attribution without external network calls.
        """
        if self.is_google_maps_active:
            return {
                "configured": True,
                "free_mode": False,
                "billing_required": False,
                "primary_engine": "Google Maps Routes API (Optional override active)",
                "open_routing_engine": "OpenStreetMap Road Routing via OSRM",
                "fallback_engine": "Dijkstra Corridor Shortest-Path Engine",
                "status": "Google Maps Platform active (Optional override; OSRM & Dijkstra fallbacks ready)",
                "attribution": "Road data © Google Maps Platform & OpenStreetMap contributors via OSRM",
            }

        return {
            "configured": True,
            "free_mode": True,
            "billing_required": False,
            "primary_engine": "OpenStreetMap Road Routing via OSRM",
            "open_routing_engine": "OpenStreetMap Road Routing via OSRM",
            "fallback_engine": "Dijkstra Corridor Shortest-Path Engine",
            "status": "OpenStreetMap & OSRM Road Routing Active (Free / No Key Required)",
            "attribution": "Road routing data © OpenStreetMap contributors via OSRM Project",
        }

    def get_route_details(
        self,
        origin: str,
        destination: str,
        waypoints: Optional[List[str]] = None,
        origin_coords: Optional[Dict[str, float]] = None,
        dest_coords: Optional[Dict[str, float]] = None,
        travel_mode: str = "DRIVE",
        compute_alternatives: bool = True,
    ) -> Dict[str, Any]:
        """
        Query road distance, driving duration, and route geometry.
        Tries Google Maps Routes API if an optional key is present; otherwise uses
        OpenStreetMap OSRM driving API. Gracefully falls back to Dijkstra graph on failure.
        Never exposes API keys in logs or responses.
        """
        if not origin or not origin.strip() or not destination or not destination.strip():
            return {
                "status": "invalid_input",
                "success": False,
                "error": "Origin and destination are required for route calculations",
                "fallback_active": True,
            }

        cleaned_origin = origin.strip()
        cleaned_dest = destination.strip()
        cleaned_waypoints = [w.strip() for w in (waypoints or []) if w and w.strip()]

        # 1. If Google Maps is optionally configured, try Google Routes first
        if self.is_google_maps_active:
            try:
                routes_data = self._call_routes_api(
                    origin=cleaned_origin,
                    destination=cleaned_dest,
                    waypoints=cleaned_waypoints,
                    travel_mode=travel_mode,
                    compute_alternatives=compute_alternatives,
                )
                if routes_data:
                    return {
                        "status": "success",
                        "success": True,
                        "source": "google_routes_api",
                        "is_live_google_maps": True,
                        "routes": routes_data,
                        "fallback_active": False,
                    }
            except Exception as exc:
                safe_err = sanitize_text(str(exc), secrets=[self.api_key])
                logger.debug("Google Routes API call failed or not enabled: %s", safe_err)

            # Try Directions API fallback
            try:
                directions_data = self._call_directions_api(
                    origin=cleaned_origin,
                    destination=cleaned_dest,
                    waypoints=cleaned_waypoints,
                    compute_alternatives=compute_alternatives,
                )
                if directions_data:
                    return {
                        "status": "success",
                        "success": True,
                        "source": "google_directions_api",
                        "is_live_google_maps": True,
                        "routes": directions_data,
                        "fallback_active": False,
                    }
            except Exception as exc:
                safe_err = sanitize_text(str(exc), secrets=[self.api_key])
                logger.warning("Google Directions API call failed: %s", safe_err)

        # 2. OpenStreetMap OSRM Road Routing (100% Free, Keyless)
        try:
            osrm_routes = self._call_osrm_api(
                origin=cleaned_origin,
                destination=cleaned_dest,
                waypoints=cleaned_waypoints,
                origin_coords=origin_coords,
                dest_coords=dest_coords,
                compute_alternatives=compute_alternatives,
            )
            if osrm_routes:
                return {
                    "status": "success",
                    "success": True,
                    "source": "osrm_road",
                    "is_live_google_maps": False,
                    "routes": osrm_routes,
                    "fallback_active": False,
                    "attribution": "Road routing © OpenStreetMap contributors via OSRM",
                }
        except Exception as exc:
            logger.warning("OSRM road route calculation failed: %s", exc)

        # 3. Graceful fallback signal to Dijkstra engine
        return {
            "status": "fallback_to_dijkstra",
            "success": False,
            "error": "Live road routing unavailable; falling back to calibrated Dijkstra corridor.",
            "fallback_active": True,
        }

    def _call_osrm_api(
        self,
        origin: str,
        destination: str,
        waypoints: List[str],
        origin_coords: Optional[Dict[str, float]],
        dest_coords: Optional[Dict[str, float]],
        compute_alternatives: bool,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Calculate driving routes using OpenStreetMap OSRM API.
        Resolves coordinates if not already provided.
        Expects coordinates in {lon},{lat} order per OSRM specifications.
        """
        # Resolve origin coordinates
        if not origin_coords or "lat" not in origin_coords or "lon" not in origin_coords:
            origin_coords = places_service.resolve_coordinates(origin)
        if not origin_coords:
            logger.debug("Could not resolve coordinates for origin: %s", origin)
            return None

        # Resolve destination coordinates
        if not dest_coords or "lat" not in dest_coords or "lon" not in dest_coords:
            dest_coords = places_service.resolve_coordinates(destination)
        if not dest_coords:
            logger.debug("Could not resolve coordinates for destination: %s", destination)
            return None

        # Resolve waypoint coordinates
        resolved_pts: List[Tuple[float, float]] = [
            (origin_coords["lon"], origin_coords["lat"])
        ]
        for wp in waypoints:
            wp_c = places_service.resolve_coordinates(wp)
            if wp_c:
                resolved_pts.append((wp_c["lon"], wp_c["lat"]))

        resolved_pts.append((dest_coords["lon"], dest_coords["lat"]))

        # Build coordinate string for OSRM: {lon1},{lat1};{lon2},{lat2};...
        coord_str = ";".join(f"{pt[0]:.5f},{pt[1]:.5f}" for pt in resolved_pts)
        cache_key = f"{coord_str}_{compute_alternatives}"
        if cache_key in self._route_cache:
            return self._route_cache[cache_key]

        url = f"{self.OSRM_ROUTE_URL}/{coord_str}"
        params = {
            "overview": "full",
            "geometries": "polyline",
            "alternatives": "true" if compute_alternatives else "false",
            "steps": "false",
        }
        headers = {"User-Agent": DEFAULT_OSRM_USER_AGENT}

        resp = requests.get(url, params=params, headers=headers, timeout=self.timeout)
        if resp.status_code != 200:
            logger.debug("OSRM returned status %s: %s", resp.status_code, resp.text[:200])
            return None

        data = resp.json()
        if data.get("code") != "Ok" or not data.get("routes"):
            return None

        raw_routes = data.get("routes", [])
        parsed_routes: List[Dict[str, Any]] = []

        for idx, r in enumerate(raw_routes):
            dist_m = float(r.get("distance", 0.0))
            dur_s = float(r.get("duration", 0.0))

            dist_km = round(dist_m / 1000.0, 1)
            dur_hours = round(dur_s / 3600.0, 1)

            # Leg summary extraction
            legs = r.get("legs", [])
            leg_summaries = [leg.get("summary") for leg in legs if leg.get("summary")]
            if leg_summaries:
                summary = " via " + ", ".join(dict.fromkeys(leg_summaries))
            else:
                summary = f"Road Corridor {idx + 1}" if idx > 0 else "Primary National/State Highway"

            route_summary = f"{summary} ({origin} → {destination})"
            poly = r.get("geometry")

            parsed_routes.append({
                "summary": route_summary,
                "total_distance_km": dist_km,
                "estimated_duration_hours": dur_hours,
                "via_waypoints": waypoints,
                "polyline": poly,
                "is_live_data": True,
                "source": "osrm_road",
                "attribution": "© OpenStreetMap contributors, OSRM Project",
            })

        if parsed_routes:
            self._route_cache[cache_key] = parsed_routes
            return parsed_routes

        return None

    def _call_routes_api(
        self,
        origin: str,
        destination: str,
        waypoints: List[str],
        travel_mode: str,
        compute_alternatives: bool,
    ) -> Optional[List[Dict[str, Any]]]:
        """Call optional Google Routes API v2 (POST ComputeRoutes)."""
        if not self.api_key:
            return None

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.description,routes.polyline.encodedPolyline",
        }
        payload: Dict[str, Any] = {
            "origin": {"address": origin},
            "destination": {"address": destination},
            "travelMode": travel_mode.upper(),
            "computeAlternativeRoutes": compute_alternatives,
            "routingPreference": "TRAFFIC_AWARE",
        }
        if waypoints:
            payload["intermediates"] = [{"address": wp} for wp in waypoints]

        resp = requests.post(
            self.ROUTES_API_URL,
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        raw_routes = data.get("routes", [])
        if not raw_routes:
            return None

        parsed_routes: List[Dict[str, Any]] = []
        for idx, r in enumerate(raw_routes):
            dist_m = float(r.get("distanceMeters", 0))
            dur_str = str(r.get("duration", "0s"))
            dur_sec = float(dur_str.rstrip("s")) if dur_str.endswith("s") else float(dur_str or 0)

            desc = r.get("description") or f"Google Highway Corridor {idx + 1} ({origin} → {destination})"
            poly = r.get("polyline", {}).get("encodedPolyline")

            parsed_routes.append({
                "summary": desc,
                "total_distance_km": round(dist_m / 1000.0, 1),
                "estimated_duration_hours": round(dur_sec / 3600.0, 1),
                "via_waypoints": waypoints,
                "polyline": poly,
                "is_live_data": True,
                "source": "google_routes",
            })

        return parsed_routes

    def _call_directions_api(
        self,
        origin: str,
        destination: str,
        waypoints: List[str],
        compute_alternatives: bool,
    ) -> Optional[List[Dict[str, Any]]]:
        """Call optional standard Google Directions API (GET directions/json)."""
        if not self.api_key:
            return None

        params: Dict[str, Any] = {
            "origin": origin,
            "destination": destination,
            "key": self.api_key,
            "alternatives": "true" if compute_alternatives else "false",
        }
        if waypoints:
            params["waypoints"] = "|".join(waypoints)

        resp = requests.get(
            self.DIRECTIONS_API_URL,
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "OK":
            return None

        raw_routes = data.get("routes", [])
        if not raw_routes:
            return None

        parsed_routes: List[Dict[str, Any]] = []
        for idx, r in enumerate(raw_routes):
            legs = r.get("legs", [])
            total_dist_m = sum(float(leg.get("distance", {}).get("value", 0)) for leg in legs)
            total_dur_sec = sum(float(leg.get("duration", {}).get("value", 0)) for leg in legs)

            summary = r.get("summary") or f"National Highway Corridor {idx + 1}"
            poly = r.get("overview_polyline", {}).get("points")

            parsed_routes.append({
                "summary": summary,
                "total_distance_km": round(total_dist_m / 1000.0, 1),
                "estimated_duration_hours": round(total_dur_sec / 3600.0, 1),
                "via_waypoints": waypoints,
                "polyline": poly,
                "is_live_data": True,
                "source": "google_directions_api",
            })

        return parsed_routes

    def __repr__(self) -> str:
        return f"<MapsService google_maps_active={self.is_google_maps_active} key={mask_secret(self.api_key)} open_osrm=True>"
