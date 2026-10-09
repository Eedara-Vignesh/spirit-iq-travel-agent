"""
frontend/components/budget_view.py
==================================
Budget breakdown dashboard with per-person calculations, category bars,
buffer protection indicators, and algorithmic audit provenance.
"""

from __future__ import annotations
from typing import Optional
import streamlit as st

from backend.schemas import BudgetBreakdown
from frontend.components import render_html


def render_budget_section(budget: Optional[BudgetBreakdown], num_travellers: int = 1) -> None:
    """Render comprehensive financial audit and spending allocation."""
    render_html(
        """
        <div style="margin: 12px 0 16px 0;">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
                <div>
                    <div class="spirit-hero-badge"><span>💰</span> Financial Architecture</div>
                    <h3 style="font-size: 1.35rem; margin-top: 4px;">Expenditure Audit & Safety Buffer</h3>
                </div>
                <div style="font-size: 0.75rem; color: #06D6A0; background: rgba(6,214,160,0.1); padding: 4px 10px; border-radius: 999px; border: 1px solid rgba(6,214,160,0.3);">
                    Method: Deterministic 4-Tier Model
                </div>
            </div>
            <p style="color: #94A3B8; font-size: 0.85rem; margin-top: 4px;">
                Every line item is audited against regional tariffs with emergency buffer protection.
            </p>
        </div>
        """
    )

    if not budget:
        st.info("Budget breakdown details are currently unavailable for this plan.")
        return

    # Top Metric Highlights
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Budget Allocated", f"₹{budget.total_budget_inr:,.0f}")
    with c2:
        st.metric("Estimated Total Cost", f"₹{budget.estimated_total_cost_inr:,.0f}")
    with c3:
        status_label = "Protected (+)" if budget.is_within_budget else "Deficit (-)"
        st.metric(
            "Emergency Buffer",
            f"₹{budget.remaining_buffer_inr:,.0f}",
            delta=status_label,
            delta_color="normal" if budget.is_within_budget else "inverse",
        )
    with c4:
        per_person = budget.estimated_total_cost_inr / max(1, num_travellers)
        st.metric("Est. Per Person", f"₹{per_person:,.0f}", help=f"Divided across {num_travellers} traveller(s)")

    # Overall Budget Consumption Bar
    spent_pct = min(100.0, (budget.estimated_total_cost_inr / max(1.0, budget.total_budget_inr)) * 100.0)
    is_warning = not budget.is_within_budget or spent_pct > 95.0
    
    render_html(
        f"""
        <div style="margin: 20px 0 10px 0;">
            <div style="display: flex; justify-content: space-between; font-size: 0.82rem;">
                <span style="color: #94A3B8;">Budget Consumption: <strong style="color: {'#FF5470' if is_warning else '#00F0FF'};">{spent_pct:.1f}%</strong></span>
                <span style="color: {'#FF5470' if not budget.is_within_budget else '#06D6A0'}; font-weight: 600;">
                    {'⚠️ Budget Exceeded' if not budget.is_within_budget else '✅ Sound Financial Reserve'}
                </span>
            </div>
            <div class="budget-progress-track">
                <div class="budget-progress-fill {'warning' if is_warning else ''}" style="width: {spent_pct:.1f}%;"></div>
            </div>
        </div>
        """
    )

    # Detailed Category Breakdown
    if budget.categories:
        render_html("<h4 style='font-size: 1.1rem; margin-top: 18px;'>Category Allocation Breakdown</h4>")
        
        table_rows = []
        for cat in budget.categories:
            cat_name = cat.category
            amount = f"₹{cat.allocated_amount_inr:,.0f}"
            share = f"{cat.percentage_of_total or 0:.1f}%"
            notes = cat.notes or "—"
            
            icon = {
                "accommodation": "🏨",
                "transport": "🚗",
                "food": "🍽️",
                "food & dining": "🍽️",
                "activities": "🎟️",
                "buffer": "🛡️",
                "emergency buffer": "🛡️",
            }.get(cat_name.lower(), "📊")

            table_rows.append(
                f"""
                <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
                    <td style="padding: 10px 14px; font-weight: 600; color: #FFFFFF;">
                        <span style="margin-right: 6px;">{icon}</span> {cat_name}
                    </td>
                    <td style="padding: 10px 14px; color: #06D6A0; font-weight: 700;">{amount}</td>
                    <td style="padding: 10px 14px; color: #00F0FF; font-weight: 600;">{share}</td>
                    <td style="padding: 10px 14px; color: #94A3B8; font-size: 0.82rem;">{notes}</td>
                </tr>
                """
            )

        render_html(
            f"""
            <div style="
                background: rgba(16, 28, 58, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 14px;
                overflow: hidden;
                margin-top: 10px;
            ">
                <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.88rem;">
                    <thead>
                        <tr style="background: rgba(255, 255, 255, 0.04); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
                            <th style="padding: 12px 14px; color: #F1F5F9; font-weight: 600;">Category</th>
                            <th style="padding: 12px 14px; color: #F1F5F9; font-weight: 600;">Amount (INR)</th>
                            <th style="padding: 12px 14px; color: #F1F5F9; font-weight: 600;">Share</th>
                            <th style="padding: 12px 14px; color: #F1F5F9; font-weight: 600;">Notes & Context</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows)}
                    </tbody>
                </table>
            </div>
            """
        )
