"""
frontend/components/trip_form.py
================================
Travel Request Panel for SpiritIQ AI Planning Agent.
Structured 6-section parameters panel with quick presets, live per-person
allocation calculations, client-side validation, and session preservation.
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import Optional
import streamlit as st

from backend.schemas import (
    TripRequest,
    TripType,
    TravelPace,
    TransportMode,
)
from frontend.components import render_html

# Starter templates for one-click agent exploration
PRESETS = [
    {
        "label": "🌴 Goa Coastal Weekend",
        "origin": "Bengaluru",
        "destination": "Goa",
        "days": 3,
        "trip_type": "couple",
        "travellers": 2,
        "budget": 35000.0,
        "pace": "relaxed",
        "interests": ["beaches", "relaxation", "local food"],
    },
    {
        "label": "☕ Coorg Coffee Trail",
        "origin": "Bengaluru",
        "destination": "Coorg",
        "days": 3,
        "trip_type": "friends",
        "travellers": 3,
        "budget": 24000.0,
        "pace": "balanced",
        "interests": ["mountains", "trekking", "nature"],
    },
    {
        "label": "🏰 Royal Udaipur Heritage",
        "origin": "Delhi",
        "destination": "Udaipur",
        "days": 4,
        "trip_type": "family",
        "travellers": 4,
        "budget": 50000.0,
        "pace": "balanced",
        "interests": ["heritage", "palaces", "culture", "local food"],
    },
]


def render_trip_form() -> Optional[TripRequest]:
    """
    Render the Agent Travel Request Panel.
    Returns validated TripRequest when submitted, or None otherwise.
    """
    # Ensure default session state keys exist
    if "form_origin" not in st.session_state:
        st.session_state.form_origin = "Bengaluru"
    if "form_destination" not in st.session_state:
        st.session_state.form_destination = "Goa"
    if "undecided_destination" not in st.session_state:
        st.session_state.undecided_destination = False
    if "form_budget" not in st.session_state:
        st.session_state.form_budget = 35000.0
    if "form_travellers" not in st.session_state:
        st.session_state.form_travellers = 2
    if "form_trip_type" not in st.session_state:
        st.session_state.form_trip_type = "couple"
    if "form_pace" not in st.session_state:
        st.session_state.form_pace = "balanced"
    if "form_interests" not in st.session_state:
        st.session_state.form_interests = ["beaches", "relaxation"]

    render_html(
        """
        <div style="margin-bottom: 14px;">
            <div class="spirit-hero-badge">
                <span>🤖</span> Autonomous Agent Input
            </div>
            <h2 style="font-size: 1.4rem; margin-bottom: 4px; color: #FFFFFF;">Travel Request Panel</h2>
            <p style="color: #94A3B8; font-size: 0.82rem; margin-bottom: 12px;">
                Specify your constraints below. The agent will orchestrate Open-Meteo, Dijkstra corridor routing,
                and Gemini AI synthesis over the verified data.
            </p>
        </div>
        """
    )

    # Preset Quick-Load Bar
    render_html(
        """
        <div style="font-size: 0.76rem; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 6px;">
            Quick Templates:
        </div>
        """
    )
    p_cols = st.columns(len(PRESETS))
    for i, p in enumerate(PRESETS):
        with p_cols[i]:
            if st.button(p["label"], key=f"preset_btn_{i}", use_container_width=True):
                st.session_state.form_origin = p["origin"]
                st.session_state.form_destination = p["destination"]
                st.session_state.undecided_destination = False
                st.session_state.form_budget = p["budget"]
                st.session_state.form_travellers = p["travellers"]
                st.session_state.form_trip_type = p["trip_type"]
                st.session_state.form_pace = p["pace"]
                st.session_state.form_interests = p["interests"]
                st.rerun()

    # Form with 6 Organized Sections
    with st.form("agent_travel_request_form", clear_on_submit=False):
        
        # Section 1: Origin & Destination
        render_html(
            """
            <div style="border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 6px; margin: 12px 0 10px 0;">
                <span style="color: #00F0FF; font-weight: 700; font-size: 0.8rem; text-transform: uppercase;">1. Destination & Origin</span>
            </div>
            """
        )
        c1, c2 = st.columns(2)
        with c1:
            origin = st.text_input(
                "Origin City *",
                value=st.session_state.form_origin,
                placeholder="e.g. Bengaluru, Mumbai, Delhi",
                help="Starting hub for route corridor calculations.",
            )
            undecided = st.checkbox(
                "Help me choose destination (AI Discovery)",
                value=st.session_state.undecided_destination,
                help="Agent will score seasonal getaways matching your month and budget.",
            )
        with c2:
            destination = st.text_input(
                "Destination",
                value="" if undecided else st.session_state.form_destination,
                placeholder="e.g. Goa, Coorg, Udaipur, Ooty",
                disabled=undecided,
                help="Leave empty or check 'Help me choose' to let agent discover.",
            )

        # Section 2: Dates & Flexibility
        render_html(
            """
            <div style="border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 6px; margin: 12px 0 10px 0;">
                <span style="color: #00F0FF; font-weight: 700; font-size: 0.8rem; text-transform: uppercase;">2. Travel Timeline</span>
            </div>
            """
        )
        d1, d2, d3 = st.columns([2, 2, 2])
        today = date.today()
        default_start = today + timedelta(days=7)
        default_end = today + timedelta(days=10)
        with d1:
            start_date = st.date_input("Start Date *", value=default_start, min_value=today)
        with d2:
            end_date = st.date_input("End Date *", value=default_end, min_value=today)
        with d3:
            st.write("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            is_flexible = st.checkbox("Flexible Dates (±2 Days)", value=True)

        num_days = max(1, (end_date - start_date).days + 1)
        render_html(
            f"""
            <div style="font-size: 0.78rem; color: #94A3B8; margin-top: -6px; margin-bottom: 10px;">
                Duration: <strong style="color: #00F0FF;">{num_days} Days</strong>
                {' (±2 days flex window)' if is_flexible else ''}
            </div>
            """
        )

        # Section 3: Travellers & Dynamic
        render_html(
            """
            <div style="border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 6px; margin: 12px 0 10px 0;">
                <span style="color: #00F0FF; font-weight: 700; font-size: 0.8rem; text-transform: uppercase;">3. Travellers & Group Dynamic</span>
            </div>
            """
        )
        t1, t2 = st.columns(2)
        with t1:
            trip_type_options = [t.value for t in TripType]
            default_tt_idx = trip_type_options.index(st.session_state.form_trip_type) if st.session_state.form_trip_type in trip_type_options else 1
            trip_type = st.selectbox(
                "Group Dynamic",
                options=trip_type_options,
                format_func=lambda x: f"{x.capitalize()} Trip",
                index=default_tt_idx,
            )
        with t2:
            num_travellers = st.number_input(
                "Travellers Count",
                min_value=1,
                max_value=50,
                value=st.session_state.form_travellers,
                step=1,
            )

        # Section 4: Budget & Transport
        render_html(
            """
            <div style="border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 6px; margin: 12px 0 10px 0;">
                <span style="color: #00F0FF; font-weight: 700; font-size: 0.8rem; text-transform: uppercase;">4. Budget & Transit Preferences</span>
            </div>
            """
        )
        b1, b2 = st.columns(2)
        with b1:
            budget_inr = st.number_input(
                "Total Budget (INR) *",
                min_value=2000.0,
                max_value=2000000.0,
                value=st.session_state.form_budget,
                step=2500.0,
                format="%.0f",
            )
            per_person_calc = budget_inr / max(1, num_travellers)
            render_html(
                f"""
                <div style="font-size: 0.78rem; color: #06D6A0; margin-top: -4px;">
                    Estimated: <strong>₹{per_person_calc:,.0f}</strong> / traveller ({num_days} days)
                </div>
                """
            )
        with b2:
            transport_pref = st.multiselect(
                "Preferred Transport Modes",
                options=[m.value for m in TransportMode],
                default=["any"],
                format_func=lambda x: {
                    "flight": "✈️ Flight",
                    "train": "🚆 Train",
                    "bus": "🚌 Bus",
                    "cab": "🚕 Cab / Taxi",
                    "self_drive": "🚗 Self Drive",
                    "any": "🌐 Any / Best Route",
                }.get(x, x.capitalize()),
            )

        # Section 5: Interests & Pace
        render_html(
            """
            <div style="border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 6px; margin: 12px 0 10px 0;">
                <span style="color: #00F0FF; font-weight: 700; font-size: 0.8rem; text-transform: uppercase;">5. Interests & Velocity</span>
            </div>
            """
        )
        i1, i2 = st.columns(2)
        with i1:
            all_interests = [
                "beaches", "mountains", "heritage", "local food",
                "trekking", "wildlife", "nightlife", "relaxation",
                "shopping", "water sports", "culture", "photography",
            ]
            default_interests = [i for i in st.session_state.form_interests if i in all_interests] or ["beaches", "relaxation"]
            selected_interests = st.multiselect(
                "Interests & Themes",
                options=all_interests,
                default=default_interests,
            )
        with i2:
            pace_options = [p.value for p in TravelPace]
            pace_idx = pace_options.index(st.session_state.form_pace) if st.session_state.form_pace in pace_options else 1
            pace = st.selectbox(
                "Travel Pace",
                options=pace_options,
                format_func=lambda x: {
                    "relaxed": "🌿 Relaxed (1-2 activities/day)",
                    "balanced": "⚖️ Balanced (2-3 activities/day)",
                    "packed": "⚡ Packed (3-5 activities/day)",
                }.get(x, x.capitalize()),
                index=pace_idx,
            )

        # Section 6: Special Notes
        render_html(
            """
            <div style="border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 6px; margin: 12px 0 10px 0;">
                <span style="color: #00F0FF; font-weight: 700; font-size: 0.8rem; text-transform: uppercase;">6. Accessibility & Dietary</span>
            </div>
            """
        )
        special_requirements = st.text_area(
            "Special Notes (Optional)",
            value="",
            placeholder="e.g. Vegetarian / Jain food, wheelchair friendly, travelling with toddler...",
        )

        render_html("<div style='margin-top: 14px;'></div>")
        submitted = st.form_submit_button(
            "🚀 Launch AI Planning Agent",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        if not origin.strip():
            st.error("⚠️ Please specify a valid departure city (e.g. Bengaluru, Mumbai).")
            return None

        if end_date < start_date:
            st.error("⚠️ End date cannot be prior to start date.")
            return None

        if not undecided and not destination.strip():
            st.error("⚠️ Please enter a destination or check 'Help me choose destination'.")
            return None

        target_dest = None if (undecided or not destination.strip()) else destination.strip()
        transport_modes = [TransportMode(m) for m in transport_pref] if transport_pref else [TransportMode.ANY]

        # Update session state with submitted values
        st.session_state.form_origin = origin.strip()
        st.session_state.form_destination = target_dest or ""
        st.session_state.undecided_destination = undecided
        st.session_state.form_budget = float(budget_inr)
        st.session_state.form_travellers = int(num_travellers)
        st.session_state.form_trip_type = trip_type
        st.session_state.form_pace = pace
        st.session_state.form_interests = selected_interests

        try:
            req = TripRequest(
                origin=origin.strip(),
                destination=target_dest,
                start_date=start_date,
                end_date=end_date,
                trip_type=TripType(trip_type),
                num_travellers=int(num_travellers),
                budget_inr=float(budget_inr),
                interests=selected_interests,
                pace=TravelPace(pace),
                transport_preferences=transport_modes,
                special_requirements=special_requirements.strip() if special_requirements.strip() else None,
                is_flexible_dates=is_flexible,
                date_flexibility_days=2 if is_flexible else 0,
            )
            return req
        except Exception as exc:
            st.error(f"⚠️ Validation error: {exc}")
            return None

    return None
