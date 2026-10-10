"""
tests/test_agent.py
===================
Unit tests for AI Travel Planning Agent (backend/agent.py).
Uses mocked Groq API responses to test orchestration, Pydantic validation,
destination discovery, and fallback resilience without live API calls or secrets.
"""

from datetime import date
import json
from unittest.mock import MagicMock, patch

from backend.agent import TravelPlanningAgent
from backend.schemas import (
    TripRequest,
    TripType,
    TravelPace,
    TransportMode,
    TripPlan,
)


def _make_mock_groq_response_json(destination: str = "Goa") -> str:
    """Helper returning valid JSON matching TripPlan schema."""
    plan_dict = {
        "trip_title": f"Sun, Sand & Heritage: {destination} Getaway",
        "summary": f"A delightful 2-day vacation in {destination} tailored for relaxation and culture.",
        "destinations": [
            {
                "name": destination,
                "state_or_country": "India",
                "tagline": "The Coastal Paradise",
                "highlights": ["Calangute Beach", "Fort Aguada", "Old Goa Churches"],
                "best_season": "November to February",
                "estimated_cost_inr": 18000.0,
            }
        ],
        "itinerary": [
            {
                "day_number": 1,
                "date": "2026-11-01",
                "theme_or_title": "Arrival & Coastal Relaxation",
                "activities": [
                    {
                        "time_slot": "Morning (10:00 - 13:00)",
                        "title": "Hotel Check-in & Beach Walk",
                        "description": "Unpack and take a tranquil walk along the sandy shore.",
                        "location": "North Goa",
                        "estimated_cost_inr": 500.0,
                        "booking_required": False,
                    },
                    {
                        "time_slot": "Evening (17:00 - 20:00)",
                        "title": "Sunset at Fort Aguada",
                        "description": "Historic lighthouse and panoramic Arabian Sea sunset views.",
                        "location": "Sinquerim",
                        "estimated_cost_inr": 300.0,
                        "booking_required": False,
                    },
                ],
                "overnight_location": "Candolim Resort",
                "estimated_daily_cost_inr": 3500.0,
                "day_notes": "Rent a scooter or cab for easy transit.",
            },
            {
                "day_number": 2,
                "date": "2026-11-02",
                "theme_or_title": "Heritage Churches & Local Gastronomy",
                "activities": [
                    {
                        "time_slot": "Morning (09:30 - 12:30)",
                        "title": "Basilica of Bom Jesus",
                        "description": "Explore UNESCO heritage Baroque architecture.",
                        "location": "Old Goa",
                        "estimated_cost_inr": 200.0,
                        "booking_required": False,
                    }
                ],
                "overnight_location": "Candolim Resort",
                "estimated_daily_cost_inr": 3000.0,
                "day_notes": "Wear modest clothing when visiting historical churches.",
            },
        ],
        "weather_summary": {
            "location": destination,
            "average_temperature_c": 28.0,
            "conditions": "Warm and sunny with coastal breeze",
            "precipitation_probability": 10.0,
            "packing_recommendations": ["Cotton shirts", "Sunscreen", "Beach footwear"],
            "advisories": ["Stay hydrated in afternoon heat"],
        },
        "transport_options": [
            {
                "mode": "flight",
                "provider_or_route": "IndiGo 6E",
                "departure_point": "BLR Airport",
                "arrival_point": "GOI Airport",
                "duration_hours": 1.2,
                "estimated_cost_inr": 4500.0,
                "is_recommended": True,
            }
        ],
        "budget_breakdown": {
            "total_budget_inr": 20000.0,
            "estimated_total_cost_inr": 16500.0,
            "remaining_buffer_inr": 3500.0,
            "is_within_budget": True,
            "categories": [
                {
                    "category": "Accommodation",
                    "allocated_amount_inr": 7000.0,
                    "percentage_of_total": 35.0,
                },
                {
                    "category": "Food & Dining",
                    "allocated_amount_inr": 5000.0,
                    "percentage_of_total": 25.0,
                },
            ],
        },
        "safety_precautions": [
            "Observe lifeguard flags on beaches.",
            "Save local helpline (112) on speed dial.",
        ],
        "alternate_routes": [],
        "booking_links": [],
        "errors": [],
        "metadata": {},
    }
    return json.dumps(plan_dict)


