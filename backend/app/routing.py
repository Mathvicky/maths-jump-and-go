from typing import Any, Protocol


METRES_PER_MILE = 1609.344


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

    if not route_matrix or not route_matrix:
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

    return round(distance_metres / METRES_PER_MILE, 2)
