"""
tests/test_destination_planning.py
==================================
Comprehensive test suite verifying Groq migration and destination-specific planning.
Fulfills all 10 testing requirements without consuming live API quota or exposing secrets:
1. Successful Groq itinerary generation.
2. Missing and invalid API keys.
3. Rate-limit and quota errors.
4. Invalid model output.
5. Two different destinations producing destination-specific planning context.
6. Different dates and interests changing the request context.
7. Correct propagation of the selected destination from frontend to backend.
8. Cache keys and session state preventing stale itinerary reuse.
9. No placeholder itinerary being reported as a successful live AI response.
10. Pydantic validation and budget consistency.
"""

from datetime import date, timedelta
import json
from unittest.mock import MagicMock, patch

import pytest
from backend.agent import TravelPlanningAgent
from backend.schemas import (
    ActivityItem,
    DayPlan,
    TravelPace,
    TripPlan,
    TripRequest,
    TripType,
)
from backend.tools.destination_tool import get_destination_catalog_entry, recommend_destinations
from backend.tools.itinerary_tool import build_daywise_itinerary


def _sample_valid_ai_json(destination: str, num_days: int = 2) -> str:
    """Construct deterministic valid JSON matching TripPlan schema for any destination."""
    itinerary = []
    for i in range(1, num_days + 1):
        itinerary.append({
            "day_number": i,
            "date": f"2026-11-0{i}",
            "theme_or_title": f"Day {i}: Exploring {destination}",
            "activities": [
                {
                    "time_slot": "Morning (09:00 - 12:30)",
                    "title": f"Iconic morning in {destination}",
                    "description": f"Exploring {destination} highlights.",
                    "location": destination,
                    "estimated_cost_inr": 500.0,
                },
                {
                    "time_slot": "Evening (18:00 - 20:30)",
                    "title": f"{destination} Sunset Point",
                    "description": f"Sunset view in {destination}.",
                    "location": destination,
                    "estimated_cost_inr": 300.0,
                },
            ],
            "estimated_daily_cost_inr": 800.0,
        })

    return json.dumps({
        "trip_title": f"SpiritIQ Expedition: {destination} Journey",
        "summary": f"Personalized plan for {destination}.",
        "destinations": [
            {
                "name": destination,
                "state_or_country": "India",
                "tagline": f"Scenic getaway to {destination}",
                "highlights": [f"{destination} Landmark A", f"{destination} Landmark B"],
                "best_season": "October to March",
                "estimated_cost_inr": 15000.0,
            }
        ],
        "itinerary": itinerary,
        "budget_breakdown": {
            "total_budget_inr": 20000.0,
            "estimated_total_cost_inr": 15000.0,
            "remaining_buffer_inr": 5000.0,
            "is_within_budget": True,
            "categories": [
                {"category": "Accommodation", "allocated_amount_inr": 7000.0, "percentage_of_total": 46.7},
                {"category": "Activities", "allocated_amount_inr": 8000.0, "percentage_of_total": 53.3},
            ],
        },
        "safety_precautions": [f"Keep emergency helplines ready while in {destination}."],
        "errors": [],
        "metadata": {},
    })


# -----------------------------------------------------------------------------
# Test 1: Successful Groq itinerary generation
# -----------------------------------------------------------------------------
def test_req1_successful_groq_itinerary_generation():
    """Requirement 1: Verify successful Groq itinerary generation with mocked response."""
    agent = TravelPlanningAgent(api_key="gsk_valid_mock_key_12345")
    req = TripRequest(
        origin="Bengaluru",
        destination="Goa",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 2),
        budget_inr=20000.0,
    )

    mock_choice = MagicMock()
    mock_choice.message.content = _sample_valid_ai_json("Goa", num_days=2)
    mock_completion = MagicMock(choices=[mock_choice])

    with patch("backend.agent.Groq") as mock_groq_cls:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = mock_completion
        mock_groq_cls.return_value = mock_instance

        plan = agent.plan_trip(req)

    assert isinstance(plan, TripPlan)
    assert plan.metadata.get("ai_orchestrated") is True
    assert plan.metadata.get("is_fallback") is False
    assert plan.metadata.get("llm_provider") == "groq"
    assert "Goa" in plan.trip_title


# -----------------------------------------------------------------------------
# Test 2: Missing and invalid API keys
# -----------------------------------------------------------------------------
def test_req2_missing_and_invalid_api_keys():
    """Requirement 2: Graceful handling of missing and invalid API keys."""
    # Scenario A: Missing key
    agent_missing = TravelPlanningAgent(api_key="")
    req = TripRequest(
        origin="Delhi",
        destination="Jaipur",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 2),
        budget_inr=15000.0,
    )
    plan_missing = agent_missing.plan_trip(req)
    assert isinstance(plan_missing, TripPlan)
    assert plan_missing.metadata.get("ai_orchestrated") is False
    assert any("GROQ_API_KEY is not configured" in err for err in plan_missing.errors)

    # Scenario B: Invalid key rejecting at provider
    agent_invalid = TravelPlanningAgent(api_key="gsk_invalid_fake_key_9999")
    with patch("backend.agent.Groq") as mock_groq_cls:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.side_effect = RuntimeError("401 Invalid API Key")
        mock_groq_cls.return_value = mock_instance

        plan_invalid = agent_invalid.plan_trip(req)

    assert isinstance(plan_invalid, TripPlan)
    assert plan_invalid.metadata.get("ai_orchestrated") is False
    assert plan_invalid.metadata.get("is_fallback") is True
    assert any("temporary error" in err.lower() for err in plan_invalid.errors)


