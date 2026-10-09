
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


OSRM_BASE_URL = "https://router.project-osrm.org"


def get_driving_route(
    origin_lon,
    origin_lat,
    destination_lon,
    destination_lat
):
    """Fetch a road route between two longitude/latitude points."""

    coordinates = (
        f"{origin_lon},{origin_lat};"
        f"{destination_lon},{destination_lat}"
    )

    query = urlencode({
        "overview": "false",
        "steps": "false",
    })

    url = (
        f"{OSRM_BASE_URL}/route/v1/driving/"
        f"{coordinates}?{query}"
    )

    request = Request(
        url,
        headers={"User-Agent": "SpiritIQTravelPlanner/1.0"}
    )

    try:
        with urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("code") != "Ok" or not data.get("routes"):
            return {
                "status": "error",
                "message": "No road route was returned by the service."
            }

        route = data["routes"][0]

        return {
            "status": "success",
            "distance_km": round(route["distance"] / 1000, 2),
            "duration_minutes": round(route["duration"] / 60, 1),
            "source": "OSRM demo service",
            "is_live_data": False,
        }

    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        return {
            "status": "error",
            "message": f"Routing service unavailable: {exc}"
        }


if __name__ == "__main__":
    # Example coordinates for Vijayawada and Guntur.
    # These are test inputs, not guaranteed to represent
    # the exact start and end points of a traveller's journey.
    result = get_driving_route(
        origin_lon=80.6480,
        origin_lat=16.5062,
        destination_lon=80.4365,
        destination_lat=16.3067,
    )
    print(result)
