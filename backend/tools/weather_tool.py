"""
backend/tools/weather_tool.py
=============================
Weather forecast and seasonal advisories tool.
Assigned to: Member 2 (Destination, Weather and Safety)

Fetches temperature, precipitation forecast, and packing tips using Open-Meteo.
Distinguishes live forecast (<= 16 days) from seasonal expectations (> 16 days).
"""

from __future__ import annotations

from datetime import date
from typing import List, Optional
from backend.schemas import ToolResult, WeatherForecastSummary
from backend.services.weather_service import WeatherService

weather_service = WeatherService()


def get_weather_forecast(
    location: str,
    start_date: date,
    end_date: date,
    coordinates: Optional[Dict[str, float]] = None,
) -> ToolResult:
    """
    Fetch forecast and packing guidance for destination across dates.
    Uses real Open-Meteo data when within the 16-day window, or seasonal guidelines otherwise.
    """
    norm_coords = None
    if coordinates and "lat" in coordinates:
        norm_coords = {
            "lat": coordinates["lat"],
            "lon": coordinates.get("lon") if "lon" in coordinates else coordinates.get("lng", 0.0),
        }
    coords = norm_coords or weather_service.resolve_coordinates(location)
    if not coords:
        # Default packing advice for unknown coordinate
        summary = WeatherForecastSummary(
            location=location,
            conditions="Seasonal expectations (Location coordinates unresolved)",
            packing_recommendations=["Comfortable all-weather clothing", "Travel umbrella", "Walking shoes"],
            advisories=["Check local weather forecast 24 hours prior to departure."],
        )
        return ToolResult.ok(
            data=summary.model_dump(),
            metadata={"tool": "weather_tool", "source": "generic_fallback"},
        )

    raw = weather_service.get_forecast(
        latitude=coords["lat"],
        longitude=coords["lon"],
        start_date=start_date,
        end_date=end_date,
    )

    is_live = raw.get("is_live_forecast", False)
    avg_temp = raw.get("average_temperature_c")
    precip_prob = raw.get("precipitation_probability")
    source_label = raw.get("data_source", "Open-Meteo Weather")

    # Generate tailored packing tips based on temperature and precipitation
    packing: List[str] = ["Comfortable footwear"]
    advisories: List[str] = []

    if avg_temp is not None:
        if avg_temp < 15.0:
            packing.extend(["Warm fleece / thermal innerwear", "Light jacket or sweater", "Moisturizer"])
            advisories.append("Expect chilly mornings and evenings.")
        elif avg_temp > 30.0:
            packing.extend(["Breathable light cottons", "UV protection sunglasses", "Sunscreen (SPF 50+)", "Sun hat"])
            advisories.append("High daytime heat. Drink plenty of water and avoid strenuous midday outdoor sun.")
        else:
            packing.extend(["Light jacket for evenings", "Cotton shirts/t-shirts"])

    if precip_prob is not None and precip_prob > 35.0:
        packing.extend(["Compact travel umbrella or raincoat", "Waterproof pouch for electronics"])
        advisories.append(f"High chance of rain (~{precip_prob:.0f}%). Plan indoor alternative activities.")
    else:
        packing.append("Standard travel daypack")

    conditions_text = (
        f"{'Live Forecast' if is_live else 'Seasonal Guidance'} ({source_label}): "
        f"{f'Avg ~{avg_temp}°C' if avg_temp else 'Moderate seasonal temperatures'}, "
        f"{f'{precip_prob}% chance of rain' if precip_prob else 'low precipitation anticipated'}."
    )

    summary = WeatherForecastSummary(
        location=location,
        average_temperature_c=avg_temp,
        conditions=conditions_text,
        precipitation_probability=precip_prob,
        packing_recommendations=packing,
        advisories=advisories,
    )

    return ToolResult.ok(
        data=summary.model_dump(),
        metadata={
            "tool": "weather_tool",
            "is_live_forecast": is_live,
            "data_source": source_label,
            "coordinates": coords,
        },
    )
