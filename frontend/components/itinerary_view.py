"""
frontend/components/itinerary_view.py
=====================================
Renders destination matching rationale, candidate comparisons,
and day-wise activity schedule with time windows and costs.
"""

from __future__ import annotations
from typing import List, Optional
import streamlit as st

from backend.schemas import TripPlan, DayPlan, DestinationRecommendation
from frontend.components import render_html


def render_itinerary_section(plan: TripPlan) -> None:
    """Render destination selection rationale and day-wise schedule."""
    
    # 1. Primary Destination Rationale Card
    if plan.destinations:
        primary_dest = plan.destinations[0]
        highlights_str = ", ".join(primary_dest.highlights[:4]) if primary_dest.highlights else "Top regional attractions"
        render_html(
            f"""
            <div style="
                background: linear-gradient(135deg, rgba(16, 28, 58, 0.7) 0%, rgba(20, 39, 70, 0.7) 100%);
                border: 1px solid rgba(0, 240, 255, 0.25);
                border-radius: 14px;
                padding: 16px 20px;
                margin-bottom: 20px;
            ">
                <div style="display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap;">
                    <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF;">
                        📍 Target Destination: <span style="color: #00F0FF;">{primary_dest.name}</span>
                    </div>
                    <span style="font-size: 0.75rem; color: #06D6A0; font-weight: 600;">
                        Best Season: {primary_dest.best_season or 'Pleasant Period'}
                    </span>
                </div>
                <div style="font-size: 0.85rem; color: #94A3B8; margin: 6px 0 10px 0;">
                    {primary_dest.tagline or 'Curated getaway aligned with your requested budget and travel month.'}
                </div>
                <div style="font-size: 0.8rem; color: #F1F5F9;">
                    <strong>Why it matches:</strong> Key highlights include <em>{highlights_str}</em>. Evaluated across climatic conditions and travel radius.
                </div>
            </div>
            """
        )

    # 2. Candidate comparison cards if discovery mode was active
    if plan.destinations and len(plan.destinations) > 1:
        render_html(
            """
            <div style="margin: 16px 0 10px 0;">
                <div class="spirit-hero-badge"><span>🌟</span> Discovered Candidates</div>
                <h4 style="font-size: 1.1rem; margin-top: 4px;">Top Scored Destination Options</h4>
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
                            <div style="font-size: 1.05rem; font-weight: 700; color: #FFFFFF;">{dest.name}</div>
                            <span style="font-size: 0.72rem; color: #00F0FF; font-weight: 600;">{season_str}</span>
                        </div>
                        <div style="font-size: 0.8rem; color: #94A3B8; margin: 4px 0 8px 0;">{dest.tagline or ''}</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 10px;">
                            {highlights_pills}
                        </div>
                        <div style="font-size: 0.76rem; color: #64748B; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
                            Est. Package: <strong style="color: #06D6A0; font-size: 0.9rem;">{cost_str}</strong>
                        </div>
                    </div>
                    """
                )
        render_html("<div style='margin-bottom: 18px;'></div>")

    # 3. Day-by-Day Master Schedule
    render_html(
        """
        <div style="margin: 12px 0 16px 0;">
            <div class="spirit-hero-badge"><span>🗓️</span> Day-Wise Schedule</div>
            <h3 style="font-size: 1.35rem; margin-top: 4px;">Day-by-Day Activity Timeline</h3>
            <p style="color: #94A3B8; font-size: 0.85rem;">
                Sequenced by proximity, optimum time windows, and balanced travel pace.
            </p>
        </div>
        """
    )

    if not plan.itinerary:
        st.info("No detailed daily activities generated for this plan.")
        return

    for day in plan.itinerary:
        date_str = f" • {day.date.strftime('%A, %d %B %Y')}" if day.date else ""
        expander_title = f"Day {day.day_number}: {day.theme_or_title}{date_str}"
        with st.expander(expander_title, expanded=True):
            if day.overnight_location:
                render_html(
                    f"""
                    <div style="font-size: 0.78rem; color: #00F0FF; margin-bottom: 12px; display: inline-flex; align-items: center; gap: 6px;">
                        <span>📍</span> Stay Location: <strong>{day.overnight_location}</strong>
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
                        💡 <strong>Daily Tip:</strong> {day.day_notes}
                    </div>
                    """
                )
