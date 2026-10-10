"""
frontend/components/booking_view.py
===================================
Booking Workflow & Payment Approval Gate View.
Enforces:
1. Itemized price review (Transport, Stay, Activities, Taxes, Total Payable).
2. Explicit User Approval Gate before any handoff or checkout action.
3. Multi-provider disclosures (separate payments per transport / hotel operator).
4. Direct partner checkout handoff links.
5. Provider confirmation verification to reach CONFIRMED state.
6. Safe order cancellation.
"""

from __future__ import annotations

from typing import Optional
import streamlit as st

from backend.schemas import BookingStatus, TripPlan
from backend.tools.booking_tool import booking_manager
from frontend.components import render_html


def render_booking_section(plan: Optional[TripPlan] = None) -> None:
    """
    Renders master booking workflow, itemized pricing audit,
    traveller details, and explicit user approval payment gate.
    """
    render_html(
        """
        <div style="margin-bottom: 24px;">
            <div class="spirit-hero-badge">
                <span>💳</span> Booking Engine & Payment Gate
            </div>
            <h2 style="font-size: 1.85rem; margin: 4px 0 6px 0; color: #0F172A;">
                Booking Review & Payment Approval Gate
            </h2>
            <p style="color: #64748B; font-size: 0.95rem;">
                Review itemized fares, verify traveller contact info, and inspect provider terms.
                <strong>SpiritIQ strictly halts at the payment gate</strong> until you explicitly authorise the handoff.
            </p>
        </div>
        """
    )

    if not plan or not plan.active_booking_order:
        render_html(
            """
            <div style="
                background: #FFFFFF;
                border: 1px dashed #CBD5E1;
                border-radius: 14px;
                padding: 32px;
                text-align: center;
                margin: 20px 0;
                box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
            ">
                <span style="font-size: 2.5rem;">📋</span>
                <h3 style="color: #0F172A; margin: 12px 0 6px 0;">No Active Booking Order</h3>
                <p style="color: #64748B; max-width: 520px; margin: 0 auto 16px auto;">
                    Please go to <strong>Plan My Trip</strong> to configure and generate an itinerary. 
                    SpiritIQ will automatically prepare your itemized booking draft.
                </p>
            </div>
            """
        )
        if st.button("✨ Start Planning My Trip", key="go_to_plan_from_booking", type="primary"):
            st.session_state.active_section = "plan_trip"
            st.rerun()
        return

    order = plan.active_booking_order

    # Status State Banner
    status_colors = {
        BookingStatus.DRAFT: "#64748B",
        BookingStatus.AWAITING_USER_REVIEW: "#0284C7",
        BookingStatus.AWAITING_USER_APPROVAL: "#D97706",
        BookingStatus.REDIRECTED_TO_PROVIDER: "#7C3AED",
        BookingStatus.CONFIRMED: "#059669",
        BookingStatus.FAILED: "#DC2626",
        BookingStatus.CANCELLED: "#64748B",
    }
    badge_color = status_colors.get(order.status, "#0284C7")

    render_html(
        f"""
        <div style="
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-left: 6px solid {badge_color};
            border-radius: 14px;
            padding: 18px 24px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
        ">
            <div>
                <div style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase;">
                    Order Reference: {order.order_id}
                </div>
                <h3 style="font-size: 1.35rem; color: #0F172A; margin: 2px 0 0 0;">
                    {order.trip_title}
                </h3>
            </div>
            <div style="text-align: right;">
                <span style="
                    background: {badge_color}18;
                    color: {badge_color};
                    border: 1px solid {badge_color}44;
                    padding: 6px 14px;
                    border-radius: 999px;
                    font-size: 0.85rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.04em;
                ">
                    Status: {order.status.value.replace('_', ' ').title()}
                </span>
            </div>
        </div>
        """
    )

    # 2 Column Layout: Details & Itemized Summary
    col_left, col_right = st.columns([1.8, 1.2])

    with col_left:
        # Section A: Selected Transport Segments
        st.subheader("🚆 Selected Transport Segments")
        if order.selected_segments:
            for seg in order.selected_segments:
                render_html(
                    f"""
                    <div style="
                        background: #FFFFFF;
                        border: 1px solid #E2E8F0;
                        border-radius: 10px;
                        padding: 12px 16px;
                        margin-bottom: 10px;
                        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.03);
                    ">
                        <div style="display: flex; justify-content: space-between; font-weight: 600; color: #0F172A;">
                            <span>Leg {seg.leg_number}: {seg.leg_title}</span>
                            <span style="color: #0284C7; font-weight: 700;">₹{seg.estimated_cost_inr:,.0f}</span>
                        </div>
                        <div style="font-size: 0.82rem; color: #64748B; margin-top: 4px;">
                            Carrier: {seg.provider} • Mode: {seg.mode.value.capitalize()} • Duration: {seg.duration_hours:.1f} hrs
                        </div>
                    </div>
                    """
                )
        else:
            st.caption("No specific transport segments selected yet. (Visit Transport & Tickets to select).")

        # Section B: Selected Hotel
        st.subheader("🏨 Selected Accommodation")
        if order.selected_hotel:
            hotel = order.selected_hotel
            render_html(
                f"""
                <div style="
                    background: #FFFFFF;
                    border: 1px solid #E2E8F0;
                    border-radius: 10px;
                    padding: 12px 16px;
                    margin-bottom: 16px;
                    box-shadow: 0 2px 6px rgba(15, 23, 42, 0.03);
                ">
                    <div style="display: flex; justify-content: space-between; font-weight: 600; color: #0F172A;">
                        <span>{hotel.name}</span>
                        <span style="color: #0284C7; font-weight: 700;">₹{hotel.total_stay_cost_inr:,.0f}</span>
                    </div>
                    <div style="font-size: 0.82rem; color: #64748B; margin-top: 4px;">
                        {hotel.room_type} • {hotel.location} • Provider: {hotel.provider}
                    </div>
                    <div style="font-size: 0.78rem; color: #059669; font-weight: 600; margin-top: 4px;">
                        🛡️ {hotel.cancellation_policy}
                    </div>
                </div>
                """
            )
        else:
            st.caption("No hotel attached yet. (Visit Hotels & Stays to choose your property).")

        # Section C: Traveller Profile Review
        st.subheader("👤 Primary Traveller & Guest Information")
        profile = order.traveller_profile
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            traveller_name = st.text_input("Lead Traveller Name", value=profile.primary_contact_name if profile else "Guest Traveller")
            traveller_phone = st.text_input("Contact Phone", value=profile.phone if profile else "+91 9876543210")
        with col_p2:
            traveller_email = st.text_input("Notification Email", value=profile.email if profile else "guest@internal.travel")
            special_notes = st.text_input("Special Requests", value=profile.special_notes if (profile and profile.special_notes) else "None")

    with col_right:
        # Itemized Cost Breakdown Card
        render_html(
            f"""
            <div style="
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 14px;
                padding: 20px 24px;
                box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
            ">
                <div style="font-size: 0.82rem; font-weight: 700; color: #0284C7; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;">
                    💰 Itemized Financial Audit
                </div>
                <div style="display: flex; justify-content: space-between; padding: 6px 0; color: #475569; font-size: 0.9rem;">
                    <span>Transport Tickets Total:</span>
                    <strong style="color: #0F172A;">₹{order.itemised_transport_inr:,.0f}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 6px 0; color: #475569; font-size: 0.9rem;">
                    <span>Hotel Accommodation Total:</span>
                    <strong style="color: #0F172A;">₹{order.itemised_hotel_inr:,.0f}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 6px 0; color: #475569; font-size: 0.9rem;">
                    <span>Estimated Activities:</span>
                    <strong style="color: #0F172A;">₹{order.estimated_activities_inr:,.0f}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 6px 0; color: #475569; font-size: 0.9rem;">
                    <span>Estimated Meals & Dining:</span>
                    <strong style="color: #0F172A;">₹{order.estimated_food_inr:,.0f}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 6px 0; color: #475569; font-size: 0.9rem;">
                    <span>Taxes & GST (Transport + Hotel):</span>
                    <strong style="color: #0F172A;">₹{order.taxes_and_fees_inr:,.0f}</strong>
                </div>
                <hr style="border: 0; border-top: 1px solid #E2E8F0; margin: 12px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 4px 0;">
                    <span style="font-size: 1.05rem; font-weight: 700; color: #0F172A;">Total Payable:</span>
                    <span style="font-size: 1.55rem; font-weight: 800; color: #0284C7;">₹{order.total_payable_inr:,.0f}</span>
                </div>
            </div>
            """
        )

        st.write("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # Provider Terms & Separate Payment Disclosure
        with st.expander("ℹ️ Multi-Provider Checkout Disclosures", expanded=True):
            for note in order.provider_handoff_notes:
                st.caption(f"• {note}")

    st.divider()

    # =========================================================================
    # Step 6: Mandatory Payment Approval Gate
    # =========================================================================
    st.subheader("🛡️ Explicit Payment Approval Gate (Step 6)")

    if order.status in (BookingStatus.DRAFT, BookingStatus.AWAITING_USER_REVIEW, BookingStatus.AWAITING_USER_APPROVAL):
        render_html(
            """
            <div style="
                background: #FFFBEB;
                border: 1px solid #FDE68A;
                border-left: 5px solid #D97706;
                border-radius: 12px;
                padding: 16px 20px;
                margin-bottom: 16px;
            ">
                <h4 style="color: #B45309; margin: 0 0 6px 0; font-size: 1rem; font-weight: 700;">
                    ⚠️ Explicit User Authorisation Required
                </h4>
                <div style="font-size: 0.88rem; color: #475569; line-height: 1.5;">
                    SpiritIQ is an ethical travel assistant. We <strong>never execute automatic charges</strong> or store your payment instruments. 
                    Before opening authorized provider checkout sessions, you must review the itemized breakdown and confirm your approval below.
                </div>
            </div>
            """
        )

        approval_checkbox = st.checkbox(
            "I have reviewed the itemized route, hotel, and pricing breakdown. I explicitly authorize SpiritIQ to proceed to provider booking handoffs.",
            key=f"chk_approval_{order.order_id}",
        )

        col_gate1, col_gate2 = st.columns([2, 1])
        with col_gate1:
            if st.button(
                "🚀 Authorize & Proceed to Provider Checkout Gate",
                type="primary",
                disabled=not approval_checkbox,
                use_container_width=True,
                key=f"btn_approve_{order.order_id}",
            ):
                booking_manager.request_approval_gate(order.order_id)
                res_app = booking_manager.approve_booking(order.order_id, user_confirmed=True)
                if res_app.success:
                    order.user_explicitly_approved = True
                    order.status = BookingStatus.REDIRECTED_TO_PROVIDER
                    st.toast("Authorization recorded! Proceeding to provider checkout.", icon="🛡️")
                    st.rerun()
                else:
                    st.error(f"Approval error: {res_app.error}")

        with col_gate2:
            if st.button("❌ Cancel Order", key=f"btn_cancel_{order.order_id}", use_container_width=True):
                booking_manager.cancel_order(order.order_id, "Cancelled by user")
                st.rerun()

    elif order.status == BookingStatus.REDIRECTED_TO_PROVIDER:
        render_html(
            f"""
            <div style="
                background: #F0FDF4;
                border: 1px solid #BBF7D0;
                border-left: 5px solid #059669;
                border-radius: 12px;
                padding: 18px 24px;
                margin-bottom: 20px;
            ">
                <div style="color: #059669; font-weight: 700; font-size: 0.9rem; text-transform: uppercase;">
                    ✅ Payment Gate Authorized by Traveller
                </div>
                <div style="font-size: 0.85rem; color: #475569; margin-top: 4px;">
                    Approved on: {order.approval_timestamp.strftime('%Y-%m-%d %H:%M:%S') if order.approval_timestamp else 'Recent Session'}
                </div>
                <p style="color: #64748B; font-size: 0.88rem; margin: 8px 0 0 0;">
                    Please complete payment on each authorized provider link below. Once issued, enter your official booking reference/PNR to mark confirmed.
                </p>
            </div>
            """
        )

        # Provider checkout links
        st.subheader("🔗 Authorized Provider Checkout Links")
        cols_handoff = st.columns(3)
        h_idx = 0

        if order.selected_segments:
            for s in order.selected_segments:
                if s.booking_url:
                    with cols_handoff[h_idx % 3]:
                        st.link_button(f"🎫 Book {s.provider} ({s.mode.value.title()})", s.booking_url, use_container_width=True)
                    h_idx += 1

        if order.selected_hotel and order.selected_hotel.booking_url:
            with cols_handoff[h_idx % 3]:
                st.link_button(f"🏨 Book {order.selected_hotel.name}", order.selected_hotel.booking_url, use_container_width=True)

        st.divider()

        # Confirmation Entry
        st.subheader("🎟️ Provider Confirmation Verification")
        conf_ref = st.text_input("Enter Provider PNR / Booking Confirmation Reference:", placeholder="e.g. IRCTC-PNR-884920194 or BKG-99201")
        if st.button("✅ Confirm Verified Booking", type="primary"):
            c_res = booking_manager.confirm_provider_success(order.order_id, conf_ref)
            if c_res.success:
                st.toast("Booking marked as CONFIRMED!", icon="🎉")
                st.rerun()
            else:
                st.error(c_res.error)

    elif order.status == BookingStatus.CONFIRMED:
        st.balloons()
        render_html(
            f"""
            <div style="
                background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
                border: 2px solid #059669;
                border-radius: 16px;
                padding: 28px;
                text-align: center;
                margin: 20px 0;
            ">
                <span style="font-size: 3rem;">🎉</span>
                <h2 style="color: #065F46; margin: 10px 0 4px 0;">Booking Confirmed!</h2>
                <p style="color: #047857; font-size: 1rem; max-width: 500px; margin: 0 auto 12px auto;">
                    Your connected journey and stay have been verified with authorized providers.
                </p>
                <div style="font-size: 0.85rem; color: #065F46; background: rgba(255,255,255,0.7); border: 1px solid #A7F3D0; padding: 8px 16px; border-radius: 8px; display: inline-block;">
                    Order Reference: <strong>{order.order_id}</strong>
                </div>
            </div>
            """
        )
