"""
tests/test_schemas.py
=====================
Unit tests for SpiritIQ schemas (TripRequest, ToolResult, TripPlan).
Validates field constraints, custom validators, and serialization.
"""

from datetime import date, timedelta
# pyrefly: ignore [missing-import]
import pytest
from pydantic import ValidationError

from backend.schemas import (
    TripRequest,
    TripType,
    TravelPace,
    TransportMode,
    ToolResult,
    TripPlan,
    DestinationRecommendation,
    DayPlan,
    ActivityItem,
    WeatherForecastSummary,
    TransportOption,
    BudgetBreakdown,
    BudgetItemBreakdown,
    AlternateRoute,
    BookingLink,
)


class TestTripRequest:
    """Test suite for TripRequest input validation."""

    def test_valid_trip_request_minimal(self):
        start = date(2026, 11, 1)
        end = date(2026, 11, 5)
        req = TripRequest(
            origin="Bengaluru",
            start_date=start,
            end_date=end,
            budget_inr=25000.0,
        )

        assert req.origin == "Bengaluru"
        assert req.destination is None
        assert req.start_date == start
        assert req.end_date == end
        assert req.trip_type == TripType.SOLO
        assert req.num_travellers == 1
        assert req.budget_inr == 25000.0
        assert req.pace == TravelPace.BALANCED
        assert req.is_flexible_dates is False
        assert req.date_flexibility_days == 0
        assert req.interests == []

    def test_valid_trip_request_all_fields(self):
        start = date(2026, 12, 10)
        end = date(2026, 12, 15)
        req = TripRequest(
            origin="Mumbai",
            destination="Goa",
            start_date=start,
            end_date=end,
            trip_type=TripType.FRIENDS,
            num_travellers=4,
            special_requirements="Vegetarian food preferred",
            age_groups=["adults"],
            budget_inr=50000.0,
            interests=["beaches", "seafood", "water sports"],
            pace=TravelPace.RELAXED,
            transport_preferences=[TransportMode.TRAIN, TransportMode.FLIGHT],
            return_journey_preference="Scenic coastal train",
            is_flexible_dates=True,
            date_flexibility_days=2,
        )

        assert req.destination == "Goa"
        assert req.trip_type == TripType.FRIENDS
        assert req.num_travellers == 4
        assert req.budget_inr == 50000.0
        assert len(req.interests) == 3
        assert req.pace == TravelPace.RELAXED
        assert req.is_flexible_dates is True
        assert req.date_flexibility_days == 2

    def test_invalid_dates_end_before_start(self):
        start = date(2026, 11, 10)
        end = date(2026, 11, 5)
        with pytest.raises(ValidationError) as exc_info:
            TripRequest(
                origin="Delhi",
                start_date=start,
                end_date=end,
                budget_inr=20000.0,
            )
        assert "end_date" in str(exc_info.value)
        assert "cannot be before start_date" in str(exc_info.value)

    def test_invalid_zero_and_negative_budget(self):
        start = date(2026, 11, 1)
        end = date(2026, 11, 5)
        with pytest.raises(ValidationError):
            TripRequest(
                origin="Delhi",
                start_date=start,
                end_date=end,
                budget_inr=0.0,
            )

        with pytest.raises(ValidationError):
            TripRequest(
                origin="Delhi",
                start_date=start,
                end_date=end,
                budget_inr=-5000.0,
            )

    def test_invalid_travellers_count(self):
        start = date(2026, 11, 1)
        end = date(2026, 11, 5)
        with pytest.raises(ValidationError):
            TripRequest(
                origin="Chennai",
                start_date=start,
                end_date=end,
                num_travellers=0,
                budget_inr=15000.0,
            )

    def test_empty_origin_string(self):
        start = date(2026, 11, 1)
        end = date(2026, 11, 5)
        with pytest.raises(ValidationError):
            TripRequest(
                origin="   ",
                start_date=start,
                end_date=end,
                budget_inr=15000.0,
            )

    def test_date_flexibility_normalization(self):
        start = date(2026, 11, 1)
        end = date(2026, 11, 5)
        req = TripRequest(
            origin="Hyderabad",
            start_date=start,
            end_date=end,
            budget_inr=18000.0,
            is_flexible_dates=False,
            date_flexibility_days=3,
        )
        assert req.is_flexible_dates is True
        assert req.date_flexibility_days == 3


