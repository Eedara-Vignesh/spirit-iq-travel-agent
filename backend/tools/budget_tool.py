"""
backend/tools/budget_tool.py
============================
Budget optimization and expenditure breakdown tool.
Assigned to: Member 3 (Routing, Dijkstra, Transport and Budget)

Splits total budget into realistic allocations, calculates per-person costs,
evaluates budget feasibility, and provides concrete lower-cost alternatives if deficit is found.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from backend.schemas import BudgetBreakdown, BudgetItemBreakdown, ToolResult, TravelPace


def calculate_budget_breakdown(
    total_budget_inr: float,
    num_days: int,
    num_travellers: int = 1,
    pace: TravelPace = TravelPace.BALANCED,
) -> ToolResult:
    """
    Calculate categorized expenditure breakdown, per-person costs, and feasibility audit.
    """
    if total_budget_inr <= 0:
        return ToolResult.fail("Total budget must be strictly positive")
    if num_days <= 0:
        return ToolResult.fail("Number of days must be at least 1")
    if num_travellers <= 0:
        return ToolResult.fail("Number of travellers must be at least 1")

    # Minimum benchmark daily expenditure per person in India: ~₹1,200 (budget) to ~₹2,500 (balanced)
    pace_daily_benchmark = {
        TravelPace.RELAXED: 2200.0,
        TravelPace.BALANCED: 2800.0,
        TravelPace.PACKED: 3500.0,
    }
    recommended_min_budget = pace_daily_benchmark.get(pace, 2800.0) * num_days * num_travellers

    # Distribution based on pace
    if pace == TravelPace.PACKED:
        categories_ratio = {
            "Accommodation & Stay": 0.30,
            "Food & Dining": 0.22,
            "Intercity & Local Transport": 0.25,
            "Activities & Sightseeing": 0.15,
            "Emergency Buffer": 0.08,
        }
    elif pace == TravelPace.RELAXED:
        categories_ratio = {
            "Accommodation & Stay": 0.40,
            "Food & Dining": 0.25,
            "Intercity & Local Transport": 0.15,
            "Activities & Sightseeing": 0.10,
            "Emergency Buffer": 0.10,
        }
    else:  # BALANCED
        categories_ratio = {
            "Accommodation & Stay": 0.35,
            "Food & Dining": 0.25,
            "Intercity & Local Transport": 0.20,
            "Activities & Sightseeing": 0.10,
            "Emergency Buffer": 0.10,
        }

    is_within_budget = total_budget_inr >= (recommended_min_budget * 0.70)
    deficit_warning: Optional[str] = None
    cost_saving_suggestions: List[str] = []

    if not is_within_budget:
        deficit = round(recommended_min_budget - total_budget_inr, 2)
        deficit_warning = (
            f"Budget Alert: ₹{total_budget_inr:,.0f} is constrained for {num_travellers} traveller(s) "
            f"over {num_days} days (recommended baseline: ~₹{recommended_min_budget:,.0f}). Deficit: ~₹{deficit:,.0f}."
        )
        cost_saving_suggestions = [
            "Opt for overnight sleeper train or state express bus rather than flights or private cabs.",
            "Choose verified boutique homestays, guesthouses, or hostels over full-service resorts.",
            "Focus on free or low-entry heritage sites and nature trails over commercial paid adventure parks.",
            f"Consider shortening trip duration to {max(1, num_days - 1)} days to maintain comfort within ₹{total_budget_inr:,.0f}.",
        ]

    breakdown_items: List[BudgetItemBreakdown] = []
    for cat, ratio in categories_ratio.items():
        allocated = round(total_budget_inr * ratio, 2)
        per_person = round(allocated / num_travellers, 2)
        breakdown_items.append(
            BudgetItemBreakdown(
                category=cat,
                allocated_amount_inr=allocated,
                percentage_of_total=round(ratio * 100, 1),
                notes=f"~₹{per_person:,.0f}/person across {num_days} day(s)",
            )
        )

    planned_spend = round(total_budget_inr * (1.0 - categories_ratio["Emergency Buffer"]), 2)
    buffer_amt = round(total_budget_inr * categories_ratio["Emergency Buffer"], 2)

    per_person_total = round(total_budget_inr / num_travellers, 2)
    daily_per_person = round(per_person_total / num_days, 2)

    budget_breakdown = BudgetBreakdown(
        total_budget_inr=total_budget_inr,
        estimated_total_cost_inr=planned_spend,
        remaining_buffer_inr=buffer_amt,
        is_within_budget=is_within_budget,
        categories=breakdown_items,
    )

    data = budget_breakdown.model_dump()
    data["per_person_total_inr"] = per_person_total
    data["daily_per_person_inr"] = daily_per_person
    data["deficit_warning"] = deficit_warning
    data["cost_saving_suggestions"] = cost_saving_suggestions

    return ToolResult.ok(
        data=data,
        metadata={
            "tool": "budget_tool",
            "num_travellers": num_travellers,
            "num_days": num_days,
            "is_feasible": is_within_budget,
            "disclaimer": "All figures are calibrated benchmark estimates in INR. Hotel tariffs and transit costs fluctuate based on seasonality and advance booking.",
        },
    )
