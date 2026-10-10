"""
frontend/components/footer.py
=============================
Modern, concise SaaS product footer for SpiritIQ.
"""

from __future__ import annotations
from frontend.components import render_html


def render_footer() -> None:
    """Render footer with system info, credits, and architecture tags."""
    render_html(
        """
        <div style="
            margin-top: 60px;
            padding: 32px 24px;
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 20px 20px 0 0;
            box-shadow: 0 -4px 16px rgba(15, 23, 42, 0.04);
            display: flex;
            flex-direction: column;
            gap: 16px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.5rem;">✈️</span>
                    <div>
                        <span style="font-family: 'Outfit', sans-serif; font-size: 1.15rem; font-weight: 800; color: #0F172A;">
                            Spirit<span style="color: #0284C7;">IQ</span>
                        </span>
                        <div style="font-size: 0.75rem; color: #64748B;">Intelligent Travel Planning & Autonomous Routing Agent</div>
                    </div>
                </div>

                <div style="display: flex; gap: 12px; flex-wrap: wrap; font-size: 0.78rem; color: #475569;">
                    <span class="dest-pill">⚡ Groq LLaMA-3.3</span>
                    <span class="dest-pill">🛣️ Dijkstra Highway Solver</span>
                    <span class="dest-pill">🌤️ Open-Meteo Integration</span>
                    <span class="dest-pill">🛡️ Dynamic Budget Safeguards</span>
                </div>
            </div>

            <div style="
                border-top: 1px solid #E2E8F0;
                padding-top: 14px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                font-size: 0.74rem;
                color: #64748B;
            ">
                <div>
                    Designed & Engineered for Autonomous Travel Optimization. All rights reserved.
                </div>
                <div>
                    SpiritIQ Travel Platform v2.0 • Streamlit Pro Architecture
                </div>
            </div>
        </div>
        """
    )
