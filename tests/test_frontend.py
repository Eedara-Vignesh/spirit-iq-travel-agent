"""
tests/test_frontend.py
======================
Unit tests for Streamlit UI rendering components.
Verifies that all components render cleanly without pandas or DLL import errors,
and tests Agent Workspace timeline, activity log, and quota banner displays.
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
    AgentExecutionTrace,
    AgentStageRecord,
    StageStatus,
)
from frontend.app import render_plan_dashboard, load_theme_css, init_session_state
from frontend.components.header import render_header
from frontend.components.hero import render_hero
from frontend.components.features import render_how_it_works, render_feature_cards
from frontend.components.destination_cards import render_destination_showcase
from frontend.components.itinerary_view import render_itinerary_section
from frontend.components.budget_view import render_budget_section
from frontend.components.transit_view import render_transit_section
from frontend.components.weather_safety_view import render_weather_section, render_safety_section
from frontend.components.footer import render_footer
from frontend.components.agent_workspace import (
    render_agent_timeline,
    render_activity_log,
    render_quota_exhausted_banner,
)


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


def test_render_agent_workspace_timeline_and_activity_log():
    """Verify agent workspace timeline and activity logs render cleanly."""
    trace = AgentExecutionTrace(
        model_used="gemini-3.8-flash",
        stages=[
            AgentStageRecord(stage_id="s1", name="Request Validation", status=StageStatus.COMPLETED, provenance="Deterministic", summary="Parameters validated"),
            AgentStageRecord(stage_id="s2", name="Destination Discovery", status=StageStatus.SKIPPED, provenance="Local DB", summary="User specified Goa"),
            AgentStageRecord(stage_id="s3", name="Weather Guidance", status=StageStatus.COMPLETED, provenance="Live Open-Meteo", summary="28°C sunny"),
            AgentStageRecord(stage_id="s4", name="Highway Corridor", status=StageStatus.COMPLETED, provenance="Dijkstra Engine", summary="560 km corridor"),
            AgentStageRecord(stage_id="s5", name="Gemini Synthesis", status=StageStatus.FAILED, provenance="Gemini AI", error="Quota limit reached"),
        ],
        activity_log=[
            "[12:00:01] Validating trip parameters for Bengaluru to Goa...",
            "[12:00:02] Querying Open-Meteo endpoint...",
            "[12:00:03] Solving Dijkstra corridor graph...",
            "[12:00:04] ⚠️ Gemini quota limit reached (429 RESOURCE_EXHAUSTED).",
        ],
        has_quota_error=True,
    )

    render_agent_timeline(trace)
    render_activity_log(trace.activity_log)
    render_quota_exhausted_banner({"model": "gemini-3.8-flash", "retry_after": 60})


def test_render_plan_dashboard_preview_mode():
    """Verify render_plan_dashboard handles deterministic non-LLM preview mode correctly."""
    plan = create_sample_plan()
    plan.metadata["is_preview_mode"] = True
    plan.metadata["has_quota_error"] = True
    plan.errors = ["Notice: Gemini model quota exceeded (429 RESOURCE_EXHAUSTED). Preview loaded."]

    render_plan_dashboard(plan)