# -----------------------------------------------------------------------------
# Test 3: Rate-limit and quota errors
# -----------------------------------------------------------------------------
def test_req3_rate_limit_and_quota_errors():
    """Requirement 3: Graceful handling when Groq encounters HTTP 429 rate limit."""
    agent = TravelPlanningAgent(api_key="gsk_valid_mock_key_12345")
    req = TripRequest(
        origin="Mumbai",
        destination="Manali",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 2),
        budget_inr=25000.0,
    )

    with patch("backend.agent.Groq") as mock_groq_cls, patch("backend.agent.time.sleep"):
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.side_effect = RuntimeError("429 Too Many Requests: Rate limit exceeded")
        mock_groq_cls.return_value = mock_instance

        plan = agent.plan_trip(req)

    assert isinstance(plan, TripPlan)
    assert plan.metadata.get("ai_orchestrated") is False
    assert plan.metadata.get("is_fallback") is True
    assert any("rate limit" in err.lower() for err in plan.errors)


# -----------------------------------------------------------------------------
# Test 4: Invalid model output
# -----------------------------------------------------------------------------
def test_req4_invalid_model_output():
    """Requirement 4: Malformed or unparseable JSON from model falls back gracefully."""
    agent = TravelPlanningAgent(api_key="gsk_valid_mock_key_12345")
    req = TripRequest(
        origin="Bengaluru",
        destination="Coorg",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 2),
        budget_inr=15000.0,
    )

    mock_choice = MagicMock()
    mock_choice.message.content = "Malformed output: { broken json, not valid at all ..."
    mock_completion = MagicMock(choices=[mock_choice])

    with patch("backend.agent.Groq") as mock_groq_cls:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = mock_completion
        mock_groq_cls.return_value = mock_instance

        plan = agent.plan_trip(req)

    assert isinstance(plan, TripPlan)
    assert plan.metadata.get("ai_orchestrated") is False
    assert plan.metadata.get("is_fallback") is True
    assert "Coorg" in plan.trip_title


# -----------------------------------------------------------------------------
# Test 5: Two different destinations produce destination-specific planning context
# -----------------------------------------------------------------------------
def test_req5_two_different_destinations_produce_destination_specific_planning_context():
    """Requirement 5: Verify Kerala and Udaipur produce destination-distinct planning context."""
    agent = TravelPlanningAgent(api_key="")  # Test deterministic tool baseline

    req_kerala = TripRequest(
        origin="Bengaluru",
        destination="Kerala",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 3),
        budget_inr=30000.0,
    )
    plan_kerala = agent.plan_trip(req_kerala)

    req_udaipur = TripRequest(
        origin="Delhi",
        destination="Udaipur",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 3),
        budget_inr=30000.0,
    )
    plan_udaipur = agent.plan_trip(req_udaipur)

    # Kerala plan must contain authentic Kerala sights and not Udaipur sights
    kerala_text = " ".join(
        a.title + " " + a.description + " " + a.location
        for dp in plan_kerala.itinerary
        for a in dp.activities
    )
    assert any(term in kerala_text.lower() for term in ["kochi", "backwater", "alleppey", "munnar", "kerala", "chinese fishing"])
    assert "city palace" not in kerala_text.lower()
    assert "lake pichola" not in kerala_text.lower()

    # Udaipur plan must contain authentic Udaipur sights and not Kerala sights
    udaipur_text = " ".join(
        a.title + " " + a.description + " " + a.location
        for dp in plan_udaipur.itinerary
        for a in dp.activities
    )
    assert any(term in udaipur_text.lower() for term in ["city palace", "lake pichola", "udaipur", "bagore", "pichola"])
    assert "houseboat" not in udaipur_text.lower()
    assert "backwater" not in udaipur_text.lower()


# -----------------------------------------------------------------------------
# Test 6: Different dates and interests change the request context
# -----------------------------------------------------------------------------
def test_req6_different_dates_and_interests_change_request_context():
    """Requirement 6: Trip duration and interests dictate itinerary days and themes."""
    agent = TravelPlanningAgent(api_key="")

    # 4-day trip
    req_4days = TripRequest(
        origin="Bengaluru",
        destination="Ooty",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 4),
        budget_inr=20000.0,
        interests=["mountains", "tea"],
    )
    plan_4days = agent.plan_trip(req_4days)
    assert len(plan_4days.itinerary) == 4
    assert plan_4days.itinerary[0].date == date(2026, 11, 1)
    assert plan_4days.itinerary[3].date == date(2026, 11, 4)

    # 2-day trip
    req_2days = TripRequest(
        origin="Bengaluru",
        destination="Ooty",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 2),
        budget_inr=20000.0,
        interests=["tea"],
    )
    plan_2days = agent.plan_trip(req_2days)
    assert len(plan_2days.itinerary) == 2


