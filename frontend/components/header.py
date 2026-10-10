"""
frontend/components/header.py
==============================
Top navigation bar, SpiritIQ brand badge, and live system status indicators.
"""

from __future__ import annotations
from typing import Optional
from frontend.components import render_html


def render_header(model_name: Optional[str] = None, maps_active: bool = False, **kwargs) -> None:
    """Render top brand navigation bar with engine status pills."""
    resolved_model = model_name or kwargs.get("groq_model") or kwargs.get("gemini_model") or "llama-3.3-70b-versatile"

    render_html(
        f"""
        <div style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 14px 24px;
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 16px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        ">
            <!-- Brand Logo & Title -->
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="
                    width: 42px;
                    height: 42px;
                    border-radius: 12px;
                    background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.3rem;
                    box-shadow: 0 2px 6px rgba(2, 132, 199, 0.25);
                ">
                    ✈️
                </div>
                <div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="
                            font-family: 'Outfit', sans-serif;
                            font-size: 1.35rem;
                            font-weight: 800;
                            letter-spacing: -0.02em;
                            color: #0F172A;
                        ">Spirit<span style="color: #0284C7;">IQ</span></span>
                        <span style="
                            font-size: 0.68rem;
                            font-weight: 700;
                            letter-spacing: 0.08em;
                            text-transform: uppercase;
                            padding: 2px 8px;
                            background: rgba(2, 132, 199, 0.08);
                            border: 1px solid rgba(2, 132, 199, 0.25);
                            border-radius: 999px;
                            color: #0284C7;
                        ">v2.0 Pro</span>
                    </div>
                    <div style="font-size: 0.75rem; color: #64748B;">Intelligent Travel Planning & Routing System</div>
                </div>
            </div>

            <!-- System Status Badges -->
            <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    font-size: 0.76rem;
                    font-weight: 600;
                    padding: 5px 12px;
                    border-radius: 999px;
                    background: rgba(5, 150, 105, 0.08);
                    border: 1px solid rgba(5, 150, 105, 0.25);
                    color: #059669;
                ">
                    <span style="width: 7px; height: 7px; border-radius: 50%; background: #059669;"></span>
                    Groq AI: {resolved_model}
                </div>
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    font-size: 0.76rem;
                    font-weight: 600;
                    padding: 5px 12px;
                    border-radius: 999px;
                    background: rgba(2, 132, 199, 0.08);
                    border: 1px solid rgba(2, 132, 199, 0.25);
                    color: #0284C7;
                ">
                    <span style="width: 7px; height: 7px; border-radius: 50%; background: #0284C7;"></span>
                    {'Google Maps API (Optional)' if maps_active else 'OpenStreetMap + OSRM'}
                </div>
            </div>
        </div>

        """
    )
