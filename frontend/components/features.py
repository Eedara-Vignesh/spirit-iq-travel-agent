"""
frontend/components/features.py
===============================
How SpiritIQ Works workflow breakdown & core technology capability cards.
"""

from __future__ import annotations
from frontend.components import render_html


def render_how_it_works() -> None:
    """Render the 4-step workflow explaining the intelligent planning pipeline."""
    render_html(
        """
        <div style="margin: 36px 0 20px 0;">
            <div class="spirit-hero-badge">
                <span>⚡</span> The Intelligence Pipeline
            </div>
            <h2 style="font-size: 1.85rem; margin-bottom: 6px;">How SpiritIQ Architects Your Journey</h2>
            <p style="color: #94A3B8; font-size: 0.95rem;">
                Four coordinated algorithmic modules working synchronously to deliver a personalized, resilient itinerary.
            </p>

            <div class="step-grid">
                <div class="step-card">
                    <div class="step-num">01</div>
                    <div class="step-title">Discover & Score</div>
                    <div class="step-desc">
                        Matches your interests, budget, and travel month against seasonal weather and regional tourism curves.
                    </div>
                </div>

                <div class="step-card">
                    <div class="step-num">02</div>
                    <div class="step-title">Forecast & Safety</div>
                    <div class="step-desc">
                        Pulls live meteorological forecasts from Open-Meteo, calculates rain probability, and flags regional advisories.
                    </div>
                </div>

                <div class="step-card">
                    <div class="step-num">03</div>
                    <div class="step-title">Dijkstra Routing</div>
                    <div class="step-desc">
                        Computes shortest-path highway corridor graphs, waypoints, drive times, and compares flight vs train economics.
                    </div>
                </div>

                <div class="step-card">
                    <div class="step-num">04</div>
                    <div class="step-title">Budget Audit</div>
                    <div class="step-desc">
                        Applies dynamic multi-tier cost modeling with dedicated buffer safeguards to ensure financial peace of mind.
                    </div>
                </div>
            </div>
        </div>
        """
    )


def render_feature_cards() -> None:
    """Render 4 flagship capability cards with glassmorphism and icons."""
    render_html(
        """
        <div style="margin: 24px 0 32px 0;">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 18px;">
                <div class="spirit-card">
                    <div class="spirit-icon-box">🧠</div>
                    <h3 style="font-size: 1.15rem; margin-bottom: 8px;">Groq AI Orchestration</h3>
                    <p style="font-size: 0.85rem; color: #94A3B8; line-height: 1.5;">
                        High-speed LLM synthesis generates morning-to-night schedules tailored to your chosen pace and party dynamics.
                    </p>
                </div>

                <div class="spirit-card">
                    <div class="spirit-icon-box">🌤️</div>
                    <h3 style="font-size: 1.15rem; margin-bottom: 8px;">Weather-Aware Scheduling</h3>
                    <p style="font-size: 0.85rem; color: #94A3B8; line-height: 1.5;">
                        Activities are dynamically scheduled around temperature highs and rain forecasts, pairing with tailored packing kits.
                    </p>
                </div>

                <div class="spirit-card">
                    <div class="spirit-icon-box">🛣️</div>
                    <h3 style="font-size: 1.15rem; margin-bottom: 8px;">Dijkstra Highway Routing</h3>
                    <p style="font-size: 0.85rem; color: #94A3B8; line-height: 1.5;">
                        Algorithmic corridor pathfinding plots major Indian expressways, scenic stops, and benchmarked drive durations.
                    </p>
                </div>

                <div class="spirit-card">
                    <div class="spirit-icon-box">💰</div>
                    <h3 style="font-size: 1.15rem; margin-bottom: 8px;">Audited Budget Protection</h3>
                    <p style="font-size: 0.85rem; color: #94A3B8; line-height: 1.5;">
                        Per-person and category breakdowns with automated 10-15% emergency buffer safeguards to avoid overspending.
                    </p>
                </div>
            </div>
        </div>
        """
    )
