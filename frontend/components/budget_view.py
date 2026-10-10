"""
frontend/components/budget_view.py
==================================
Budget breakdown dashboard with per-person calculations, category bars,
and buffer protection indicators.
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
            <div class="spirit-hero-badge"><span>💰</span> Financial Architecture</div>
            <h3 style="font-size: 1.35rem; margin-top: 4px;">Expenditure Audit & Safety Buffer</h3>
            <p style="color: #94A3B8; font-size: 0.85rem;">
                Every line item is validated against regional market tariffs with emergency deficit protections.
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
                <span style="color: #475569;">Budget Consumption: <strong style="color: {'#E11D48' if is_warning else '#0284C7'};">{spent_pct:.1f}%</strong></span>
                <span style="color: {'#E11D48' if not budget.is_within_budget else '#059669'}; font-weight: 600;">
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
                <tr style="border-bottom: 1px solid #E2E8F0;">
                    <td style="padding: 10px 14px; font-weight: 600; color: #0F172A;">
                        <span style="margin-right: 6px;">{icon}</span> {cat_name}
                    </td>
                    <td style="padding: 10px 14px; color: #059669; font-weight: 700;">{amount}</td>
                    <td style="padding: 10px 14px; color: #0284C7; font-weight: 600;">{share}</td>
                    <td style="padding: 10px 14px; color: #475569; font-size: 0.85rem;">{notes}</td>
                </tr>
                """
            )

        render_html(
            f"""
            <div style="
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 14px;
                overflow: hidden;
                margin-top: 10px;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
            ">
                <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.88rem;">
                    <thead>
                        <tr style="background: #F8FAFC; border-bottom: 1px solid #E2E8F0;">
                            <th style="padding: 12px 14px; color: #0F172A; font-weight: 700;">Category</th>
                            <th style="padding: 12px 14px; color: #0F172A; font-weight: 700;">Amount (INR)</th>
                            <th style="padding: 12px 14px; color: #0F172A; font-weight: 700;">Share</th>
                            <th style="padding: 12px 14px; color: #0F172A; font-weight: 700;">Notes & Context</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows)}
                    </tbody>
                </table>
            </div>
            """
        )

