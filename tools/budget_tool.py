
def calculate_budget(
    travellers,
    transport_total,
    accommodation_total,
    food_per_person_per_day,
    local_transport_total,
    activities_total,
    days
):
    """Calculate estimated trip cost for the whole group."""

    if travellers < 1:
        raise ValueError("Travellers must be at least 1.")

    if days < 1:
        raise ValueError("Days must be at least 1.")

    costs = {
        "transport": transport_total,
        "accommodation": accommodation_total,
        "food": food_per_person_per_day * travellers * days,
        "local_transport": local_transport_total,
        "activities": activities_total,
    }

    if any(cost < 0 for cost in costs.values()):
        raise ValueError("Costs cannot be negative.")

    total = sum(costs.values())

    return {
        "status": "success",
        "currency": "INR",
        "travellers": travellers,
        "days": days,
        "cost_breakdown": costs,
        "total_estimated_cost": total,
        "estimated_cost_per_person": round(total / travellers, 2),
    }


if __name__ == "__main__":
    result = calculate_budget(
        travellers=4,
        transport_total=4000,
        accommodation_total=6000,
        food_per_person_per_day=500,
        local_transport_total=1500,
        activities_total=2000,
        days=2
    )

    print(result)
