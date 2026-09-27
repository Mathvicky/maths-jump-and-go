from typing import Any

import pytest
import httpx

from app.routing import (
    RouteCalculationError,
    calculate_driving_miles,
    calculate_osrm_driving_miles,
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

    assert distance == pytest.approx(8047 / 1609.344)
    assert distance > 5
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


@pytest.mark.asyncio
async def test_osrm_driving_distance_fallback() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/route/v1/driving/" in request.url.path
        assert request.headers["user-agent"] == "maths-jump-and-go/0.4"
        return httpx.Response(200, json={
            "code": "Ok",
            "routes": [{"distance": 8046.72}],
        })

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        distance = await calculate_osrm_driving_miles(
            client,
            origin=(51.6287, -0.7482),
            destination=(51.6000, -0.7000),
        )

    assert distance == pytest.approx(5.0)
