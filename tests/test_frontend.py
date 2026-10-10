"""
tests/test_frontend.py
======================
Unit tests for Streamlit UI rendering components.
Verifies that all components render cleanly without pandas or DLL import errors.
"""

from backend.schemas import (
    TripPlan,
    BudgetBreakdown,
    BudgetItemBreakdown,
    DestinationRecommendation,
    DayPlan,
    ActivityItem,
    TransportOption,
    TransportMode,
    WeatherForecastSummary,
    AlternateRoute,
)
from frontend.app import render_plan_dashboard, load_theme_css, init_session_state
from frontend.components.header import render_header
from frontend.components.hero import render_hero
from frontend.components.navbar import render_navbar
from frontend.components.features import render_how_it_works, render_feature_cards
from frontend.components.destination_cards import render_destination_showcase
from frontend.components.itinerary_view import render_itinerary_section
from frontend.components.budget_view import render_budget_section
from frontend.components.transit_view import render_transit_section
from frontend.components.weather_safety_view import render_weather_section, render_safety_section
from frontend.components.connected_journey_view import render_connected_journey_section
from frontend.components.hotel_view import render_hotel_section
from frontend.components.booking_view import render_booking_section
from frontend.components.assistant_view import render_assistant_section
from frontend.components.profile_view import render_profile_section
from frontend.components.footer import render_footer


def create_sample_plan() -> TripPlan:
    """Helper to generate a realistic TripPlan fixture."""
    return TripPlan(
        trip_title="Coastal Explorer: Goa",
        summary="A 2-day beach getaway.",
        destinations=[
            DestinationRecommendation(
                name="Goa",
                tagline="Sun & Sand",
                highlights=["Calangute", "Baga"],
                estimated_cost_inr=25000.0,
            ),
            DestinationRecommendation(
                name="Gokarna",
                tagline="Serene Beaches",
                highlights=["Om Beach", "Kudle Beach"],
                estimated_cost_inr=18000.0,
            ),
        ],
        itinerary=[
            DayPlan(
                day_number=1,
                theme_or_title="Arrival & Beach Walk",
                overnight_location="North Goa Resort",
                activities=[
                    ActivityItem(
                        time_slot="Morning (10:00 - 13:00)",
                        title="Hotel Check-in & Relaxation",
                        location="North Goa",
                        estimated_cost_inr=500.0,
                    )
                ],
                day_notes="Rent a two-wheeler for easy transit.",
            )
        ],
        budget_breakdown=BudgetBreakdown(
            total_budget_inr=30000.0,
            estimated_total_cost_inr=26000.0,
            remaining_buffer_inr=4000.0,
            is_within_budget=True,
            categories=[
                BudgetItemBreakdown(
                    category="Accommodation",
                    allocated_amount_inr=12000.0,
                    percentage_of_total=40.0,
                    notes="Beach resort",
                ),
                BudgetItemBreakdown(
                    category="Transport",
                    allocated_amount_inr=8000.0,
                    percentage_of_total=26.7,
                    notes="Flights & cabs",
                ),
            ],
        ),
        transport_options=[
            TransportOption(
                mode=TransportMode.FLIGHT,
                departure_point="BLR",
                arrival_point="GOI",
                estimated_cost_inr=5000.0,
                duration_hours=1.2,
                is_recommended=True,
            )
        ],
        alternate_routes=[
            AlternateRoute(
                route_name="NH 48 Coastal Expressway",
                via_waypoints=["Hubballi", "Dharwad"],
                total_distance_km=560.0,
                estimated_duration_hours=9.5,
                algorithm_notes="Shortest highway path via Dijkstra",
            )
        ],
        weather_summary=WeatherForecastSummary(
            location="Goa",
            conditions="Sunny & Pleasant",
            average_temperature_c=29.0,
            precipitation_probability=5.0,
            packing_recommendations=["Sunscreen", "Cotton wear"],
        ),
        safety_precautions=["Swim only in designated lifeguard zones."],
    )


def test_render_plan_dashboard_no_pandas_dependency():
    """Verify render_plan_dashboard renders without triggering pandas C-extensions."""
    plan = create_sample_plan()
    # Must execute without raising any exceptions
    render_plan_dashboard(plan)


def test_render_all_modular_components():
    """Verify all individual UI components render cleanly."""
    plan = create_sample_plan()
    
    init_session_state()
    load_theme_css()
    render_header("gemini-3.8-flash", True)
    render_hero()
    render_how_it_works()
    render_feature_cards()
    render_destination_showcase()
    render_itinerary_section(plan)
    render_budget_section(plan.budget_breakdown, num_travellers=2)
    render_transit_section(plan.transport_options, plan.alternate_routes)
    render_weather_section(plan.weather_summary)
    render_safety_section(plan.safety_precautions)
    render_footer()


def test_render_empty_and_edge_case_states():
    """Verify components handle empty and None states gracefully."""
    empty_plan = TripPlan(
        trip_title="Minimal Trip",
        destinations=[],
        itinerary=[],
        budget_breakdown=None,
        weather_summary=None,
        transport_options=[],
        alternate_routes=[],
        safety_precautions=[],
    )
    render_plan_dashboard(empty_plan)
    render_budget_section(None, num_travellers=1)
    render_weather_section(None)
    render_safety_section([])


def test_render_new_workflow_views():
    """Verify new 9-section views render cleanly with sample plan."""
    plan = create_sample_plan()
    init_session_state()

    # Navbar
    section = render_navbar()
    assert section is not None

    # Connected journey view
    render_connected_journey_section(plan)
    render_connected_journey_section(None)

    # Hotel view
    render_hotel_section(plan)
    render_hotel_section(None)

    # Booking view
    render_booking_section(plan)
    render_booking_section(None)

    # Assistant view
    render_assistant_section(plan)

    # Profile view
    render_profile_section()

