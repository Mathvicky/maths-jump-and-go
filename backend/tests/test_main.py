from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.dependencies import (
    get_postcode_client,
    get_routes_client,
)
from app.main import app
from app.pricing import calculate_car_price


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
                "postcode": "HP11 2AA",
                "latitude": 51.6287,
                "longitude": -0.7482,
                "parish": "Chepping Wycombe",
                "admin_district": "Buckinghamshire",
                "region": "South East",
            },
        },
    )


def override_settings() -> Settings:
    return Settings(
        service_base_postcode="HP00 0AA",
        aws_region="eu-west-2",
        environment="testing",
        vehicle_12v_adjustment=0,
        vehicle_24v_adjustment=30,
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
ESTIMATE_ID = "82c77659-19e0-4b81-81ef-eed4a84c61b1"


@pytest.fixture(autouse=True)
def mock_lead_delivery(monkeypatch: pytest.MonkeyPatch):
    delivered = []

    async def successful_delivery(lead, *args, **kwargs):
        delivered.append(lead)

    monkeypatch.setattr("app.main.save_lead_in_background", successful_delivery)
    return delivered


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


def test_car_quote_uses_postcode(mock_lead_delivery) -> None:
    response = client.post(
        "/api/quotes/estimate",
        json={
            "vehicle_type": "car",
            "postcode": "HP11 2AA",
            "callout_time": "12:00",
            "estimate_id": ESTIMATE_ID,
        },
    )

    assert response.status_code == 200
    assert response.json()["pricing_status"] == "estimated"
    assert response.json()["estimated_price"] == 45
    assert response.json()["postcode"] == "HP11 2AA"
    assert response.json()["location"] == "Chepping Wycombe, Buckinghamshire, South East"
    assert response.json()["driving_miles"] == 4.0
    assert response.json()["base_postcode"] == "HP00 0AA"
    assert mock_lead_delivery[0].model_dump().keys() == {
        "postcode", "vehicle_type", "callout_time", "estimated_price",
        "timestamp", "estimate_id",
    }
    assert mock_lead_delivery[0].postcode == "HP11 2AA"


def test_car_night_quote_doubles_base_price() -> None:
    response = client.post(
        "/api/quotes/estimate",
        json={
            "vehicle_type": "car",
            "postcode": "HP11 2AA",
            "callout_time": "23:00",
            "estimate_id": ESTIMATE_ID,
        },
    )

    assert response.status_code == 200
    assert response.json()["estimated_price"] == 90
    assert response.json()["rate_notice"] == "Night call-out rate applies."


@pytest.mark.parametrize(
    ("miles", "postcode", "location", "callout_time", "expected_price", "expected_label", "expected_notice"),
    [
        (15.0, "OX1 1AA", "Oxford", "12:00", 60, "Your estimate is ready", None),
        (18.4, "LU1 2AA", "Luton", "12:00", 120, "Out-of-area estimate", "Out-of-area rate applies."),
        (35.0, "CB1 1AA", "Cambridge", "12:00", 180, "Out-of-area estimate", "Out-of-area rate applies."),
        (60.0, "BN1 1AA", "Brighton", "12:00", 240, "Out-of-area estimate", "Out-of-area rate applies."),
        (100.0, "B1 1AA", "Birmingham", "12:00", 420, "Out-of-area estimate", "Out-of-area rate applies."),
        (376.3, "EH1 1YZ", "Edinburgh", "12:00", 1560, "Out-of-area estimate", "Out-of-area rate applies."),
        (376.3, "EH1 1YZ", "Edinburgh", "23:00", 3120, "Out-of-area estimate", "Night/out-of-area rate applies."),
    ],
)
def test_uk_distance_boundaries_and_distant_postcode(
    monkeypatch: pytest.MonkeyPatch,
    miles: float,
    postcode: str,
    location: str,
    callout_time: str,
    expected_price: int,
    expected_label: str,
    expected_notice: str | None,
) -> None:
    async def fake_estimate(**kwargs):
        night = callout_time == "23:00"
        out_of_area = miles > 15
        price = calculate_car_price(miles, night_rate=night)
        return price, miles, postcode, location, night, out_of_area

    monkeypatch.setattr("app.main.estimate_car_quote_from_postcode", fake_estimate)
    response = client.post(
        "/api/quotes/estimate",
        json={
            "vehicle_type": "car",
            "postcode": postcode,
            "callout_time": callout_time,
            "estimate_id": ESTIMATE_ID,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["estimated_price"] == expected_price
    assert body["driving_miles"] == miles
    assert body["estimate_label"] == expected_label
    assert body["rate_notice"] == expected_notice


def test_suv_uses_standard_distance_price() -> None:
    response = client.post(
        "/api/quotes/estimate",
        json={
            "vehicle_type": "suv_4x4",
            "postcode": "HP11 2AA",
            "callout_time": "12:00",
            "estimate_id": ESTIMATE_ID,
        },
    )

    assert response.status_code == 200
    assert response.json()["pricing_status"] == "estimated"
    assert response.json()["estimated_price"] == 45


@pytest.mark.parametrize(
    ("callout_time", "expected_price"),
    [("12:00", 45), ("23:00", 90)],
)
def test_12v_van_uses_normal_distance_price(
    callout_time: str,
    expected_price: int,
) -> None:
    response = client.post(
        "/api/quotes/estimate",
        json={
            "vehicle_type": "van_12v",
            "postcode": "HP11 2AA",
            "callout_time": callout_time,
            "estimate_id": ESTIMATE_ID,
        },
    )

    assert response.status_code == 200
    assert response.json()["pricing_status"] == "estimated"
    assert response.json()["estimated_price"] == expected_price


@pytest.mark.parametrize(
    ("callout_time", "expected_price"),
    [("12:00", 75), ("23:00", 150)],
)
def test_24v_adjustment_is_applied_before_night_multiplier(
    callout_time: str,
    expected_price: int,
) -> None:
    response = client.post(
        "/api/quotes/estimate",
        json={
            "vehicle_type": "van_large_24v",
            "postcode": "HP11 2AA",
            "callout_time": callout_time,
            "estimate_id": ESTIMATE_ID,
        },
    )

    assert response.status_code == 200
    assert response.json()["pricing_status"] == "estimated"
    assert response.json()["estimated_price"] == expected_price


def test_specialist_vehicle_requires_manual_quote() -> None:
    response = client.post(
        "/api/quotes/estimate",
        json={
            "vehicle_type": "other_specialist",
            "postcode": "HP11 2AA",
            "callout_time": "12:00",
            "estimate_id": ESTIMATE_ID,
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
            "callout_time": "12:00",
            "estimate_id": ESTIMATE_ID,
        },
    )

    assert response.status_code == 422
