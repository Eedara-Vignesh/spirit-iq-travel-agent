"""
frontend/components/transit_view.py
===================================
Renders multimodal transit comparison and Dijkstra corridor route solutions.
"""

from __future__ import annotations
from typing import List, Optional
import streamlit as st

from backend.schemas import TransportOption, AlternateRoute
from frontend.components import render_html


def render_transit_section(
    transport_options: List[TransportOption],
    alternate_routes: List[AlternateRoute],
) -> None:
    """Render transit mode comparisons and Dijkstra corridor graphs."""
    render_html(
        """
        <div style="margin: 12px 0 16px 0;">
            <div class="spirit-hero-badge"><span>🚗</span> Mobility & Navigation</div>
            <h3 style="font-size: 1.35rem; margin-top: 4px;">Transit Comparison & Dijkstra Corridors</h3>
            <p style="color: #475569; font-size: 0.85rem;">
                Multi-modal door-to-door options benchmarked alongside shortest-path highway graph algorithms.
            </p>
        </div>
        """
    )

    # 1. Multi-modal Transport Comparison Cards
    if transport_options:
        render_html("<h4 style='font-size: 1.1rem; margin-bottom: 12px;'>Modal Benchmark Matrix</h4>")
        
        t_cols = st.columns(min(len(transport_options), 4))
        for idx, opt in enumerate(transport_options):
            col = t_cols[idx % min(len(transport_options), 4)]
            with col:
                mode_icon = {
                    "flight": "✈️",
                    "train": "🚆",
                    "bus": "🚌",
                    "cab": "🚕",
                    "self_drive": "🚗",
                }.get(opt.mode.value, "🌐")

                dur_str = f"{opt.duration_hours:.1f} hrs" if opt.duration_hours else "Transit"
                cost_str = f"₹{opt.estimated_cost_inr:,.0f}" if opt.estimated_cost_inr > 0 else "Estimate"
                rec_badge = (
                    '<div style="font-size: 0.7rem; font-weight: 700; color: #0284C7; background: rgba(2, 132, 199, 0.08); border: 1px solid rgba(2, 132, 199, 0.25); padding: 2px 8px; border-radius: 999px; margin-bottom: 8px; display: inline-block;">⭐ RECOMMENDED</div>'
                    if opt.is_recommended
                    else ""
                )

                render_html(
                    f"""
                    <div class="spirit-card-sm" style="margin-bottom: 12px; height: 100%;">
                        {rec_badge}
                        <div style="font-size: 1.6rem; margin-bottom: 6px;">{mode_icon}</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #0F172A;">{opt.mode.value.capitalize()}</div>
                        <div style="font-size: 0.82rem; color: #0284C7; font-weight: 600; margin: 4px 0 10px 0;">{dur_str}</div>
                        <div style="font-size: 0.78rem; color: #475569; margin-bottom: 10px;">
                            {opt.departure_point} ➔ {opt.arrival_point}<br>
                            <span style="color: #64748B;">({opt.provider_or_route or 'Standard Route'})</span>
                        </div>
                        <div style="font-size: 1.1rem; font-weight: 800; color: #059669; border-top: 1px solid #E2E8F0; padding-top: 8px;">
                            {cost_str}
                        </div>
                    </div>
                    """
                )
                if opt.booking_url:
                    st.link_button(f"Search {opt.mode.value.capitalize()} Booking", opt.booking_url, use_container_width=True)

    render_html("<div style='margin-bottom: 24px;'></div>")

    # 2. Dijkstra Highway Corridors
    render_html("<h4 style='font-size: 1.1rem; margin-bottom: 8px;'>🛣️ Dijkstra Shortest-Path Highway Corridor</h4>")
    if alternate_routes:
        for r in alternate_routes:
            dist_str = f"{r.total_distance_km:.0f} km" if r.total_distance_km else "Calculated corridor"
            drive_str = f"~{r.estimated_duration_hours:.1f} hours drive" if r.estimated_duration_hours else ""
            waypoints_str = ", ".join(r.via_waypoints) if r.via_waypoints else "Direct arterial highway"

            render_html(
                f"""
                <div class="spirit-card" style="margin-bottom: 14px;">
                    <div style="display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap;">
                        <h4 style="color: #0F172A; font-size: 1.15rem; margin: 0;">{r.route_name}</h4>
                        <span style="font-size: 0.82rem; color: #0284C7; font-weight: 600;">{dist_str} {('• ' + drive_str) if drive_str else ''}</span>
                    </div>
                    <div style="margin: 8px 0; font-size: 0.85rem; color: #475569;">
                        <strong>Key Corridor Waypoints:</strong> <span style="color: #0F172A;">{waypoints_str}</span>
                    </div>
                    <div style="
                        background: #F8FAFC;
                        border-left: 3px solid #0284C7;
                        border: 1px solid #E2E8F0;
                        padding: 8px 12px;
                        border-radius: 6px;
                        font-size: 0.78rem;
                        color: #475569;
                        margin-top: 10px;
                    ">
                        ⚡ <strong>Graph Solver:</strong> {r.algorithm_notes or 'Calculated via weighted Dijkstra adjacency graph.'}
                    </div>
                </div>
                """
            )

    else:
        st.info("Direct corridor transit selected.")
