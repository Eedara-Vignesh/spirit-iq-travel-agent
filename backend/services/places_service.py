"""
backend/services/places_service.py
==================================
Google Places API service integration.
Assigned to: Member 2 (Destination, Weather and Safety)

Wraps Google Places API to search for attractions, ratings, photos, and opening hours.
"""

from typing import Any, Dict, List, Optional
from backend.config import get_settings


class PlacesService:
    """Service client for Google Places API."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.settings = get_settings()
        self.api_key = api_key or self.settings.google_maps_api_key

    def search_attractions(self, query: str, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for points of interest matching query.
        TODO: Member 2 - Implement Google Places API Text Search / Place Details.
        """
        if not self.api_key:
            return []
        return []
