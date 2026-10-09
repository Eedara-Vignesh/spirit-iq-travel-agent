
import heapq


def dijkstra(graph, start, destination):
    """
    Find the lowest-weight path between two nodes.

    graph format:
    {
        "A": [("B", 10), ("C", 4)],
        "B": [("D", 3)],
        "C": [("B", 2), ("D", 8)],
        "D": []
    }

    Each edge weight can represent distance, time, or cost.
    All weights must be non-negative.
    """
    if start not in graph or destination not in graph:
        return {
            "status": "error",
            "message": "Start or destination is missing from graph."
        }

    distances = {node: float("inf") for node in graph}
    previous = {node: None for node in graph}
    distances[start] = 0

    priority_queue = [(0, start)]

    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)

        if current_distance > distances[current_node]:
            continue

        if current_node == destination:
            break

        for neighbor, weight in graph[current_node]:
            if weight < 0:
                raise ValueError("Dijkstra requires non-negative weights.")

            new_distance = current_distance + weight

            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous[neighbor] = current_node
                heapq.heappush(
                    priority_queue,
                    (new_distance, neighbor)
                )

    if distances[destination] == float("inf"):
        return {
            "status": "error",
            "message": "No route found."
        }

    path = []
    node = destination

    while node is not None:
        path.append(node)
        node = previous[node]

    path.reverse()

    return {
        "status": "success",
        "path": path,
        "total_weight": distances[destination]
    }


if __name__ == "__main__":
    graph = {
        "A": [("B", 10), ("C", 4)],
        "B": [("D", 3)],
        "C": [("B", 2), ("D", 8)],
        "D": []
    }

    print(dijkstra(graph, "A", "D"))
