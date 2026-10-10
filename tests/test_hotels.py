"""
tests/test_hotels.py
====================
Unit tests for Accommodation & Hotel Search Tool.
Verifies destination matching, category filtering, stay cost calculations,
amenity matching, and official booking URL parameters.
"""

import datetime
import pytest
from backend.schemas import HotelCategory
from backend.tools.hotel_tool import search_hotels


def test_search_hotels_kerala_curated():
    """Verify curated hotel retrieval for Kerala with valid dates and guests."""
    check_in = datetime.date(2026, 11, 10)
    check_out = datetime.date(2026, 11, 14)  # 4 nights
    res = search_hotels(
        destination="Kerala",
        check_in_date=check_in,
        check_out_date=check_out,
        num_guests=2,
        num_rooms=1,
    )
    assert res.success is True
    hotels = res.data
    assert len(hotels) > 0

    first_hotel = hotels[0]
    assert first_hotel.destination == "Kerala"
    assert first_hotel.rating >= 4.0
    assert first_hotel.price_per_night_inr > 0
    # 4 nights * 1 room * price_per_night
    expected_total = first_hotel.price_per_night_inr * 4 * 1
    assert abs(first_hotel.total_stay_cost_inr - expected_total) < 0.01
    assert "booking.com" in first_hotel.booking_url.lower()


def test_search_hotels_category_filter():
    """Verify filtering by specific HotelCategory."""
    res = search_hotels(
        destination="Kerala",
        num_guests=2,
        preferred_category=HotelCategory.HOMESTAY,
    )
    assert res.success is True
    hotels = res.data
    assert len(hotels) >= 1
    assert all(h.category == HotelCategory.HOMESTAY for h in hotels)


def test_search_hotels_budget_cap():
    """Verify max budget per night constraint."""
    max_budget = 4000.0
    res = search_hotels(
        destination="Goa",
        max_budget_per_night_inr=max_budget,
    )
    assert res.success is True
    hotels = res.data
    assert len(hotels) >= 1
    assert all(h.price_per_night_inr <= max_budget for h in hotels)


def test_search_hotels_uncatalogued_city_fallback():
    """Verify generic synthesis for a town not in curated database."""
    res = search_hotels(
        destination="Tirupati",
        num_guests=3,
        num_rooms=2,
    )
    assert res.success is True
    hotels = res.data
    assert len(hotels) >= 1
    assert any("Tirupati" in h.name for h in hotels)
    assert hotels[0].booking_url is not None


def test_search_hotels_empty_destination():
    """Verify empty destination fails cleanly."""
    res = search_hotels(destination="")
    assert res.success is False
    assert "destination must be provided" in res.error.lower()
