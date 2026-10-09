"""
backend/services/maps_service.py
================================
Google Maps / Routes service integration.
Assigned to: Member 3 (Routing, Dijkstra, Transport and Budget)

Wraps Google Maps Routes API / Distance Matrix API to calculate distances,
durations, and routing polylines.
"""

from typing import Any, Dict, List, Optional
from backend.config import get_settings


class MapsService:
    """Service client for Google Maps and Routes API."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.settings = get_settings()
        self.api_key = api_key or self.settings.google_maps_api_key

    def get_route_details(
        self,
        origin: str,
        destination: str,
        waypoints: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Query distance and duration from Google Maps Routes API.
        TODO: Member 3 - Implement Google Routes / Distance Matrix API call.
        """
        if not self.api_key:
            return {"status": "api_key_not_configured"}
        return {"status": "pending_integration"}
