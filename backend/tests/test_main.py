from fastapi.testclient import TestClient

from app.main import app


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


def test_car_quote_standard_hours() -> None:
    response = client.post(
        "/api/quotes/estimate",
        json={
            "vehicle_type": "car",
            "driving_miles": 4,
            "evening_or_weekend": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["estimated_price"] == 45
    assert response.json()["pricing_status"] == "estimated"


def test_car_quote_evening_or_weekend() -> None:
    response = client.post(
        "/api/quotes/estimate",
        json={
            "vehicle_type": "car",
            "driving_miles": 4,
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
            "driving_miles": 4,
            "evening_or_weekend": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["pricing_status"] == "confirmation_required"
    assert response.json()["estimated_price"] is None


def test_large_vehicle_requires_manual_quote() -> None:
    response = client.post(
        "/api/quotes/estimate",
        json={
            "vehicle_type": "large",
            "driving_miles": 4,
            "evening_or_weekend": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["pricing_status"] == "manual_quote"
    assert response.json()["estimated_price"] is None


def test_negative_distance_is_rejected_by_api() -> None:
    response = client.post(
        "/api/quotes/estimate",
        json={
            "vehicle_type": "car",
            "driving_miles": -1,
            "evening_or_weekend": False,
        },
    )

    assert response.status_code == 422
