"""
frontend/components/weather_safety_view.py
==========================================
Renders real-time weather forecasts, packing recommendations, and safety advisories.
"""

from __future__ import annotations
from typing import List, Optional
import streamlit as st

from backend.schemas import WeatherForecastSummary
from frontend.components import render_html


def render_weather_section(weather: Optional[WeatherForecastSummary]) -> None:
    """Render meteorological conditions and packing checklist."""
    render_html(
        """
        <div style="margin: 12px 0 16px 0;">
            <div class="spirit-hero-badge"><span>🌤️</span> Atmospheric Intelligence</div>
            <h3 style="font-size: 1.35rem; margin-top: 4px;">Weather Forecast & Gear Advisory</h3>
            <p style="color: #475569; font-size: 0.85rem;">
                Synchronized with Open-Meteo meteorological endpoints and seasonal historical baselines.
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
        st.metric("Destination Clime", weather.location, help=f"Forecast target: {weather.location}")
    with w2:
        temp_str = f"{weather.average_temperature_c:.1f} °C" if weather.average_temperature_c is not None else "Seasonal Norm"
        st.metric("Avg Temperature", temp_str)
    with w3:
        precip_str = f"{weather.precipitation_probability:.0f} %" if weather.precipitation_probability is not None else "Minimal"
        st.metric("Precipitation Chance", precip_str)

    # Condition Callout
    if weather.conditions:
        render_html(
            f"""
            <div style="
                background: rgba(2, 132, 199, 0.06);
                border: 1px solid rgba(2, 132, 199, 0.2);
                border-radius: 12px;
                padding: 14px 18px;
                margin: 16px 0;
                display: flex;
                align-items: center;
                gap: 12px;
            ">
                <span style="font-size: 1.8rem;">🌤️</span>
                <div>
                    <div style="font-size: 0.8rem; color: #0284C7; font-weight: 700; text-transform: uppercase;">Forecast Summary</div>
                    <div style="color: #0F172A; font-size: 1rem; font-weight: 600;">{weather.conditions}</div>
                </div>
            </div>
            """
        )

    # Packing Recommendations
    if weather.packing_recommendations:
        render_html("<h4 style='font-size: 1.1rem; margin-top: 20px; margin-bottom: 10px;'>🎒 Essential Packing Checklist</h4>")
        pack_cols = st.columns(min(len(weather.packing_recommendations), 3))
        for idx, item in enumerate(weather.packing_recommendations):
            col = pack_cols[idx % 3]
            with col:
                render_html(
                    f"""
                    <div style="
                        background: #FFFFFF;
                        border: 1px solid #E2E8F0;
                        border-radius: 10px;
                        padding: 10px 14px;
                        margin-bottom: 8px;
                        display: flex;
                        align-items: center;
                        gap: 10px;
                        font-size: 0.88rem;
                        color: #0F172A;
                        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
                    ">
                        <span style="color: #059669; font-weight: 700;">✔</span> {item}
                    </div>
                    """
                )


def render_safety_section(precautions: List[str]) -> None:
    """Render localized safety advisories and emergency precautions."""
    render_html(
        """
        <div style="margin: 12px 0 16px 0;">
            <div class="spirit-hero-badge"><span>🛡️</span> Safety Intelligence</div>
            <h3 style="font-size: 1.35rem; margin-top: 4px;">Contextual Safety & Local Advisories</h3>
            <p style="color: #475569; font-size: 0.85rem;">
                Curated risk mitigation protocols, emergency numbers, and seasonal health guidelines.
            </p>
        </div>
        """
    )

    if precautions:
        for idx, item in enumerate(precautions):
            render_html(
                f"""
                <div style="
                    background: #FFFFFF;
                    border: 1px solid #E2E8F0;
                    border-left: 3px solid #D97706;
                    border-radius: 8px;
                    padding: 12px 16px;
                    margin-bottom: 10px;
                    font-size: 0.9rem;
                    color: #0F172A;
                    display: flex;
                    align-items: flex-start;
                    gap: 10px;
                    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
                ">
                    <span style="color: #D97706; font-weight: 700;">#{idx + 1}</span>
                    <span>{item}</span>
                </div>
                """
            )

    else:
        st.info("Standard travel safety precautions apply.")
