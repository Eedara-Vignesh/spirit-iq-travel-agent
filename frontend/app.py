"""
frontend/app.py
===============
SpiritIQ — AI Travel Planning Agent (Agent-First Workspace).
Assigned to: Member 4 (Frontend, Itinerary and Group Planning)

Provides interactive workspace for multi-step autonomous travel planning.
Integrates with backend TravelPlanningAgent via validated Pydantic models.
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import date, timedelta
from typing import Optional
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
from frontend.components.header import render_header
from frontend.components.agent_workspace import (
    render_agent_timeline,
    render_activity_log,
    render_quota_exhausted_banner,
)
from frontend.components.trip_form import render_trip_form
from frontend.components.itinerary_view import render_itinerary_section
from frontend.components.budget_view import render_budget_section
from frontend.components.transit_view import render_transit_section
from frontend.components.weather_safety_view import render_weather_section, render_safety_section
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
    if "last_request" not in st.session_state:
        st.session_state.last_request = None
    if "form_origin" not in st.session_state:
        st.session_state.form_origin = "Bengaluru"
    if "form_destination" not in st.session_state:
        st.session_state.form_destination = "Goa"
    if "undecided_destination" not in st.session_state:
        st.session_state.undecided_destination = False
    if "execution_trace" not in st.session_state:
        st.session_state.execution_trace = None


def render_sidebar(settings) -> None:
    """Render system status, active plan metrics, and team responsibilities."""
    with st.sidebar:
        render_html(
            """
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px;">
                <span style="font-size: 1.8rem;">✈️</span>
                <div>
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.25rem; font-weight: 800; color: #FFFFFF;">
                        Spirit<span style="color: #00F0FF;">IQ</span>
                    </div>
                    <div style="font-size: 0.72rem; color: #94A3B8;">Autonomous Travel Agent</div>
                </div>
            </div>
            """
        )

        render_html("<h4 style='font-size: 1rem; color: #F1F5F9; margin-top: 10px;'>⚙️ Engine Status</h4>")
        key_status = settings.validate_keys()

        if key_status["gemini_api_key_set"]:
            st.success(f"Gemini AI: Configured\n`{settings.gemini_model}`")
        else:
            st.warning("Gemini AI: API key missing in .env")

        if key_status["google_maps_api_key_set"]:
            st.success("Google Maps API: Live")
        else:
            st.info("Google Maps: Dijkstra corridor fallback active")

        # Active Plan Quick Summary (if present)
        if st.session_state.current_plan:
            st.divider()
            render_html("<h4 style='font-size: 1rem; color: #00F0FF;'>📋 Active Plan</h4>")
            plan: TripPlan = st.session_state.current_plan
            st.caption(f"**Trip:** {plan.trip_title}")
            if plan.budget_breakdown:
                st.caption(f"**Budget:** ₹{plan.budget_breakdown.estimated_total_cost_inr:,.0f} / ₹{plan.budget_breakdown.total_budget_inr:,.0f}")
            if st.button("🗑️ Reset Workspace", use_container_width=True):
                st.session_state.current_plan = None
                st.session_state.execution_trace = None
                st.rerun()

        st.divider()
        render_html("<h4 style='font-size: 0.95rem; color: #F1F5F9;'>👥 SpiritIQ Engineering Team</h4>")
        st.caption(
            "• **Member 1 (Lead)**: Gemini AI Orchestrator & Schemas\n"
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
    render_html("<div style='margin-top: 16px;'></div>")

    # If this is a preview mode (e.g. non-LLM preview due to quota), make it explicit!
    is_preview = bool(plan.metadata.get("is_preview_mode"))
    has_quota = bool(plan.metadata.get("has_quota_error"))

    if is_preview:
        render_html(
            """
            <div style="
                background: rgba(255, 183, 3, 0.1);
                border: 1px solid rgba(255, 183, 3, 0.35);
                border-left: 4px solid #FFB703;
                border-radius: 12px;
                padding: 12px 18px;
                margin-bottom: 16px;
                display: flex;
                align-items: center;
                gap: 12px;
            ">
                <span style="font-size: 1.4rem;">🛡️</span>
                <div>
                    <div style="font-size: 0.85rem; font-weight: 700; color: #FFB703; text-transform: uppercase;">
                        Deterministic Rule-Based Preview (Non-LLM)
                    </div>
                    <div style="font-size: 0.82rem; color: #F1F5F9;">
                        Displaying verified outputs from local tools (Open-Meteo weather, Dijkstra routing corridors, and budget calculations). 
                        This plan was assembled without Gemini AI synthesis.
                    </div>
                </div>
            </div>
            """
        )

    # Hero Title Banner & Action buttons
    col_h1, col_h2 = st.columns([4, 1.4])
    with col_h1:
        badge_text = "Preview Mode" if is_preview else "Itinerary Ready"
        render_html(
            f"""
            <div style="margin-bottom: 12px;">
                <div class="spirit-hero-badge"><span>🎉</span> {badge_text}</div>
                <h1 style="font-size: 2.1rem; margin: 4px 0 6px 0; color: #FFFFFF;">
                    🗺️ {plan.trip_title}
                </h1>
            </div>
            """
        )
    with col_h2:
        st.write("<div style='height: 18px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Retry / Regenerate", use_container_width=True, type="primary"):
            if "last_request" in st.session_state and st.session_state.last_request:
                agent = TravelPlanningAgent()
                with st.spinner("🤖 Launching AI Agent pipeline..."):
                    st.session_state.current_plan = agent.plan_trip(st.session_state.last_request)
                    st.rerun()

    # Notices & Warnings (clean display without raw exception dumps)
    if plan.errors:
        for err in plan.errors:
            # If error mentions quota or rate-limits, format cleanly
            if "rate-limits" in err or "429" in err:
                st.warning(f"ℹ️ {err}")
            else:
                st.info(f"ℹ️ {err}")

    # Executive Summary Card
    if plan.summary:
        render_html(
            f"""
            <div style="
                background: linear-gradient(135deg, rgba(16, 28, 58, 0.8) 0%, rgba(20, 39, 70, 0.8) 100%);
                border: 1px solid rgba(0, 240, 255, 0.25);
                border-radius: 16px;
                padding: 18px 24px;
                margin-bottom: 24px;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
            ">
                <div style="font-size: 0.8rem; font-weight: 700; color: #00F0FF; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">
                    ✨ Executive Summary
                </div>
                <div style="font-size: 0.96rem; line-height: 1.6; color: #F1F5F9;">
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

    # Top Brand Navigation Header
    key_status = settings.validate_keys()
    render_header(
        gemini_model=settings.gemini_model,
        maps_active=key_status["google_maps_api_key_set"],
    )

    # Main Agent-First Workspace Split Layout
    col_request, col_workspace = st.columns([5, 7], gap="large")

    # LEFT: Travel Request Panel (Inputs)
    with col_request:
        form_request = render_trip_form()

    # RIGHT: Agent Workspace & Execution Console
    with col_workspace:
        # Check if user submitted form
        if form_request is not None:
            st.session_state.last_request = form_request
            
            # Progress and real-time trace placeholder
            trace_placeholder = st.empty()
            
            agent = TravelPlanningAgent()
            final_plan: Optional[TripPlan] = None
            
            # Real streaming execution over actual backend tools
            for trace, plan_result in agent.plan_trip_stream(form_request):
                with trace_placeholder.container():
                    render_agent_timeline(trace)
                    render_activity_log(trace.activity_log)
                    if trace.has_quota_error:
                        render_quota_exhausted_banner(trace.quota_error_details)
                
                if plan_result is not None:
                    final_plan = plan_result

            if final_plan:
                st.session_state.current_plan = final_plan
                st.session_state.execution_trace = final_plan.execution_trace
                st.rerun()

        # Render Active Plan & Execution Trace
        elif st.session_state.current_plan:
            plan = st.session_state.current_plan
            
            # Check for quota exhaustion
            if plan.metadata.get("has_quota_error"):
                quota_details = plan.metadata.get("quota_error_details") or {
                    "model": settings.gemini_model,
                    "retry_after": None,
                }
                render_quota_exhausted_banner(quota_details)

            # Collapsible Agent Execution Trace & Activity Log
            with st.expander("🔍 Inspect Agent Tool Execution Trace & Provenance", expanded=False):
                if plan.execution_trace:
                    render_agent_timeline(plan.execution_trace)
                    render_activity_log(plan.execution_trace.activity_log)

            # Final Master Plan Dashboard
            render_plan_dashboard(plan)

        # Idle State: Agent Ready Guide
        else:
            render_html(
                """
                <div style="
                    background: rgba(16, 28, 58, 0.5);
                    border: 1px dashed rgba(0, 240, 255, 0.3);
                    border-radius: 16px;
                    padding: 32px 28px;
                    text-align: center;
                    margin-top: 24px;
                ">
                    <div style="font-size: 3rem; margin-bottom: 12px;">🧭</div>
                    <h3 style="font-size: 1.4rem; color: #FFFFFF; margin-bottom: 8px;">
                        SpiritIQ Agent Workspace Ready
                    </h3>
                    <p style="color: #94A3B8; font-size: 0.9rem; max-width: 500px; margin: 0 auto 20px auto; line-height: 1.5;">
                        Configure your travel parameters on the left and click 
                        <strong style="color: #00F0FF;">Launch AI Planning Agent</strong> to initiate the autonomous orchestration pipeline.
                    </p>

                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; text-align: left; margin-top: 20px;">
                        <div class="spirit-card-sm">
                            <div style="font-size: 0.8rem; font-weight: 700; color: #00F0FF;">01. Seasonal Discovery</div>
                            <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 2px;">Scores Indian destinations by month, climate, and interest fit.</div>
                        </div>
                        <div class="spirit-card-sm">
                            <div style="font-size: 0.8rem; font-weight: 700; color: #06D6A0;">02. Open-Meteo Sync</div>
                            <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 2px;">Queries live weather forecasts and flags rain probabilities.</div>
                        </div>
                        <div class="spirit-card-sm">
                            <div style="font-size: 0.8rem; font-weight: 700; color: #FFB703;">03. Dijkstra Graph Engine</div>
                            <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 2px;">Computes shortest-path highway corridor waypoints and drive times.</div>
                        </div>
                        <div class="spirit-card-sm">
                            <div style="font-size: 0.8rem; font-weight: 700; color: #FF5470;">04. Budget & Safety Audit</div>
                            <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 2px;">Deterministic 4-tier cost allocation with dedicated safety buffer.</div>
                        </div>
                    </div>
                </div>
                """
            )

    # Modern Product Footer
    render_footer()


if __name__ == "__main__":
    main()
