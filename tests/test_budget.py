"""
tests/test_budget.py
====================
Unit tests for budget breakdown, per-person calculations, and deficit auditing.
"""

from backend.schemas import TravelPace
from backend.tools.budget_tool import calculate_budget_breakdown


def test_calculate_budget_breakdown_success():
    """Verify healthy budget breakdown with per-person metrics."""
    res = calculate_budget_breakdown(
        total_budget_inr=50000.0,
        num_days=5,
        num_travellers=2,
        pace=TravelPace.BALANCED,
    )

    assert res.success is True
    assert res.data is not None
    data = res.data
    assert data["total_budget_inr"] == 50000.0
    assert data["is_within_budget"] is True
    assert len(data["categories"]) == 5
    assert data["per_person_total_inr"] == 25000.0
    assert data["daily_per_person_inr"] == 5000.0

    # Total allocated must equal total budget
    total_allocated = sum(c["allocated_amount_inr"] for c in data["categories"])
    assert round(total_allocated, 2) == 50000.0


def test_calculate_budget_breakdown_deficit_warning():
    """Verify that an unrealistically low budget triggers a deficit warning and savings suggestions."""
    # ₹3,000 for 4 travellers over 5 days is severely constrained
    res = calculate_budget_breakdown(
        total_budget_inr=3000.0,
        num_days=5,
        num_travellers=4,
        pace=TravelPace.BALANCED,
    )

    assert res.success is True
    data = res.data
    assert data["is_within_budget"] is False
    assert data["deficit_warning"] is not None
    assert "Deficit" in data["deficit_warning"]
    assert len(data["cost_saving_suggestions"]) >= 2


def test_calculate_budget_breakdown_invalid_inputs():
    res_zero = calculate_budget_breakdown(total_budget_inr=0.0, num_days=3)
    assert res_zero.success is False
    assert "positive" in res_zero.error.lower()

    res_neg_days = calculate_budget_breakdown(total_budget_inr=20000.0, num_days=0)
    assert res_neg_days.success is False
    assert "at least 1" in res_neg_days.error.lower()
