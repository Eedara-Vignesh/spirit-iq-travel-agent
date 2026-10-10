"""
frontend/components/connected_journey_view.py
=============================================
Connected Multi-Modal Journey Planning & Multi-Transport Tickets View.
Renders door-to-door multi-segment journeys, feeder transfers from tier-2/3 towns,
inter-hub transit, local hotel transfers, layover warnings, and verified booking handoffs.
"""

from __future__ import annotations

from typing import List, Optional
import streamlit as st

from backend.schemas import ConnectedJourney, JourneySegment, TransportMode, TripPlan
from backend.tools.booking_tool import booking_manager
from frontend.components import render_html


def render_connected_journey_section(plan: Optional[TripPlan] = None) -> None:
    """
    Renders connected multimodal journeys and transport ticketing hub.
    Allows users to compare air links, rail corridors, and highway options,
    inspect transfer warnings, open verified booking URLs, and attach journeys to their order.
    """
    render_html(
        """
        <div style="margin-bottom: 24px;">
            <div class="spirit-hero-badge">
                <span>🚆</span> Multi-Modal Connected Transit
            </div>
            <h2 style="font-size: 1.85rem; margin: 4px 0 6px 0; color: #0F172A;">
                Connected Multi-Leg Journeys & Ticket Booking
            </h2>
            <p style="color: #475569; font-size: 0.95rem;">
                Door-to-door multimodal routing. For non-metro origins, SpiritIQ resolves feeder road transfers 
                to regional air and rail junctions, computes transfer layovers, and provides official booking handoffs.
            </p>
        </div>
        """
    )

    if not plan or not plan.connected_journeys:
        render_html(
            """
            <div style="
                background: #FFFFFF;
                border: 1px dashed rgba(2, 132, 199, 0.4);
                border-radius: 14px;
                padding: 32px;
                text-align: center;
                margin: 20px 0;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
            ">
                <span style="font-size: 2.5rem;">🗺️</span>
                <h3 style="color: #0F172A; margin: 12px 0 6px 0;">No Active Connected Journey Plan</h3>
                <p style="color: #475569; max-width: 520px; margin: 0 auto 16px auto;">
                    Please go to <strong>Plan My Trip</strong> to enter your origin (e.g. Narasaraopeta) and destination (e.g. Kerala). 
                    SpiritIQ will automatically calculate multi-leg feeder transfers and intercity transit.
                </p>
            </div>
            """
        )
        if st.button("✨ Go to Plan My Trip", key="go_to_plan_from_transit", type="primary"):
            st.session_state.active_section = "plan_trip"
            st.rerun()
        return

    journeys: List[ConnectedJourney] = plan.connected_journeys

    # Route archetype selector tabs
    route_titles = [f"{j.route_type} (~₹{j.total_transit_cost_inr:,.0f})" for j in journeys]
    selected_tab_idx = st.radio(
        "Select Journey Archetype to Inspect:",
        options=range(len(journeys)),
        format_func=lambda idx: route_titles[idx],
        horizontal=True,
        key="selected_journey_radio",
    )

    active_journey = journeys[selected_tab_idx]

    # Journey Overview Card
    render_html(
        f"""
        <div style="
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-left: 4px solid #0284C7;
            border-radius: 16px;
            padding: 20px 24px;
            margin: 18px 0 24px 0;
            box-shadow: 0 2px 10px rgba(15, 23, 42, 0.05);
        ">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
                <div>
                    <span style="background: rgba(2, 132, 199, 0.08); color: #0284C7; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">
                        {active_journey.convenience_rating}
                    </span>
                    <h3 style="font-size: 1.4rem; color: #0F172A; margin: 8px 0 4px 0;">
                        {active_journey.route_type}
                    </h3>
                    <div style="color: #475569; font-size: 0.88rem;">
                        <strong>Route:</strong> {active_journey.origin} ➔ {active_journey.origin_hub or 'Hub'} ➔ {active_journey.destination_hub or 'Destination Hub'} ➔ {active_journey.final_destination}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 1.6rem; font-weight: 800; color: #0284C7;">
                        ₹{active_journey.total_transit_cost_inr:,.0f}
                    </div>
                    <div style="font-size: 0.82rem; color: #64748B;">
                        Total Door-to-Door Duration: <strong>{active_journey.total_duration_hours:.1f} hrs</strong>
                    </div>
                </div>
            </div>
        </div>
        """
    )

    # Multi-Leg Timeline
    st.subheader(f"📍 Journey Legs Breakdown ({len(active_journey.segments)} Sequential Legs)")

    for seg in active_journey.segments:
        mode_icons = {
            TransportMode.FLIGHT: "✈️",
            TransportMode.TRAIN: "🚆",
            TransportMode.BUS: "🚌",
            TransportMode.CAB: "🚕",
            TransportMode.SELF_DRIVE: "🚗",
            TransportMode.ANY: "🌐",
        }
        icon = mode_icons.get(seg.mode, "🚗")

        col_seg1, col_seg2 = st.columns([3, 1.2])

        with col_seg1:
            render_html(
                f"""
                <div style="
                    background: #FFFFFF;
                    border: 1px solid #E2E8F0;
                    border-left: 4px solid #0284C7;
                    border-radius: 12px;
                    padding: 16px 20px;
                    margin-bottom: 12px;
                    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
                ">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <span style="font-size: 0.78rem; font-weight: 700; color: #0284C7; text-transform: uppercase;">
                            Leg {seg.leg_number} • {seg.mode.value.capitalize()}
                        </span>
                        <span style="font-size: 0.78rem; background: #F1F5F9; border: 1px solid #E2E8F0; padding: 2px 8px; border-radius: 4px; color: #475569;">
                            {seg.availability_status}
                        </span>
                    </div>
                    <h4 style="font-size: 1.05rem; color: #0F172A; margin: 4px 0 6px 0;">
                        {icon} {seg.leg_title}
                    </h4>
                    <div style="font-size: 0.85rem; color: #334155; margin-bottom: 6px;">
                        <strong>From:</strong> {seg.origin} &nbsp;|&nbsp; <strong>To:</strong> {seg.destination}
                    </div>
                    <div style="display: flex; gap: 16px; font-size: 0.8rem; color: #64748B;">
                        <span>🏢 <strong>Provider:</strong> {seg.provider}</span>
                        <span>⏱️ <strong>Duration:</strong> {seg.duration_hours:.1f} hrs</span>

                        {f'<span>📏 <strong>Distance:</strong> {seg.distance_km:.0f} km</span>' if seg.distance_km else ''}
                        <span>💵 <strong>Fare:</strong> ₹{seg.estimated_cost_inr:,.0f}</span>
                    </div>
                    {f'<div style="margin-top: 8px; padding: 6px 10px; background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 6px; font-size: 0.78rem; color: #F59E0B;">⚠️ <strong>Transfer Warning:</strong> {seg.connection_warning}</div>' if seg.connection_warning else ''}
                </div>
                """
            )

        with col_seg2:
            st.write("<div style='height: 18px;'></div>", unsafe_allow_html=True)
            if seg.booking_url:
                st.link_button(
                    f"🔗 Search & Book {seg.provider}",
                    seg.booking_url,
                    use_container_width=True,
                )
            else:
                st.button(f"ℹ️ Provider Handoff", key=f"handoff_{seg.segment_id}", disabled=True, use_container_width=True)

    # Actions: Select This Journey for the Order
    st.divider()
    col_act1, col_act2 = st.columns([2.5, 1.5])
    with col_act1:
        st.info("💡 Selecting this connected route will automatically sync all feeder and transit segments into your active booking review order.")
    with col_act2:
        if st.button("✅ Select This Route for My Booking", key=f"sel_route_{active_journey.journey_id}", type="primary", use_container_width=True):
            # Update order segments in booking manager
            if plan.active_booking_order:
                plan.active_booking_order.selected_segments = active_journey.segments
                # Recalculate order totals
                updated_order = booking_manager.create_or_get_order(
                    trip_title=plan.trip_title,
                    traveller_profile=plan.active_booking_order.traveller_profile,
                    selected_segments=active_journey.segments,
                    selected_hotel=plan.active_booking_order.selected_hotel,
                    estimated_activities_inr=plan.active_booking_order.estimated_activities_inr,
                    estimated_food_inr=plan.active_booking_order.estimated_food_inr,
                )
                plan.active_booking_order = updated_order
            st.toast(f"Route '{active_journey.route_type}' attached to your booking order!", icon="🚆")
            st.session_state.active_section = "bookings"
            st.rerun()
