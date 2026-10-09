"""
tests/test_weather.py
====================
Unit tests for weather service and tool.
Tests coordinate resolution and 16-day forecast window detection (mocked).
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from backend.services.weather_service import WeatherService
from backend.tools.weather_tool import get_weather_forecast


def test_weather_service_coordinate_resolution():
    """Verify city name resolution to latitude/longitude coordinates."""
    svc = WeatherService()
    coords = svc.resolve_coordinates("Goa")
    assert coords is not None
    assert round(coords["lat"], 1) == 15.3
    assert round(coords["lon"], 1) == 74.1

    coords_ooty = svc.resolve_coordinates("Ooty")
    assert coords_ooty is not None
    assert round(coords_ooty["lat"], 1) == 11.4


def test_weather_service_outside_window_detection():
    """Verify that dates beyond 16 days trigger seasonal guidance rather than live forecast."""
    svc = WeatherService()
    future_start = date.today() + timedelta(days=45)
    future_end = future_start + timedelta(days=5)

    res = svc.get_forecast(latitude=15.2993, longitude=74.1240, start_date=future_start, end_date=future_end)
    assert res["is_live_forecast"] is False
    assert "Seasonal Climate Expectation" in res["data_source"]


def test_weather_tool_packaging_advice():
    """Verify weather tool returns structured WeatherForecastSummary with packing advice."""
    with patch.object(WeatherService, "get_forecast") as mock_get:
        mock_get.return_value = {
            "is_live_forecast": True,
            "data_source": "Open-Meteo Live Forecast API",
            "average_temperature_c": 28.5,
            "precipitation_probability": 15.0,
        }

        res = get_weather_forecast(
            location="Goa",
            start_date=date.today() + timedelta(days=2),
            end_date=date.today() + timedelta(days=5),
        )

        assert res.success is True
        data = res.data
        assert data["location"] == "Goa"
        assert len(data["packing_recommendations"]) > 0
        assert any("cotton" in item.lower() or "sun" in item.lower() for item in data["packing_recommendations"])