def test_agent_plan_trip_with_mocked_groq_success():
    """Verify end-to-end trip planning when Groq API responds successfully."""
    agent = TravelPlanningAgent(api_key="gsk_mock_test_key_12345")

    req = TripRequest(
        origin="Bengaluru",
        destination="Goa",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 2),
        budget_inr=20000.0,
        trip_type=TripType.SOLO,
        pace=TravelPace.BALANCED,
        interests=["beaches", "heritage"],
    )

    mock_choice = MagicMock()
    mock_choice.message.content = _make_mock_groq_response_json(destination="Goa")
    mock_completion = MagicMock(choices=[mock_choice])

    with patch("backend.agent.Groq") as mock_groq_cls:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = mock_completion
        mock_groq_cls.return_value = mock_instance

        plan = agent.plan_trip(req)

    assert isinstance(plan, TripPlan)
    assert "Goa" in plan.trip_title
    assert len(plan.itinerary) == 2
    assert plan.itinerary[0].day_number == 1
    assert len(plan.itinerary[0].activities) == 2
    assert plan.budget_breakdown is not None
    assert plan.budget_breakdown.is_within_budget is True
    assert len(plan.safety_precautions) >= 2
    assert plan.metadata.get("ai_orchestrated") is True
    assert plan.metadata.get("is_fallback") is False


def test_agent_plan_trip_destination_discovery():
    """Verify that omitting a destination triggers discovery recommendations."""
    agent = TravelPlanningAgent(api_key="gsk_mock_test_key_12345")

    req = TripRequest(
        origin="Delhi",
        destination=None,  # Destination discovery mode
        start_date=date(2026, 12, 1),
        end_date=date(2026, 12, 3),
        budget_inr=25000.0,
        trip_type=TripType.COUPLE,
        pace=TravelPace.RELAXED,
        interests=["mountains", "scenic"],
    )

    from backend.tools.destination_tool import recommend_destinations
    discovered_res = recommend_destinations(
        origin=req.origin,
        interests=req.interests,
        budget_inr=req.budget_inr,
        travel_month=req.start_date.month,
        trip_type=req.trip_type.value,
        preferred_destination=None,
    )
    top_dest_name = discovered_res.data["destinations"][0]["name"]

    mock_choice = MagicMock()
    mock_choice.message.content = _make_mock_groq_response_json(destination=top_dest_name)
    mock_completion = MagicMock(choices=[mock_choice])

    with patch("backend.agent.Groq") as mock_groq_cls:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = mock_completion
        mock_groq_cls.return_value = mock_instance

        plan = agent.plan_trip(req)

    assert isinstance(plan, TripPlan)
    assert len(plan.destinations) >= 1
    assert plan.destinations[0].name == top_dest_name
    assert len(plan.itinerary) == 3


def test_agent_missing_api_key_graceful_handling():
    """Verify that agent does not crash if GROQ_API_KEY is unset or empty."""
    agent = TravelPlanningAgent(api_key="")

    req = TripRequest(
        origin="Mumbai",
        destination="Pune",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 2),
        budget_inr=10000.0,
    )

    plan = agent.plan_trip(req)

    assert isinstance(plan, TripPlan)
    assert len(plan.errors) > 0
    assert "GROQ_API_KEY is not configured" in plan.errors[0]
    assert plan.budget_breakdown is not None  # Local budget tool still runs
    assert plan.metadata.get("ai_orchestrated") is False
    assert plan.metadata.get("is_fallback") is True


def test_agent_groq_server_error_fallback():
    """Verify fallback plan is returned when Groq encounters transient API error."""
    agent = TravelPlanningAgent(api_key="gsk_mock_test_key_12345")

    req = TripRequest(
        origin="Bengaluru",
        destination="Ooty",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 2),
        budget_inr=15000.0,
    )

    with patch("backend.agent.Groq") as mock_groq_cls, patch("backend.agent.time.sleep"):
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.side_effect = RuntimeError("503 Service Unavailable: Groq API temporarily busy")
        mock_groq_cls.return_value = mock_instance

        plan = agent.plan_trip(req)

    assert isinstance(plan, TripPlan)
    assert "Ooty" in plan.trip_title
    assert len(plan.itinerary) == 2
    assert len(plan.errors) > 0
    assert "temporary error" in plan.errors[0].lower()
    assert plan.budget_breakdown is not None
    assert len(plan.safety_precautions) >= 1
    assert plan.metadata.get("ai_orchestrated") is False
    assert plan.metadata.get("is_fallback") is True
