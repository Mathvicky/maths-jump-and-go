from typing import Any, Protocol

import httpx


METRES_PER_MILE = 1609.344
OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"


class RouteCalculationError(RuntimeError):
    """Raised when a driving route cannot be calculated."""


class GeoRoutesClient(Protocol):
    def calculate_route_matrix(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Calculate a route matrix."""


def calculate_driving_miles(
    client: GeoRoutesClient,
    origin: tuple[float, float],
    destination: tuple[float, float],
) -> float:
    """Return driving distance in miles between two coordinates."""

    origin_latitude, origin_longitude = origin
    destination_latitude, destination_longitude = destination

    response = client.calculate_route_matrix(
        Origins=[
            {
                "Position": [
                    origin_longitude,
                    origin_latitude,
                ]
            }
        ],
        Destinations=[
            {
                "Position": [
                    destination_longitude,
                    destination_latitude,
                ]
            }
        ],
        RoutingBoundary={"Unbounded": True},
        TravelMode="Car",
        OptimizeRoutingFor="FastestRoute",
    )

    route_matrix = response.get("RouteMatrix", [])

    if not route_matrix or not route_matrix[0]:
        raise RouteCalculationError(
            "Amazon Location returned no route result."
        )

    route = route_matrix[0][0]

    if route.get("Error"):
        raise RouteCalculationError(
            f"Amazon Location route error: {route['Error']}"
        )

    distance_metres = route.get("Distance")

    if distance_metres is None:
        raise RouteCalculationError(
            "Amazon Location returned no route distance."
        )

    return distance_metres / METRES_PER_MILE


async def calculate_osrm_driving_miles(
    client: httpx.AsyncClient,
    origin: tuple[float, float],
    destination: tuple[float, float],
) -> float:
    """Return an OpenStreetMap road distance when AWS routing is unavailable."""
    origin_latitude, origin_longitude = origin
    destination_latitude, destination_longitude = destination
    coordinates = (
        f"{origin_longitude},{origin_latitude};"
        f"{destination_longitude},{destination_latitude}"
    )
    response = await client.get(
        f"{OSRM_ROUTE_URL}/{coordinates}",
        params={"overview": "false", "alternatives": "false", "steps": "false"},
        headers={"User-Agent": "maths-jump-and-go/0.4"},
        timeout=8.0,
    )
    response.raise_for_status()
    payload = response.json()
    routes = payload.get("routes", [])
    if payload.get("code") != "Ok" or not routes or routes[0].get("distance") is None:
        raise RouteCalculationError("OpenStreetMap returned no route distance.")
    return routes[0]["distance"] / METRES_PER_MILE
