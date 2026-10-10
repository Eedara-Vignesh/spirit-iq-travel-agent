"""
frontend/components/trip_form.py
================================
Structured 6-section trip planning form with validation, sensible defaults,
destination quick-picks, live per-person budget cues, and state preservation.
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import Optional
import streamlit as st

from backend.schemas import (
    HotelCategory,
    TripRequest,
    TripType,
    TravelPace,
    TransportMode,
)
from backend.services.places_service import PlacesService
from frontend.components import render_html

places_service = PlacesService()

# Common Indian destination quick-picks
QUICK_DESTINATIONS = ["Goa", "Coorg", "Udaipur", "Ooty", "Jaipur", "Wayanad", "Manali", "Varkala"]


def render_trip_form() -> Optional[TripRequest]:
    """
    Render the 6-section trip planner form.
    Returns validated TripRequest when submitted and valid, or None otherwise.
    """
    # Ensure default session state keys exist
    if "form_origin" not in st.session_state:
        st.session_state.form_origin = "Bengaluru"
    if "form_destination" not in st.session_state:
        st.session_state.form_destination = "Goa"
    if "undecided_destination" not in st.session_state:
        st.session_state.undecided_destination = False

    render_html('<div id="trip-planner-section"></div>')

    # Form Container Banner
    render_html(
        """
        <div style="margin: 28px 0 18px 0;">
            <div class="spirit-hero-badge">
                <span>🎯</span> Intelligent Trip Architect
            </div>
            <h2 style="font-size: 1.85rem; margin-bottom: 4px; color: #0F172A;">Configure Your Travel Preferences</h2>
            <p style="color: #64748B; font-size: 0.95rem;">
                Customize your travel parameters across 6 modular dimensions. 
                Our backend coordinates Groq AI, Open-Meteo, and Dijkstra graph solvers to craft your route.
            </p>
        </div>
        """
    )

    # Destination Quick-Picks Bar
    render_html(
        """
        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 12px;">
            <span style="font-size: 0.8rem; font-weight: 600; color: #64748B;">Popular Suggestions:</span>
        </div>
        """
    )
    
    quick_cols = st.columns(len(QUICK_DESTINATIONS))
    for i, dest_name in enumerate(QUICK_DESTINATIONS):
        with quick_cols[i]:
            if st.button(f"{dest_name}", key=f"quick_dest_{i}", use_container_width=True):
                st.session_state.form_destination = dest_name
                st.session_state.undecided_destination = False
                st.session_state.form_destination_coords = None
                st.rerun()

    # Main Input Form
    with st.form("spirit_iq_trip_form", clear_on_submit=False):
        
        # -------------------------------------------------------------
        # Section 1: Origin & Destination Discovery
        # -------------------------------------------------------------
        render_html(
            """
            <div style="border-bottom: 1px solid #E2E8F0; padding-bottom: 10px; margin-bottom: 16px;">
                <span style="color: #0284C7; font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;">Section 1</span>
                <h3 style="font-size: 1.2rem; margin: 4px 0 0 0; color: #0F172A;">📍 Origin & Destination Discovery</h3>
            </div>
            """
        )
        col1_1, col1_2 = st.columns(2)
        with col1_1:
            origin = st.text_input(
                "Starting City / Origin *",
                value=st.session_state.form_origin,
                placeholder="e.g. Bengaluru, Mumbai, Delhi, Hyderabad, Chennai",
                help="Your journey departure point. Used for Dijkstra corridor graph calculations and transit pricing.",
            )
            if places_service.is_configured and len(origin.strip()) >= 3:
                origin_preds = places_service.get_place_predictions(origin.strip())
                if origin_preds:
                    st.caption("📍 *Verified Places:* " + " • ".join([p["main_text"] for p in origin_preds[:3]]))

            undecided_dest = st.checkbox(
                "I don't have a destination — recommend seasonal getaways! 🌟",
                value=st.session_state.undecided_destination,
                help="Enable AI destination discovery based on weather suitability, seasonal curves, and budget.",
            )
        with col1_2:
            destination = st.text_input(
                "Target Destination",
                value="" if undecided_dest else st.session_state.form_destination,
                placeholder="e.g. Goa, Coorg, Udaipur, Ooty, Manali",
                disabled=undecided_dest,
                help="Leave blank or select the discovery checkbox if you want SpiritIQ to recommend optimal locations.",
            )
            if undecided_dest:
                st.caption("✨ *Discovery mode activated: Groq & Destination Engine will score top 3 candidates.*")
            elif places_service.is_configured and len(destination.strip()) >= 3:
                dest_preds = places_service.get_place_predictions(destination.strip())
                if dest_preds:
                    st.caption("📍 *Verified Places:* " + " • ".join([p["main_text"] for p in dest_preds[:3]]))

        render_html("<div style='margin-bottom: 18px;'></div>")

        # -------------------------------------------------------------
        # Section 2: Travel Dates & Flexible Dates
        # -------------------------------------------------------------
        render_html(
            """
            <div style="border-bottom: 1px solid #E2E8F0; padding-bottom: 10px; margin-bottom: 16px;">
                <span style="color: #0284C7; font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;">Section 2</span>
                <h3 style="font-size: 1.2rem; margin: 4px 0 0 0; color: #0F172A;">🗓️ Travel Dates & Temporal Flexibility</h3>
            </div>
            """
        )
        col2_1, col2_2, col2_3 = st.columns([2, 2, 2])
        today = date.today()
        default_start = today + timedelta(days=7)
        default_end = today + timedelta(days=10)

        with col2_1:
            start_date = st.date_input("Start Date *", value=default_start, min_value=today)
        with col2_2:
            end_date = st.date_input("End Date *", value=default_end, min_value=today)
        with col2_3:
            st.write("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            is_flexible = st.checkbox("Flexible Dates (±2 Days)", value=True, help="Enables date flex matching for better transit and tariff options.")

        # Duration Indicator
        num_days = max(1, (end_date - start_date).days + 1)
        render_html(
            f"""
            <div style="font-size: 0.82rem; color: #64748B; margin-top: -6px; margin-bottom: 14px;">
                Calculated Trip Duration: <strong style="color: #0284C7;">{num_days} Day{'s' if num_days > 1 else ''}</strong>
                {' (with ±2 day elasticity window)' if is_flexible else ''}
            </div>
            """
        )

        render_html("<div style='margin-bottom: 18px;'></div>")

        # -------------------------------------------------------------
        # Section 3: Travellers & Group Type
        # -------------------------------------------------------------
        render_html(
            """
            <div style="border-bottom: 1px solid #E2E8F0; padding-bottom: 10px; margin-bottom: 16px;">
                <span style="color: #0284C7; font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;">Section 3</span>
                <h3 style="font-size: 1.2rem; margin: 4px 0 0 0; color: #0F172A;">👥 Travellers & Party Dynamic</h3>
            </div>
            """
        )
        col3_1, col3_2 = st.columns(2)
        with col3_1:
            trip_type = st.selectbox(
                "Party Dynamic",
                options=[t.value for t in TripType],
                format_func=lambda x: f"{x.capitalize()} Trip",
                index=0,
                help="Solo, couple, family, friends, or group.",
            )
        with col3_2:
            default_travelers = 1 if trip_type == "solo" else 2
            num_travellers = st.number_input(
                "Total Travellers",
                min_value=1,
                max_value=50,
                value=default_travelers,
                step=1,
            )

        render_html("<div style='margin-bottom: 18px;'></div>")

        # -------------------------------------------------------------
        # Section 4: Interests & Travel Pace
        # -------------------------------------------------------------
        render_html(
            """
            <div style="border-bottom: 1px solid #E2E8F0; padding-bottom: 10px; margin-bottom: 16px;">
                <span style="color: #0284C7; font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;">Section 4</span>
                <h3 style="font-size: 1.2rem; margin: 4px 0 0 0; color: #0F172A;">🎨 Interests & Travel Pace</h3>
            </div>
            """
        )
        col4_1, col4_2 = st.columns(2)
        with col4_1:
            all_interests = [
                "beaches", "mountains", "heritage", "local food",
                "trekking", "wildlife", "nightlife", "relaxation",
                "shopping", "water sports", "culture", "photography",
            ]
            selected_interests = st.multiselect(
                "Interests & Vacation Themes",
                options=all_interests,
                default=["beaches", "relaxation"] if not undecided_dest else ["mountains", "local food"],
                help="Select key experiences you desire. LLM prioritizes activities matching these tags.",
            )
        with col4_2:
            pace = st.selectbox(
                "Itinerary Velocity / Pace",
                options=[p.value for p in TravelPace],
                format_func=lambda x: {
                    "relaxed": "🌿 Relaxed (1-2 unhurried activities daily)",
                    "balanced": "⚖️ Balanced (2-3 curated activities daily)",
                    "packed": "⚡ Packed (3-5 high-energy sightseeing stops)",
                }.get(x, x.capitalize()),
                index=1,
            )

        render_html("<div style='margin-bottom: 18px;'></div>")

        # -------------------------------------------------------------
        # Section 5: Budget & Transport Preferences
        # -------------------------------------------------------------
        render_html(
            """
            <div style="border-bottom: 1px solid #E2E8F0; padding-bottom: 10px; margin-bottom: 16px;">
                <span style="color: #0284C7; font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;">Section 5</span>
                <h3 style="font-size: 1.2rem; margin: 4px 0 0 0; color: #0F172A;">💰 Budget & Transit Preferences</h3>
            </div>
            """
        )
        col5_1, col5_2 = st.columns(2)
        with col5_1:
            budget_inr = st.number_input(
                "Total Budget (INR) *",
                min_value=2000.0,
                max_value=2000000.0,
                value=35000.0,
                step=2500.0,
                format="%.0f",
                help="Overall spending budget for accommodation, food, activities, and transit.",
            )
            per_person_est = budget_inr / max(1, num_travellers)
            render_html(
                f"""
                <div style="font-size: 0.8rem; color: #059669; font-weight: 600; margin-top: -4px;">
                    Estimated Allocation: <strong>₹{per_person_est:,.0f}</strong> per traveller ({num_days} days)
                </div>
                """
            )
        with col5_2:
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
                    "any": "🌐 Any / Optimal Mode",
                }.get(x, x.capitalize()),
            )

        render_html("<div style='margin-bottom: 18px;'></div>")

        # -------------------------------------------------------------
        # Section 5b: Accommodation & Hotel Preferences
        # -------------------------------------------------------------
        render_html(
            """
            <div style="border-bottom: 1px solid #E2E8F0; padding-bottom: 10px; margin-bottom: 16px;">
                <span style="color: #0284C7; font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;">Section 5b</span>
                <h3 style="font-size: 1.2rem; margin: 4px 0 0 0; color: #0F172A;">🏨 Accommodation & Stays Preferences</h3>
            </div>
            """
        )
        col5b_1, col5b_2, col5b_3 = st.columns(3)
        with col5b_1:
            hotel_required = st.checkbox("Hotel Required", value=True, help="Include curated hotel recommendations and bookings.")
            num_rooms = st.number_input("Number of Rooms Needed", min_value=1, max_value=10, value=1, step=1)
        with col5b_2:
            hotel_cat_val = st.selectbox(
                "Preferred Category",
                options=["any", "budget", "boutique", "luxury", "resort", "homestay"],
                format_func=lambda x: f"🌟 {x.capitalize()}",
                index=0,
            )
        with col5b_3:
            hotel_amenities = st.multiselect(
                "Desired Amenities",
                options=["Wi-Fi", "Swimming Pool", "Breakfast Included", "Free Parking", "Spa", "Air Conditioning"],
                default=["Wi-Fi", "Breakfast Included"],
            )

        render_html("<div style='margin-bottom: 18px;'></div>")

        # -------------------------------------------------------------
        # Section 6: Accessibility & Special Requirements
        # -------------------------------------------------------------
        render_html(
            """
            <div style="border-bottom: 1px solid #E2E8F0; padding-bottom: 10px; margin-bottom: 16px;">
                <span style="color: #0284C7; font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;">Section 6</span>
                <h3 style="font-size: 1.2rem; margin: 4px 0 0 0; color: #0F172A;">🛡️ Special Requirements & Accessibility</h3>
            </div>
            """
        )
        special_requirements = st.text_area(
            "Special Notes, Dietary Preferences, or Accessibility Guidelines (Optional)",
            value="",
            placeholder="e.g. Pure Vegetarian or Jain food options required, wheelchair friendly hotels, traveling with infant, preference for sea-view rooms...",
            help="SpiritIQ Groq agent will factor these constraints into activity suggestions and restaurant selections.",
        )

        render_html("<div style='margin-top: 24px;'></div>")

        # Submit CTA
        submitted = st.form_submit_button(
            "✨ Generate My Personalized Travel Plan 🚀",
            use_container_width=True,
            type="primary",
        )

    # Validation & Model Assembly
    if submitted:
        if not origin.strip():
            st.error("⚠️ Please specify a valid origin city (e.g. Bengaluru, Mumbai).")
            return None

        if end_date < start_date:
            st.error("⚠️ End date cannot be prior to the start date.")
            return None

        if not undecided_dest and not destination.strip():
            st.error("⚠️ Please enter a preferred destination or check 'I don't have a destination' for automated discovery.")
            return None

        target_dest = None if (undecided_dest or not destination.strip()) else destination.strip()
        transport_modes = [TransportMode(m) for m in transport_pref] if transport_pref else [TransportMode.ANY]

        # Resolve fresh coordinates via PlacesService when configured, preventing stale data
        origin_coords = None
        dest_coords = None
        if places_service.is_configured:
            origin_coords = places_service.resolve_coordinates(origin.strip())
            if target_dest:
                dest_coords = places_service.resolve_coordinates(target_dest)

        # Preserve validated user inputs and fresh coordinates in session state
        st.session_state.form_origin = origin.strip()
        st.session_state.form_origin_coords = origin_coords
        if target_dest:
            st.session_state.form_destination = target_dest
            st.session_state.form_destination_coords = dest_coords
        else:
            st.session_state.form_destination = ""
            st.session_state.form_destination_coords = None
        st.session_state.undecided_destination = undecided_dest

        try:
            req = TripRequest(
                origin=origin.strip(),
                destination=target_dest,
                origin_coordinates=origin_coords,
                destination_coordinates=dest_coords,
                start_date=start_date,
                end_date=end_date,
                trip_type=TripType(trip_type),
                num_travellers=int(num_travellers),
                budget_inr=float(budget_inr),
                interests=selected_interests,
                pace=TravelPace(pace),
                transport_preferences=transport_modes,
                hotel_required=hotel_required,
                hotel_category=HotelCategory(hotel_cat_val) if hotel_cat_val != "any" else None,
                num_rooms=int(num_rooms),
                hotel_amenities=hotel_amenities,
                special_requirements=special_requirements.strip() if special_requirements.strip() else None,
                is_flexible_dates=is_flexible,
                date_flexibility_days=2 if is_flexible else 0,
            )
            return req
        except Exception as exc:
            st.error(f"⚠️ Validation error: {exc}")
            return None

    return None