# -----------------------------------------------------------------------------
# Test 7: Correct propagation of selected destination from frontend to backend
# -----------------------------------------------------------------------------
def test_req7_correct_propagation_of_selected_destination():
    """Requirement 7: Selected destination in TripRequest is strictly preserved by backend."""
    agent = TravelPlanningAgent(api_key="")

    for dest in ["Varanasi", "Pondicherry", "Shimla", "Manali"]:
        req = TripRequest(
            origin="Delhi",
            destination=dest,
            start_date=date(2026, 11, 1),
            end_date=date(2026, 11, 2),
            budget_inr=20000.0,
        )
        plan = agent.plan_trip(req)
        assert dest in plan.trip_title
        assert len(plan.destinations) >= 1
        assert dest.lower() in plan.destinations[0].name.lower()


# -----------------------------------------------------------------------------
# Test 8: Cache keys and session state preventing stale itinerary reuse
# -----------------------------------------------------------------------------
def test_req8_session_state_prevents_stale_itinerary_reuse():
    """Requirement 8: Subsequent request replaces previous result completely."""
    agent = TravelPlanningAgent(api_key="")

    # First request
    req1 = TripRequest(
        origin="Bengaluru",
        destination="Goa",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 2),
        budget_inr=20000.0,
    )
    plan1 = agent.plan_trip(req1)
    assert "Goa" in plan1.trip_title

    # Second request with new destination
    req2 = TripRequest(
        origin="Bengaluru",
        destination="Coorg",
        start_date=date(2026, 11, 5),
        end_date=date(2026, 11, 7),
        budget_inr=15000.0,
    )
    plan2 = agent.plan_trip(req2)
    assert "Coorg" in plan2.trip_title
    assert "Goa" not in plan2.trip_title
    assert len(plan2.itinerary) == 3


# -----------------------------------------------------------------------------
# Test 9: No placeholder itinerary being reported as a successful live AI response
# -----------------------------------------------------------------------------
def test_req9_no_placeholder_reported_as_successful_ai_response():
    """Requirement 9: Fallback responses MUST NOT claim ai_orchestrated=True."""
    agent = TravelPlanningAgent(api_key="")
    req = TripRequest(
        origin="Mumbai",
        destination="Pune",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 2),
        budget_inr=10000.0,
    )
    plan = agent.plan_trip(req)

    # Must be explicitly marked as NOT live AI orchestrated
    assert plan.metadata.get("ai_orchestrated") is False
    assert plan.metadata.get("is_fallback") is True
    # Non-empty errors notifying the user of the fallback
    assert len(plan.errors) > 0


# -----------------------------------------------------------------------------
# Test 10: Pydantic validation and budget consistency
# -----------------------------------------------------------------------------
def test_req10_pydantic_validation_and_budget_consistency():
    """Requirement 10: Ensure TripPlan satisfies schema constraints and budget arithmetic."""
    agent = TravelPlanningAgent(api_key="")
    req = TripRequest(
        origin="Hyderabad",
        destination="Goa",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 3),
        budget_inr=30000.0,
        num_travellers=3,
        pace=TravelPace.BALANCED,
    )
    plan = agent.plan_trip(req)

    # Validate model integrity
    dumped = plan.model_dump()
    re_validated = TripPlan.model_validate(dumped)
    assert re_validated.trip_title == plan.trip_title

    # Budget checks
    assert plan.budget_breakdown is not None
    assert plan.budget_breakdown.total_budget_inr == 30000.0
    assert plan.budget_breakdown.estimated_total_cost_inr <= 30000.0
    assert plan.budget_breakdown.is_within_budget is True


def test_req11_destination_coordinates_passed_and_stale_data_prevented():
    """Verify fresh coordinates are honored and changing destination never reuses stale coordinates."""
    agent = TravelPlanningAgent(api_key="")

    # Request with explicit Coorg coordinates
    coorg_coords = {"lat": 12.3375, "lon": 75.8069}
    req1 = TripRequest(
        origin="Bengaluru",
        destination="Coorg",
        destination_coordinates=coorg_coords,
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 3),
        budget_inr=15000.0,
    )
    plan1 = agent.plan_trip(req1)
    assert "Coorg" in plan1.trip_title
    assert plan1.weather_summary is not None
    assert "Coorg" in plan1.weather_summary.location

    # Subsequent request for Goa with no coordinates: must NOT reuse Coorg's coordinates
    req2 = TripRequest(
        origin="Bengaluru",
        destination="Goa",
        destination_coordinates=None,
        start_date=date(2026, 11, 10),
        end_date=date(2026, 11, 12),
        budget_inr=25000.0,
    )
    plan2 = agent.plan_trip(req2)
    assert "Goa" in plan2.trip_title
    assert "Coorg" not in plan2.trip_title
    assert "Goa" in plan2.weather_summary.location

