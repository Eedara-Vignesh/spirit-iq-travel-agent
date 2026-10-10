"""
frontend/components/navbar.py
==============================
Professional 9-section navigation bar for SpiritIQ.
Supports:
1. Home
2. Plan My Trip (Prominent action)
3. Explore Destinations
4. My Itinerary
5. Transport & Tickets
6. Hotels & Stays
7. My Bookings
8. Travel Assistant
9. Profile / Settings

Preserves dark midnight-navy / electric-teal aesthetic and updates active session state.
"""

from __future__ import annotations

import streamlit as st
from frontend.components import render_html


NAV_ITEMS = [
    {"id": "home", "label": "Home", "icon": "🏠"},
    {"id": "plan_trip", "label": "Plan Trip", "icon": "✨"},
    {"id": "destinations", "label": "Destinations", "icon": "🌴"},
    {"id": "itinerary", "label": "Itinerary", "icon": "📅"},
    {"id": "transport", "label": "Transport", "icon": "🚆"},
    {"id": "hotels", "label": "Hotels", "icon": "🏨"},
    {"id": "bookings", "label": "Bookings", "icon": "💳"},
    {"id": "assistant", "label": "Assistant", "icon": "💬"},
    {"id": "profile", "label": "Settings", "icon": "⚙️"},
]


def render_navbar() -> str:
    """
    Renders top navigation bar and returns the current active section ID.
    Synchronizes with st.session_state.active_section.
    """
    if "active_section" not in st.session_state:
        st.session_state.active_section = "home"

    active_id = st.session_state.active_section

    # Custom Top Navbar Container
    render_html(
        f"""
        <div style="
            background: #FFFFFF;
            border-bottom: 1px solid #E2E8F0;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
            padding: 10px 18px;
            margin: -60px -20px 20px -20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 999;
        ">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.6rem;">✈️</span>
                <div>
                    <span style="font-family: 'Outfit', sans-serif; font-size: 1.3rem; font-weight: 800; color: #0F172A; letter-spacing: -0.02em;">
                        Spirit<span style="color: #0284C7;">IQ</span>
                    </span>
                    <span style="font-size: 0.72rem; color: #64748B; margin-left: 8px; border-left: 1px solid #E2E8F0; padding-left: 8px;">
                        End-to-End Travel AI
                    </span>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 0.8rem; color: #64748B;">Active: </span>
                <span style="font-size: 0.82rem; font-weight: 700; color: #0284C7; background: rgba(2, 132, 199, 0.08); padding: 4px 10px; border-radius: 999px; border: 1px solid rgba(2, 132, 199, 0.25);">
                    {next((item["label"] for item in NAV_ITEMS if item["id"] == active_id), "Home")}
                </span>
            </div>
        </div>
        """
    )

    # Streamlit Navigation Pills row
    cols = st.columns(len(NAV_ITEMS))
    for i, item in enumerate(NAV_ITEMS):
        with cols[i]:
            is_active = (item["id"] == active_id)
            btn_label = f"{item['icon']} {item['label']}"
            btn_type = "primary" if is_active else "secondary"

            if st.button(
                btn_label,
                key=f"nav_btn_{item['id']}",
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state.active_section = item["id"]
                st.rerun()


    render_html("<div style='margin-bottom: 20px;'></div>")
    return st.session_state.active_section
