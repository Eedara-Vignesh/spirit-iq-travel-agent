
from tools.dijkstra import dijkstra


def find_best_route(graph, origin, destination, weight_unit="km"):
    """
    Find the lowest-weight route in a supplied network.

    This does not fetch real-world roads or live traffic.
    The graph must be supplied by the caller.
    """
    result = dijkstra(graph, origin, destination)

    if result["status"] != "success":
        return result

    return {
        "status": "success",
        "origin": origin,
        "destination": destination,
        "route": result["path"],
        "total_weight": result["total_weight"],
        "weight_unit": weight_unit,
        "source": "provided_graph",
        "is_live_data": False,
    }


if __name__ == "__main__":
    sample_graph = {
        "Vijayawada": [("Guntur", 40), ("Ongole", 120)],
        "Guntur": [("Narasaraopet", 65)],
        "Narasaraopet": [("Ongole", 100)],
        "Ongole": [],
    }

    print(
        find_best_route(
            sample_graph,
            "Vijayawada",
            "Ongole"
        )
    )
