from typing import Any

import pytest

from app.routing import (
    RouteCalculationError,
    calculate_driving_miles,
)


class FakeGeoRoutesClient:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.request: dict[str, Any] | None = None

    def calculate_route_matrix(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]:
        self.request = kwargs
        return self.response


def test_calculate_driving_miles() -> None:
    client = FakeGeoRoutesClient(
        {
            "RouteMatrix": [
                [
                    {
                        "Distance": 8047,
                        "Duration": 720,
                    }
                ]
            ]
        }
    )

    distance = calculate_driving_miles(
        client=client,
        origin=(51.6287, -0.7482),
        destination=(51.6000, -0.7000),
    )

    assert distance == 5.0
    assert client.request is not None
    assert client.request["TravelMode"] == "Car"
    assert client.request["OptimizeRoutingFor"] == "FastestRoute"

    assert client.request["Origins"] == [
        {
            "Position": [
                -0.7482,
                51.6287,
            ]
        }
    ]

    assert client.request["Destinations"] == [
        {
            "Position": [
                -0.7000,
                51.6000,
            ]
        }
    ]


def test_empty_route_matrix_is_rejected() -> None:
    client = FakeGeoRoutesClient(
        {
            "RouteMatrix": [],
        }
    )

    with pytest.raises(
        RouteCalculationError,
        match="returned no route result",
    ):
        calculate_driving_miles(
            client=client,
            origin=(51.6287, -0.7482),
            destination=(51.6000, -0.7000),
        )


def test_route_error_is_rejected() -> None:
    client = FakeGeoRoutesClient(
        {
            "RouteMatrix": [
                [
                    {
                        "Error": "NoRoute",
                    }
                ]
            ]
        }
    )

    with pytest.raises(
        RouteCalculationError,
        match="NoRoute",
    ):
        calculate_driving_miles(
            client=client,
            origin=(51.6287, -0.7482),
            destination=(51.6000, -0.7000),
        )


def test_missing_distance_is_rejected() -> None:
    client = FakeGeoRoutesClient(
        {
            "RouteMatrix": [
                [
                    {
                        "Duration": 720,
                    }
                ]
            ]
        }
    )

    with pytest.raises(
        RouteCalculationError,
        match="returned no route distance",
    ):
        calculate_driving_miles(
            client=client,
            origin=(51.6287, -0.7482),
            destination=(51.6000, -0.7000),
        )
