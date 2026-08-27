from typing import Any

import httpx
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.dependencies import (
    get_postcode_client,
    get_routes_client,
)
from app.main import app


class FakeRoutesClient:
    def calculate_route_matrix(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return {
            "RouteMatrix": [
                [
                    {
                        "Distance": 6437,
                        "Duration": 600,
                    }
                ]
            ]
        }


def postcode_handler(
    request: httpx.Request,
) -> httpx.Response:
    return httpx.Response(
        status_code=200,
        json={
            "status": 200,
            "result": {
                "latitude": 51.6287,
                "longitude": -0.7482,
            },
        },
    )


def override_settings() -> Settings:
    return Settings(
        service_base_postcode="HP00 0AA",
        aws_region="eu-west-2",
        environment="testing",
        _env_file=None,
    )


async def override_postcode_client():
    transport = httpx.MockTransport(postcode_handler)

    async with httpx.AsyncClient(
        transport=transport,
    ) as client:
        yield client


def override_routes_client() -> FakeRoutesClient:
    return FakeRoutesClient()


app.dependency_overrides[get_settings] = override_settings
app.dependency_overrides[get_postcode_client] = (
    override_postcode_client
)
app.dependency_overrides[get_routes_client] = (
    override_routes_client
)

client = TestClient(app)


def test_root_endpoint() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": "Math's Jump & Go API",
        "status": "running",
    }


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
    }


def test_car_quote_uses_postcode() -> None:
    response = client.post(
        "/api/quotes/estimate",
        json={
            "vehicle_type": "car",
            "postcode": "HP11 2AA",
            "evening_or_weekend": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["pricing_status"] == "estimated"
    assert response.json()["estimated_price"] == 45


def test_car_evening_quote_adds_supplement() -> None:
    response = client.post(
        "/api/quotes/estimate",
        json={
            "vehicle_type": "car",
            "postcode": "HP11 2AA",
            "evening_or_weekend": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["estimated_price"] == 55


def test_van_requires_confirmation() -> None:
    response = client.post(
        "/api/quotes/estimate",
        json={
            "vehicle_type": "van",
            "postcode": "HP11 2AA",
            "evening_or_weekend": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["pricing_status"] == (
        "confirmation_required"
    )
    assert response.json()["estimated_price"] is None


def test_large_vehicle_requires_manual_quote() -> None:
    response = client.post(
        "/api/quotes/estimate",
        json={
            "vehicle_type": "large",
            "postcode": "HP11 2AA",
            "evening_or_weekend": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["pricing_status"] == "manual_quote"
    assert response.json()["estimated_price"] is None


def test_short_postcode_is_rejected() -> None:
    response = client.post(
        "/api/quotes/estimate",
        json={
            "vehicle_type": "car",
            "postcode": "HP1",
            "evening_or_weekend": False,
        },
    )

    assert response.status_code == 422
