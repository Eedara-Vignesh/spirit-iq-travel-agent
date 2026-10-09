"""
frontend/components/header.py
==============================
Top navigation bar, SpiritIQ brand badge, and live system status indicators.
"""

from __future__ import annotations
from frontend.components import render_html


def render_header(gemini_model: str, maps_active: bool) -> None:
    """Render top brand navigation bar with engine status pills."""
    render_html(
        f"""
        <div style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 14px 24px;
            background: rgba(11, 19, 43, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        ">
            <!-- Brand Logo & Title -->
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="
                    width: 42px;
                    height: 42px;
                    border-radius: 12px;
                    background: linear-gradient(135deg, #00C2CB 0%, #008B94 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.3rem;
                    box-shadow: 0 0 15px rgba(0, 240, 255, 0.35);
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
                            color: #FFFFFF;
                        ">Spirit<span style="color: #00F0FF;">IQ</span></span>
                        <span style="
                            font-size: 0.68rem;
                            font-weight: 700;
                            letter-spacing: 0.08em;
                            text-transform: uppercase;
                            padding: 2px 8px;
                            background: rgba(0, 240, 255, 0.12);
                            border: 1px solid rgba(0, 240, 255, 0.3);
                            border-radius: 999px;
                            color: #00F0FF;
                        ">v2.0 Pro</span>
                    </div>
                    <div style="font-size: 0.75rem; color: #94A3B8;">Intelligent Travel Planning & Routing System</div>
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
                    background: rgba(6, 214, 160, 0.1);
                    border: 1px solid rgba(6, 214, 160, 0.3);
                    color: #06D6A0;
                ">
                    <span style="width: 7px; height: 7px; border-radius: 50%; background: #06D6A0; box-shadow: 0 0 8px #06D6A0;"></span>
                    Gemini AI: {gemini_model}
                </div>
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    font-size: 0.76rem;
                    font-weight: 600;
                    padding: 5px 12px;
                    border-radius: 999px;
                    background: rgba(0, 240, 255, 0.08);
                    border: 1px solid rgba(0, 240, 255, 0.25);
                    color: #00F0FF;
                ">
                    <span style="width: 7px; height: 7px; border-radius: 50%; background: #00F0FF; box-shadow: 0 0 8px #00F0FF;"></span>
                    {'Google Maps API' if maps_active else 'Dijkstra Engine Active'}
                </div>
            </div>
        </div>
        """
    )
