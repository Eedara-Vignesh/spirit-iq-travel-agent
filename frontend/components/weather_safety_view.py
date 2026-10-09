"""
frontend/components/weather_safety_view.py
==========================================
Renders real-time weather forecasts with date ranges, source provenance,
packing checklists, and localized safety advisories.
"""

from __future__ import annotations
from typing import List, Optional
import streamlit as st

from backend.schemas import WeatherForecastSummary
from frontend.components import render_html


def render_weather_section(weather: Optional[WeatherForecastSummary]) -> None:
    """Render meteorological conditions, forecast period labels, and packing checklist."""
    render_html(
        """
        <div style="margin: 12px 0 16px 0;">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
                <div>
                    <div class="spirit-hero-badge"><span>🌤️</span> Atmospheric Intelligence</div>
                    <h3 style="font-size: 1.35rem; margin-top: 4px;">Weather Forecast & Gear Advisory</h3>
                </div>
                <div style="font-size: 0.75rem; color: #00F0FF; background: rgba(0,240,255,0.08); padding: 4px 10px; border-radius: 999px; border: 1px solid rgba(0,240,255,0.2);">
                    Source: Open-Meteo Endpoints
                </div>
            </div>
            <p style="color: #94A3B8; font-size: 0.85rem; margin-top: 4px;">
                Retrieved based on geographic coordinates for the requested travel period.
            </p>
        </div>
        """
    )

    if not weather:
        st.info("Weather forecast details are currently unavailable for this destination.")
        return

    # Weather metric highlights
    w1, w2, w3 = st.columns(3)
    with w1:
        st.metric("Destination", weather.location)
    with w2:
        temp_str = f"{weather.average_temperature_c:.1f} °C" if weather.average_temperature_c is not None else "Seasonal Baseline"
        st.metric("Avg Temperature", temp_str)
    with w3:
        precip_str = f"{weather.precipitation_probability:.0f} %" if weather.precipitation_probability is not None else "Minimal"
        st.metric("Precipitation Chance", precip_str)

    # Condition Callout
    if weather.conditions:
        render_html(
            f"""
            <div style="
                background: rgba(0, 240, 255, 0.06);
                border: 1px solid rgba(0, 240, 255, 0.2);
                border-radius: 12px;
                padding: 14px 18px;
                margin: 16px 0;
                display: flex;
                align-items: center;
                gap: 12px;
            ">
                <span style="font-size: 1.8rem;">🌤️</span>
                <div>
                    <div style="font-size: 0.78rem; color: #00F0FF; font-weight: 700; text-transform: uppercase;">Forecast Summary</div>
                    <div style="color: #FFFFFF; font-size: 0.98rem; font-weight: 600;">{weather.conditions}</div>
                </div>
            </div>
            """
        )

    # Advisories if any
    if weather.advisories:
        for adv in weather.advisories:
            render_html(
                f"""
                <div style="background: rgba(255, 183, 3, 0.1); border-left: 3px solid #FFB703; padding: 8px 12px; border-radius: 6px; font-size: 0.8rem; color: #F1F5F9; margin-bottom: 8px;">
                    ⚠️ <strong>Weather Advisory:</strong> {adv}
                </div>
                """
            )

    # Packing Recommendations
    if weather.packing_recommendations:
        render_html("<h4 style='font-size: 1.1rem; margin-top: 18px; margin-bottom: 10px;'>🎒 Essential Packing Checklist</h4>")
        pack_cols = st.columns(min(len(weather.packing_recommendations), 3))
        for idx, item in enumerate(weather.packing_recommendations):
            col = pack_cols[idx % 3]
            with col:
                render_html(
                    f"""
                    <div style="
                        background: rgba(255, 255, 255, 0.04);
                        border: 1px solid rgba(255, 255, 255, 0.08);
                        border-radius: 10px;
                        padding: 10px 14px;
                        margin-bottom: 8px;
                        display: flex;
                        align-items: center;
                        gap: 10px;
                        font-size: 0.88rem;
                        color: #F1F5F9;
                    ">
                        <span style="color: #06D6A0;">✔</span> {item}
                    </div>
                    """
                )


def render_safety_section(precautions: List[str]) -> None:
    """Render localized safety advisories and emergency precautions."""
    render_html(
        """
        <div style="margin: 12px 0 16px 0;">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
                <div>
                    <div class="spirit-hero-badge"><span>🛡️</span> Safety Intelligence</div>
                    <h3 style="font-size: 1.35rem; margin-top: 4px;">Contextual Safety & Local Advisories</h3>
                </div>
                <div style="font-size: 0.75rem; color: #FFB703; background: rgba(255,183,3,0.1); padding: 4px 10px; border-radius: 999px; border: 1px solid rgba(255,183,3,0.3);">
                    Verified Risk Guidelines
                </div>
            </div>
            <p style="color: #94A3B8; font-size: 0.85rem; margin-top: 4px;">
                Curated risk mitigation protocols and seasonal advisory checkpoints.
            </p>
        </div>
        """
    )

    if precautions:
        for idx, item in enumerate(precautions):
            render_html(
                f"""
                <div style="
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.07);
                    border-left: 3px solid #FFB703;
                    border-radius: 8px;
                    padding: 12px 16px;
                    margin-bottom: 10px;
                    font-size: 0.9rem;
                    color: #F1F5F9;
                    display: flex;
                    align-items: flex-start;
                    gap: 10px;
                ">
                    <span style="color: #FFB703; font-weight: 700;">#{idx + 1}</span>
                    <span>{item}</span>
                </div>
                """
            )
    else:
        st.info("Standard travel safety precautions apply.")