class TestToolResult:
    """Test suite for standardized ToolResult envelope."""

    def test_tool_result_ok(self):
        payload = {"found": 3, "items": ["Beach A", "Beach B", "Beach C"]}
        res = ToolResult.ok(data=payload, metadata={"cached": True})

        assert res.success is True
        assert res.data == payload
        assert res.error is None
        assert res.metadata.get("cached") is True

    def test_tool_result_fail(self):
        res = ToolResult.fail(error="Failed to connect to weather provider")

        assert res.success is False
        assert res.data is None
        assert "weather provider" in res.error

    def test_tool_result_serialization(self):
        res = ToolResult.ok(data={"count": 1})
        dump = res.model_dump()
        assert dump["success"] is True
        assert dump["data"]["count"] == 1


class TestTripPlan:
    """Test suite for master TripPlan model and sub-components."""

    def test_trip_plan_default_factories_isolation(self):
        plan1 = TripPlan()
        plan2 = TripPlan()

        plan1.errors.append("Warning 1")
        assert len(plan2.errors) == 0, "Default factory lists must not be shared between instances"

    def test_trip_plan_full_serialization(self):
        destination = DestinationRecommendation(
            name="Udaipur",
            state_or_country="Rajasthan, India",
            tagline="The City of Lakes",
            highlights=["City Palace", "Lake Pichola", "Jag Mandir"],
            best_season="October to March",
            estimated_cost_inr=35000.0,
        )

        activity = ActivityItem(
            time_slot="Morning (09:00 - 12:00)",
            title="Boat ride on Lake Pichola",
            description="Scenic boat ride with views of Jag Mandir.",
            estimated_cost_inr=800.0,
            booking_required=True,
        )

        day = DayPlan(
            day_number=1,
            date=date(2026, 11, 1),
            theme_or_title="Royal Heritage Arrival",
            activities=[activity],
            overnight_location="Udaipur Heritage Haveli",
            estimated_daily_cost_inr=4500.0,
        )

        weather = WeatherForecastSummary(
            location="Udaipur",
            average_temperature_c=24.5,
            conditions="Clear skies, pleasant",
            precipitation_probability=5.0,
            packing_recommendations=["Light cottons", "Sunglasses", "Evening shawl"],
        )

        transport = TransportOption(
            mode=TransportMode.TRAIN,
            provider_or_route="Mewar Express",
            departure_point="Delhi (NZM)",
            arrival_point="Udaipur City (UDZ)",
            duration_hours=12.0,
            estimated_cost_inr=1500.0,
            is_recommended=True,
        )

        budget = BudgetBreakdown(
            total_budget_inr=40000.0,
            estimated_total_cost_inr=34000.0,
            remaining_buffer_inr=6000.0,
            is_within_budget=True,
            categories=[
                BudgetItemBreakdown(
                    category="Stay",
                    allocated_amount_inr=14000.0,
                    percentage_of_total=35.0,
                )
            ],
        )

        alternate_route = AlternateRoute(
            route_name="Via Chittorgarh Fort",
            via_waypoints=["Chittorgarh"],
            total_distance_km=420.0,
            estimated_duration_hours=7.5,
            highlights=["Historic UNESCO World Heritage Fort"],
            algorithm_notes="Scenic alternate via Dijkstra",
        )

        booking = BookingLink(
            title="Udaipur Heritage Hotel",
            category="stay",
            url="https://example.com/hotel/udaipur",
        )

        plan = TripPlan(
            trip_title="Royal Udaipur Odyssey",
            summary="A comprehensive 4-day royal cultural heritage experience in Udaipur.",
            destinations=[destination],
            itinerary=[day],
            weather_summary=weather,
            transport_options=[transport],
            budget_breakdown=budget,
            safety_precautions=["Drink bottled water", "Keep sunscreen handy"],
            alternate_routes=[alternate_route],
            booking_links=[booking],
        )

        # Ensure dictionary serialization succeeds
        dump = plan.model_dump()
        assert dump["trip_title"] == "Royal Udaipur Odyssey"
        assert len(dump["destinations"]) == 1
        assert dump["destinations"][0]["name"] == "Udaipur"
        assert len(dump["itinerary"]) == 1
        assert dump["itinerary"][0]["activities"][0]["title"] == "Boat ride on Lake Pichola"
        assert dump["budget_breakdown"]["is_within_budget"] is True
        assert dump["alternate_routes"][0]["route_name"] == "Via Chittorgarh Fort"

        # Ensure JSON serialization succeeds
        json_str = plan.model_dump_json()
        assert "Royal Udaipur Odyssey" in json_str
        assert "Udaipur" in json_str
