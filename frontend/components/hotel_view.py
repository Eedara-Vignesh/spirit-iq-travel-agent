"""
frontend/components/hotel_view.py
=================================
Dedicated Hotels & Stays search and selection workflow.
Displays curated accommodation options, partner booking links, amenity filters,
and allows attaching selected properties directly to the trip's booking order.
"""

from __future__ import annotations

import datetime
from typing import List, Optional
import streamlit as st

from backend.schemas import HotelCategory, HotelOption, TripPlan
from backend.tools.booking_tool import booking_manager
from backend.tools.hotel_tool import search_hotels
from frontend.components import render_html


def render_hotel_section(plan: Optional[TripPlan] = None) -> None:
    """
    Renders hotel search filters, curated property cards, and selection controls.
    """
    render_html(
        """
        <div style="margin-bottom: 24px;">
            <div class="spirit-hero-badge">
                <span>🏨</span> Accommodation & Stays
            </div>
            <h2 style="font-size: 1.85rem; margin: 4px 0 6px 0; color: #0F172A;">
                Hotels, Heritage Haveli & Nature Resorts
            </h2>
            <p style="color: #475569; font-size: 0.95rem;">
                Browse curated verified properties matching your budget and comfort preferences. 
                Select a hotel to attach to your master itinerary and booking review.
            </p>
        </div>
        """
    )

    # Search and Filter Toolbar
    default_dest = (
        plan.destinations[0].name
        if (plan and plan.destinations)
        else (st.session_state.get("form_destination", "Kerala"))
    )

    with st.expander("🔍 Filter & Customise Accommodation Search", expanded=True):
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            hotel_dest = st.text_input("Destination / City", value=default_dest, key="hotel_search_dest")
        with col_f2:
            hotel_cat = st.selectbox(
                "Category",
                options=[c.value for c in HotelCategory],
                format_func=lambda x: f"🌟 {x.capitalize()}",
                index=0,
                key="hotel_filter_category",
            )
        with col_f3:
            max_rate = st.number_input(
                "Max Rate / Night (INR)",
                min_value=1000.0,
                max_value=100000.0,
                value=25000.0,
                step=2000.0,
                key="hotel_filter_budget",
            )
        with col_f4:
            rooms_count = st.number_input("Rooms Needed", min_value=1, max_value=10, value=1, key="hotel_rooms_count")

        amenity_options = ["Wi-Fi", "Swimming Pool", "Spa", "Breakfast Included", "Free Parking", "Air Conditioning", "Mountain View", "Beach Access"]
        selected_amenities = st.multiselect(
            "Desired Amenities",
            options=amenity_options,
            default=["Wi-Fi"],
            key="hotel_amenities_filter",
        )

    # Perform hotel search
    check_in = datetime.date.today() + datetime.timedelta(days=7)
    check_out = datetime.date.today() + datetime.timedelta(days=10)

    res = search_hotels(
        destination=hotel_dest,
        check_in_date=check_in,
        check_out_date=check_out,
        num_guests=2,
        num_rooms=int(rooms_count),
        preferred_category=HotelCategory(hotel_cat),
        max_budget_per_night_inr=float(max_rate),
        amenities_required=selected_amenities,
    )

    hotel_options: List[HotelOption] = res.data if (res.success and isinstance(res.data, list)) else []

    if not hotel_options:
        st.warning(f"No properties found matching all selected filters for '{hotel_dest}'. Loosening search...")
        res_fallback = search_hotels(destination=hotel_dest, num_guests=2, num_rooms=1)
        hotel_options = res_fallback.data if (res_fallback.success and isinstance(res_fallback.data, list)) else []

    st.subheader(f"🏨 Available Accommodations in {hotel_dest.title()} ({len(hotel_options)} Properties)")

    # Grid of Hotel Cards
    for i, hotel in enumerate(hotel_options):
        col_c1, col_c2 = st.columns([3, 1.2])

        is_current_selection = False
        if plan and plan.active_booking_order and plan.active_booking_order.selected_hotel:
            if plan.active_booking_order.selected_hotel.id == hotel.id:
                is_current_selection = True

        with col_c1:
            amenity_badges = "".join(
                f"<span style='background: #F1F5F9; color: #475569; border: 1px solid #E2E8F0; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; margin-right: 6px; margin-bottom: 4px; display: inline-block;'>{a}</span>"
                for a in hotel.amenities[:5]
            )

            border_highlight = "#0284C7" if is_current_selection else "#E2E8F0"
            selection_chip = "<span style='background: #0284C7; color: #FFFFFF; font-weight: 700; font-size: 0.72rem; padding: 2px 8px; border-radius: 4px; text-transform: uppercase;'>Selected for Booking</span>" if is_current_selection else ""

            render_html(
                f"""
                <div style="
                    background: #FFFFFF;
                    border: 1px solid {border_highlight};
                    border-radius: 14px;
                    padding: 18px 22px;
                    margin-bottom: 16px;
                    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
                        <div>
                            <span style="font-size: 0.75rem; font-weight: 700; color: #0284C7; text-transform: uppercase;">
                                {hotel.category.value.capitalize()} • ⭐ {hotel.rating:.1f}
                            </span>
                            &nbsp;{selection_chip}
                            <h3 style="font-size: 1.25rem; color: #0F172A; margin: 4px 0 2px 0;">
                                {hotel.name}
                            </h3>
                            <div style="color: #475569; font-size: 0.85rem; margin-bottom: 8px;">
                                📍 {hotel.location} • 🛏️ {hotel.room_type} (Capacity: {hotel.guest_capacity} guests)
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.4rem; font-weight: 800; color: #0284C7;">
                                ₹{hotel.price_per_night_inr:,.0f} <span style="font-size: 0.8rem; font-weight: 400; color: #64748B;">/ night</span>
                            </div>
                            <div style="font-size: 0.8rem; color: #64748B;">
                                Total Stay: <strong>₹{hotel.total_stay_cost_inr:,.0f}</strong>
                            </div>
                        </div>
                    </div>
                    <div style="margin: 8px 0 10px 0;">
                        {amenity_badges}
                    </div>
                    <div style="font-size: 0.78rem; color: #059669;">
                        🛡️ <strong>Cancellation:</strong> {hotel.cancellation_policy}
                    </div>

                </div>
                """
            )

        with col_c2:
            st.write("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            if hotel.booking_url:
                st.link_button(
                    f"🔗 View on {hotel.provider}",
                    hotel.booking_url,
                    use_container_width=True,
                )

            if is_current_selection:
                st.success("Selected Property", icon="✅")
            else:
                if st.button("➕ Select Hotel for Booking", key=f"sel_htl_{hotel.id}_{i}", use_container_width=True):
                    if plan and plan.active_booking_order:
                        # Attach hotel to order
                        plan.active_booking_order.selected_hotel = hotel
                        # Recalculate order totals
                        updated_order = booking_manager.create_or_get_order(
                            trip_title=plan.trip_title,
                            traveller_profile=plan.active_booking_order.traveller_profile,
                            selected_segments=plan.active_booking_order.selected_segments,
                            selected_hotel=hotel,
                            estimated_activities_inr=plan.active_booking_order.estimated_activities_inr,
                            estimated_food_inr=plan.active_booking_order.estimated_food_inr,
                        )
                        plan.active_booking_order = updated_order
                        st.toast(f"Attached '{hotel.name}' to your booking order!", icon="🏨")
                        st.session_state.active_section = "bookings"
                        st.rerun()
                    else:
                        st.info("Please plan a trip first to create an active booking order.")
