"""
tests/test_destination.py
=========================
Unit tests for destination recommendation and seasonal discovery tool.
"""

from backend.tools.destination_tool import recommend_destinations


def test_destination_user_specified():
    """Verify that when a user specifies a destination, it is preserved and detailed."""
    res = recommend_destinations(
        origin="Bengaluru",
        preferred_destination="Goa",
        budget_inr=30000.0,
    )

    assert res.success is True
    data = res.data
    assert data["is_user_specified"] is True
    assert len(data["destinations"]) == 1
    assert data["destinations"][0]["name"] == "Goa"
    assert len(data["destinations"][0]["highlights"]) > 0


def test_destination_discovery_seasonal_scoring():
    """Verify that destination discovery scores suitable getaways for specific months."""
    # Month 11 (November) - Peak season for Goa and Rajasthan
    res_nov = recommend_destinations(
        origin="Bengaluru",
        interests=["beaches", "relaxation"],
        budget_inr=35000.0,
        travel_month=11,
        trip_type="solo",
        limit=3,
    )

    assert res_nov.success is True
    data = res_nov.data
    assert data["is_user_specified"] is False
    assert len(data["destinations"]) >= 1

    dest_names = [d["name"] for d in data["destinations"]]
    # Goa should be prominently recommended for November beaches
    assert "Goa" in dest_names
    assert len(data["explanations"]) == len(data["destinations"])


def test_destination_discovery_excludes_origin():
    """Verify that origin city is never recommended as a destination."""
    res = recommend_destinations(
        origin="Jaipur",
        interests=["heritage"],
        budget_inr=20000.0,
        travel_month=12,
    )

    assert res.success is True
    dest_names = [d["name"].lower() for d in res.data["destinations"]]
    assert "jaipur" not in dest_names
