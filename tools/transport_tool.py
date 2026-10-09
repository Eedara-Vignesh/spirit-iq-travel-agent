
def compare_transport_options(options, budget_limit=None):
    """
    Compare supplied transport estimates.

    Each option should contain:
    {
        "mode": "bus",
        "estimated_cost": 500,
        "duration_minutes": 180,
        "source": "sample"
    }

    These values must come from your data source or be labelled
    as estimates. This function does not search live availability.
    """
    valid_options = []

    for option in options:
        cost = option.get("estimated_cost")
        duration = option.get("duration_minutes")

        if cost is None or duration is None:
            continue

        if cost < 0 or duration < 0:
            continue

        if not option.get("mode"):
            continue

        valid_options.append(option.copy())

    if not valid_options:
        return {
            "status": "error",
            "message": "No valid transport options were supplied.",
            "options": [],
        }

    valid_options.sort(
        key=lambda item: (
            item["estimated_cost"],
            item["duration_minutes"]
        )
    )

    cheapest = valid_options[0]
    fastest = min(
        valid_options,
        key=lambda item: item["duration_minutes"]
    )

    within_budget = None
    if budget_limit is not None:
        within_budget = [
            option for option in valid_options
            if option["estimated_cost"] <= budget_limit
        ]

    return {
        "status": "success",
        "options": valid_options,
        "cheapest_option": cheapest,
        "fastest_option": fastest,
        "within_budget": within_budget,
        "data_is_live": all(
            option.get("is_live_data", False)
            for option in valid_options
        ),
    }


if __name__ == "__main__":
    sample_options = [
        {
            "mode": "bus",
            "estimated_cost": 400,
            "duration_minutes": 180,
            "source": "sample",
            "is_live_data": False,
        },
        {
            "mode": "train",
            "estimated_cost": 250,
            "duration_minutes": 150,
            "source": "sample",
            "is_live_data": False,
        },
        {
            "mode": "car",
            "estimated_cost": 1200,
            "duration_minutes": 120,
            "source": "sample",
            "is_live_data": False,
        },
    ]

    print(compare_transport_options(sample_options, budget_limit=500))
