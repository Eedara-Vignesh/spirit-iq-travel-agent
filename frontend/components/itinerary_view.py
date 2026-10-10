"""
frontend/components/itinerary_view.py
=====================================
Renders day-wise itinerary schedule, activity cards, and discovered destinations.
"""

from __future__ import annotations
from typing import List, Optional
import streamlit as st

from backend.schemas import TripPlan, DayPlan, DestinationRecommendation
from frontend.components import render_html


def render_itinerary_section(plan: TripPlan) -> None:
    """Render discovered destination candidates and day-wise schedule."""
    
    # 1. Destination candidates (if in discovery mode or multiple candidates exist)
    if plan.destinations and len(plan.destinations) > 1:
        render_html(
            """
            <div style="margin: 16px 0 12px 0;">
                <div class="spirit-hero-badge"><span>🌟</span> Evaluated Getaways</div>
                <h3 style="font-size: 1.35rem; margin-top: 4px;">Top Scored Destination Candidates</h3>
                <p style="color: #475569; font-size: 0.85rem;">
                    Scored by seasonal climate suitability, travel radius, and budget compatibility.
                </p>
            </div>
            """
        )
        
        d_cols = st.columns(min(len(plan.destinations), 3))
        for idx, dest in enumerate(plan.destinations[:3]):
            with d_cols[idx]:
                cost_str = f"₹{dest.estimated_cost_inr:,.0f}" if dest.estimated_cost_inr else "Estimate Pending"
                season_str = dest.best_season or "All-Season"
                highlights_pills = "".join(
                    [f'<span class="dest-pill">{h}</span>' for h in (dest.highlights or [])[:3]]
                )
                
                render_html(
                    f"""
                    <div class="spirit-card-sm" style="margin-bottom: 12px; height: 100%;">
                        <div style="display: flex; justify-content: space-between; align-items: baseline;">
                            <div style="font-size: 1.15rem; font-weight: 700; color: #0F172A;">{dest.name}</div>
                            <span style="font-size: 0.72rem; color: #0284C7; font-weight: 600;">{season_str}</span>
                        </div>
                        <div style="font-size: 0.82rem; color: #475569; margin: 4px 0 10px 0;">{dest.tagline or ''}</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 12px;">
                            {highlights_pills}
                        </div>
                        <div style="font-size: 0.78rem; color: #64748B; border-top: 1px solid #E2E8F0; padding-top: 8px;">
                            Est. Package: <strong style="color: #059669; font-size: 0.95rem;">{cost_str}</strong>
                        </div>
                    </div>
                    """
                )
        render_html("<div style='margin-bottom: 24px;'></div>")

    # 2. Day-by-Day Detailed Schedule
    render_html(
        """
        <div style="margin: 12px 0 16px 0;">
            <div class="spirit-hero-badge"><span>🗓️</span> Master Timeline</div>
            <h3 style="font-size: 1.35rem; margin-top: 4px;">Day-by-Day Curated Experience</h3>
            <p style="color: #475569; font-size: 0.85rem;">
                Sequenced by geographic proximity, ideal time-of-day light, and balanced activity pace.
            </p>
        </div>
        """
    )

    if not plan.itinerary:
        st.info("No detailed daily activities generated for this request.")
        return

    for day in plan.itinerary:
        date_str = f" • {day.date.strftime('%A, %d %B %Y')}" if day.date else ""
        expander_title = f"Day {day.day_number}: {day.theme_or_title}{date_str}"
        with st.expander(expander_title, expanded=True):
            if day.overnight_location:
                render_html(
                    f"""
                    <div style="font-size: 0.78rem; color: #0284C7; margin-bottom: 12px; display: inline-flex; align-items: center; gap: 6px;">
                        <span>📍</span> Base / Stay: <strong>{day.overnight_location}</strong>
                    </div>
                    """
                )


            if day.activities:
                for act in day.activities:
                    col_time, col_content, col_cost = st.columns([2, 5, 2])
                    
                    with col_time:
                        render_html(
                            f"""
                            <div class="activity-time" style="margin-top: 6px;">
                                {act.time_slot}
                            </div>
                            """
                        )

                    with col_content:
                        loc_markup = (
                            f'<span style="font-size: 0.78rem; color: #94A3B8;"> 📍 {act.location}</span>'
                            if act.location
                            else ""
                        )
                        render_html(
                            f"""
                            <div style="font-size: 0.95rem; font-weight: 600; color: #FFFFFF;">
                                {act.title}{loc_markup}
                            </div>
                            """
                        )
                        if act.description:
                            st.caption(act.description)
                        if act.booking_url:
                            st.markdown(f"[🔗 Reserve / Info Link]({act.booking_url})")

                    with col_cost:
                        if act.estimated_cost_inr > 0:
                            render_html(
                                f"""
                                <div style="font-weight: 700; color: #06D6A0; text-align: right; font-size: 0.95rem; margin-top: 6px;">
                                    ₹{act.estimated_cost_inr:,.0f}
                                </div>
                                """
                            )
                        else:
                            render_html(
                                """
                                <div style="color: #64748B; font-size: 0.8rem; text-align: right; margin-top: 6px;">
                                    Included / Free
                                </div>
                                """
                            )
                    
                    st.divider()
            else:
                st.write("Leisure & unstructured exploration time.")

            if day.day_notes:
                render_html(
                    f"""
                    <div style="
                        background: rgba(0, 240, 255, 0.05);
                        border-left: 3px solid #00F0FF;
                        padding: 10px 14px;
                        border-radius: 6px;
                        font-size: 0.82rem;
                        color: #94A3B8;
                        margin-top: 8px;
                    ">
                        💡 <strong>Daily Advisor Tip:</strong> {day.day_notes}
                    </div>
                    """
                )
