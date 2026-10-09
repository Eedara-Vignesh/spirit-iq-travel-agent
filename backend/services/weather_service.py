"""
backend/services/weather_service.py
===================================
Open-Meteo weather service integration.
Assigned to: Member 2 (Destination, Weather and Safety)

Fetches temperature forecasts and precipitation probability using the free Open-Meteo API.
Detects whether dates fall within the live forecast window (<= 16 days) or require
general seasonal guidance.
"""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from datetime import date
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Known coordinates for fast fallback / geocoding resolution
CITY_COORDINATES: Dict[str, Dict[str, float]] = {
    "goa": {"lat": 15.2993, "lon": 74.1240},
    "coorg": {"lat": 12.3375, "lon": 75.8069},
    "kodagu": {"lat": 12.3375, "lon": 75.8069},
    "bengaluru": {"lat": 12.9716, "lon": 77.5946},
    "bangalore": {"lat": 12.9716, "lon": 77.5946},
    "delhi": {"lat": 28.6139, "lon": 77.2090},
    "new delhi": {"lat": 28.6139, "lon": 77.2090},
    "mumbai": {"lat": 19.0760, "lon": 72.8777},
    "udaipur": {"lat": 24.5854, "lon": 73.7125},
    "jaipur": {"lat": 26.9124, "lon": 75.7873},
    "ooty": {"lat": 11.4102, "lon": 76.6950},
    "wayanad": {"lat": 11.6854, "lon": 76.1320},
    "manali": {"lat": 32.2432, "lon": 77.1892},
    "mysore": {"lat": 12.2958, "lon": 76.6394},
    "mysuru": {"lat": 12.2958, "lon": 76.6394},
    "chennai": {"lat": 13.0827, "lon": 80.2707},
    "hyderabad": {"lat": 17.3850, "lon": 78.4867},
    "kolkata": {"lat": 22.5726, "lon": 88.3639},
}


class WeatherService:
    """Service client for Open-Meteo weather API."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"

    def resolve_coordinates(self, location_name: str) -> Optional[Dict[str, float]]:
        """Resolve city name to latitude and longitude."""
        cleaned = location_name.strip().lower()
        for key, coords in CITY_COORDINATES.items():
            if key in cleaned or cleaned in key:
                return coords

        # Fallback: Open-Meteo geocoding search
        try:
            query = urllib.parse.quote(location_name.strip())
            url = f"{self.GEOCODE_URL}?name={query}&count=1&language=en&format=json"
            req = urllib.request.Request(url, headers={"User-Agent": "SpiritIQ/1.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode())
                results = data.get("results")
                if results and len(results) > 0:
                    return {
                        "lat": float(results[0]["latitude"]),
                        "lon": float(results[0]["longitude"]),
                    }
        except Exception as exc:
            logger.debug("Geocoding lookup failed for %s: %s", location_name, exc)
        return None

    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Fetch forecast from Open-Meteo if within 16-day window; otherwise return metadata.
        """
        today = date.today()
        # Open-Meteo standard API supports up to 16 days forward
        is_within_window = False
        if start_date:
            days_until_trip = (start_date - today).days
            is_within_window = 0 <= days_until_trip <= 16
        else:
            is_within_window = True

        if not is_within_window:
            return {
                "is_live_forecast": False,
                "data_source": "Seasonal Climate Expectation (General Guidance)",
                "note": "Trip dates are beyond the 16-day live forecast window. Showing seasonal expectations.",
                "latitude": latitude,
                "longitude": longitude,
            }

        try:
            url = (
                f"{self.BASE_URL}?latitude={latitude}&longitude={longitude}"
                f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
                f"&timezone=auto"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "SpiritIQ/1.0"})
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                data = json.loads(resp.read().decode())
                daily = data.get("daily", {})
                times = daily.get("time", [])
                max_temps = daily.get("temperature_2m_max", [])
                min_temps = daily.get("temperature_2m_min", [])
                precip_probs = daily.get("precipitation_probability_max", [])

                avg_temp = None
                if max_temps and min_temps:
                    valid_max = [t for t in max_temps if t is not None]
                    valid_min = [t for t in min_temps if t is not None]
                    if valid_max and valid_min:
                        avg_temp = round((sum(valid_max) / len(valid_max) + sum(valid_min) / len(valid_min)) / 2, 1)

                avg_precip = None
                if precip_probs:
                    valid_p = [p for p in precip_probs if p is not None]
                    if valid_p:
                        avg_precip = round(sum(valid_p) / len(valid_p), 1)

                return {
                    "is_live_forecast": True,
                    "data_source": "Open-Meteo Live Forecast API",
                    "average_temperature_c": avg_temp,
                    "precipitation_probability": avg_precip,
                    "daily_forecasts": [
                        {
                            "date": times[i],
                            "max_temp_c": max_temps[i],
                            "min_temp_c": min_temps[i],
                            "precip_prob_pct": precip_probs[i] if i < len(precip_probs) else None,
                        }
                        for i in range(min(len(times), 7))
                    ],
                }
        except Exception as exc:
            logger.warning("Open-Meteo forecast call failed: %s", exc)
            return {
                "is_live_forecast": False,
                "data_source": "Seasonal Climate Expectation (General Guidance)",
                "note": f"Weather API temporarily unreachable: {exc}. Using regional seasonal guidance.",
                "latitude": latitude,
                "longitude": longitude,
            }
