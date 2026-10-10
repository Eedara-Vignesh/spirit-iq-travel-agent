"""
frontend/app.py
===============
SpiritIQ — AI Travel Planning Agent (Premium Animated UI).
Assigned to: Member 4 (Frontend, Itinerary and Group Planning)

Provides interactive UI for multi-step travel planning.
Integrates with backend TravelPlanningAgent via validated Pydantic models.
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import date, timedelta
import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.schemas import (
    TripRequest,
    TripType,
    TravelPace,
    TransportMode,
    TripPlan,
)
from backend.config import get_settings
from backend.agent import TravelPlanningAgent

from frontend.components import render_html
from frontend.components.navbar import render_navbar
from frontend.components.header import render_header
from frontend.components.hero import render_hero
from frontend.components.destination_cards import render_destination_showcase
from frontend.components.features import render_how_it_works, render_feature_cards
from frontend.components.trip_form import render_trip_form
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


def load_theme_css() -> None:
    """Inject custom SpiritIQ theme and typography stylesheet."""
    css_path = PROJECT_ROOT / "frontend" / "styles" / "theme.css"
    if css_path.exists():
        try:
            with open(css_path, "r", encoding="utf-8") as f:
                render_html(f"<style>{f.read()}</style>")
        except Exception:
            pass


def init_session_state() -> None:
    """Initialize persistent session variables."""
    if "current_plan" not in st.session_state:
        st.session_state.current_plan = None
    if "active_section" not in st.session_state:
        st.session_state.active_section = "home"
    if "last_request" not in st.session_state:
        st.session_state.last_request = None
    if "form_origin" not in st.session_state:
        st.session_state.form_origin = "Bengaluru"
    if "form_destination" not in st.session_state:
        st.session_state.form_destination = "Goa"
    if "undecided_destination" not in st.session_state:
        st.session_state.undecided_destination = False


def render_sidebar(settings) -> None:
    """Render system status, active plan metrics, and team responsibilities."""
    with st.sidebar:
        render_html(
            """
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px;">
                <span style="font-size: 1.8rem;">✈️</span>
                <div>
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.25rem; font-weight: 800; color: #0F172A;">
                        Spirit<span style="color: #0284C7;">IQ</span>
                    </div>
                    <div style="font-size: 0.72rem; color: #64748B;">Autonomous Travel Agent</div>
                </div>
            </div>
            """
        )

        render_html("<h4 style='font-size: 1rem; color: #0F172A; margin-top: 10px;'>⚙️ Engine Status</h4>")
        key_status = settings.validate_keys()

        if key_status.get("groq_api_key_set"):
            st.success(f"Groq AI: Configured\n`{settings.groq_model}`")
        else:
            st.warning("Groq AI: API key missing in .env")

        if key_status["google_maps_api_key_set"]:
            st.success("Google Maps API: Live (Optional)")
        else:
            st.success("Roads & Places: OpenStreetMap + OSRM (Free)")

        # Active Plan Quick Summary (if present)
        if st.session_state.current_plan:
            st.divider()
            render_html("<h4 style='font-size: 1rem; color: #0284C7;'>📋 Active Plan</h4>")
            plan = st.session_state.current_plan
            st.caption(f"**Trip:** {plan.trip_title}")
            if plan.budget_breakdown:
                st.caption(f"**Budget:** ₹{plan.budget_breakdown.estimated_total_cost_inr:,.0f} / ₹{plan.budget_breakdown.total_budget_inr:,.0f}")
            if st.button("🗑️ Clear Plan & Reset Form", use_container_width=True):
                st.session_state.current_plan = None
                st.rerun()

        st.divider()
        render_html("<h4 style='font-size: 0.95rem; color: #0F172A;'>👥 SpiritIQ Engineering Team</h4>")
        st.caption(
            "• **Member 1 (Lead)**: Groq AI Orchestrator & Schemas\n"
            "• **Member 2**: Places, Open-Meteo Weather & Safety\n"
            "• **Member 3**: Dijkstra Shortest Path, Routes & Budget\n"
            "• **Member 4**: Streamlit Dashboard & Itinerary UI"
        )
        st.divider()
        st.caption("SpiritIQ v2.0 • 24-Hour Hackathon Build")


def render_plan_dashboard(plan: TripPlan) -> None:
    """
    Render comprehensive itinerary dashboard from validated TripPlan.
    Exported function required for unit testing and backwards compatibility.
    """
    render_html('<div id="results-dashboard"></div>')
    render_html("<div style='margin-top: 24px;'></div>")

    # Hero Title Banner & Action buttons
    col_h1, col_h2 = st.columns([4, 1.2])
    with col_h1:
        render_html(
            f"""
            <div style="margin-bottom: 12px;">
                <div class="spirit-hero-badge"><span>🎉</span> Itinerary Ready</div>
                <h1 style="font-size: 2.2rem; margin: 4px 0 6px 0; color: #0F172A;">
                    🗺️ {plan.trip_title}
                </h1>
            </div>
            """
        )
    with col_h2:
        st.write("<div style='height: 18px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Regenerate Plan", use_container_width=True):
            if "last_request" in st.session_state and st.session_state.last_request:
                agent = TravelPlanningAgent()
                with st.spinner("🤖 Regenerating fresh itinerary with Groq AI..."):
                    st.session_state.current_plan = agent.plan_trip(st.session_state.last_request)
                    st.rerun()

    # Verified Request Summary Card
    req = st.session_state.get("last_request")
    if req:
        num_d = max(1, (req.end_date - req.start_date).days + 1)
        is_ai = plan.metadata.get("ai_orchestrated", False)
        ai_badge = f"🤖 Groq AI ({plan.metadata.get('model', 'llama-3.3-70b-versatile')})" if is_ai else "🛠️ Modular Tool Mode"
        target_display = req.destination if req.destination else (plan.destinations[0].name if plan.destinations else "Auto-Discovery")
        render_html(
            f"""
            <div style="
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                padding: 14px 20px;
                margin-bottom: 20px;
                display: flex;
                flex-wrap: wrap;
                gap: 16px;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
            ">
                <div>
                    <span style="font-size: 0.72rem; color: #64748B; text-transform: uppercase;">Origin → Target</span>
                    <div style="font-size: 0.98rem; font-weight: 700; color: #0F172A;">{req.origin} ➔ {target_display}</div>
                </div>
                <div>
                    <span style="font-size: 0.72rem; color: #64748B; text-transform: uppercase;">Dates & Duration</span>
                    <div style="font-size: 0.92rem; font-weight: 600; color: #0284C7;">{req.start_date.strftime('%d %b %Y')} – {req.end_date.strftime('%d %b %Y')} ({num_d} Days)</div>
                </div>
                <div>
                    <span style="font-size: 0.72rem; color: #64748B; text-transform: uppercase;">Party Dynamic</span>
                    <div style="font-size: 0.92rem; font-weight: 600; color: #0F172A;">{req.num_travellers} Traveller(s) • {req.trip_type.value.capitalize()}</div>
                </div>
                <div>
                    <span style="font-size: 0.72rem; color: #64748B; text-transform: uppercase;">Total Budget</span>
                    <div style="font-size: 0.92rem; font-weight: 600; color: #059669;">₹{req.budget_inr:,.0f} (₹{req.budget_inr / max(1, req.num_travellers):,.0f}/person)</div>
                </div>
                <div>
                    <span style="font-size: 0.72rem; color: #64748B; text-transform: uppercase;">Engine Mode</span>
                    <div style="font-size: 0.85rem; font-weight: 700; color: {'#059669' if is_ai else '#D97706'};">{ai_badge}</div>
                </div>
            </div>
            """
        )

    # Notices & Warnings
    if plan.errors:
        for err in plan.errors:
            st.warning(f"ℹ️ Advisory: {err}")

    # Executive Summary Card
    if plan.summary:
        render_html(
            f"""
            <div style="
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-left: 4px solid #0284C7;
                border-radius: 14px;
                padding: 18px 24px;
                margin-bottom: 24px;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
            ">
                <div style="font-size: 0.8rem; font-weight: 700; color: #0284C7; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">
                    ✨ Executive Summary
                </div>
                <div style="font-size: 0.98rem; line-height: 1.6; color: #0F172A;">
                    {plan.summary}
                </div>
            </div>
            """
        )


    # Organized Result Tabs
    tab_itinerary, tab_budget, tab_transit, tab_weather, tab_safety = st.tabs([
        "📅 Day-wise Itinerary",
        "💰 Budget & Costs",
        "🚗 Transit & Dijkstra Routes",
        "🌤️ Weather & Packing",
        "🛡️ Safety Precautions",
    ])

    num_travellers = (
        st.session_state.last_request.num_travellers
        if ("last_request" in st.session_state and st.session_state.last_request)
        else 1
    )

    with tab_itinerary:
        render_itinerary_section(plan)

    with tab_budget:
        render_budget_section(plan.budget_breakdown, num_travellers=num_travellers)

    with tab_transit:
        render_transit_section(plan.transport_options, plan.alternate_routes)

    with tab_weather:
        render_weather_section(plan.weather_summary)

    with tab_safety:
        render_safety_section(plan.safety_precautions)


def main() -> None:
    st.set_page_config(
        page_title="SpiritIQ — AI Travel Planning Agent",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_session_state()
    load_theme_css()

    settings = get_settings()
    render_sidebar(settings)

    # Top Navigation Bar with 9 Connected Sections
    active_section = render_navbar()

    # Route based on active navigation section
    if active_section == "home":
        key_status = settings.validate_keys()
        render_header(
            model_name=settings.groq_model,
            maps_active=key_status["google_maps_api_key_set"],
        )
        render_hero()
        render_how_it_works()
        render_feature_cards()
        render_destination_showcase()

        # Prompt CTA Button
        col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
        with col_c2:
            if st.button("✨ Launch Connected Trip Planner 🚀", key="home_cta_plan_btn", type="primary", use_container_width=True):
                st.session_state.active_section = "plan_trip"
                st.rerun()

    elif active_section == "plan_trip":
        form_request = render_trip_form()
        if form_request is not None:
            try:
                with st.spinner("🤖 SpiritIQ Groq AI Agent synthesizing your personalized connected trip plan..."):
                    agent = TravelPlanningAgent()
                    plan: TripPlan = agent.plan_trip(form_request)
                    st.session_state.current_plan = plan
                    st.session_state.last_request = form_request
                    st.session_state.active_section = "itinerary"
                    if plan.metadata.get("ai_orchestrated"):
                        st.toast("🎉 Your personalized Groq AI itinerary is ready! Switched to My Itinerary view.", icon="✈️")
                    else:
                        st.toast("📋 Your destination plan is ready (Modular Tool Mode). Switched to My Itinerary view.", icon="🗺️")
                    st.rerun()
            except Exception as e:
                st.error(f"Planning error: {e}")

        if st.session_state.current_plan:
            st.divider()
            render_html("<h3 style='color: #00F0FF; margin-bottom: 12px;'>📋 Current Generated Plan Overview</h3>")
            render_plan_dashboard(st.session_state.current_plan)

    elif active_section == "destinations":
        key_status = settings.validate_keys()
        render_header(
            model_name=settings.groq_model,
            maps_active=key_status["google_maps_api_key_set"],
        )
        render_destination_showcase()

    elif active_section == "itinerary":
        if st.session_state.current_plan:
            render_plan_dashboard(st.session_state.current_plan)
        else:
            render_html(
                """
                <div style="
                    background: rgba(16, 28, 58, 0.6);
                    border: 1px dashed rgba(0, 240, 255, 0.3);
                    border-radius: 14px;
                    padding: 36px;
                    text-align: center;
                    margin: 20px 0;
                ">
                    <span style="font-size: 2.8rem;">📅</span>
                    <h3 style="color: #F1F5F9; margin: 12px 0 6px 0;">No Active Itinerary Generated</h3>
                    <p style="color: #94A3B8; max-width: 500px; margin: 0 auto 18px auto;">
                        Configure your travel dates and route in Plan My Trip to view an optimized day-by-day plan.
                    </p>
                </div>
                """
            )
            if st.button("✨ Go to Plan My Trip", key="no_itin_plan_btn", type="primary"):
                st.session_state.active_section = "plan_trip"
                st.rerun()

    elif active_section == "transport":
        render_connected_journey_section(st.session_state.current_plan)

    elif active_section == "hotels":
        render_hotel_section(st.session_state.current_plan)

    elif active_section == "bookings":
        render_booking_section(st.session_state.current_plan)

    elif active_section == "assistant":
        render_assistant_section(st.session_state.current_plan)

    elif active_section == "profile":
        render_profile_section()

    # Modern Product Footer
    render_footer()


if __name__ == "__main__":
    main()
