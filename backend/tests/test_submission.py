from datetime import datetime, timezone
from uuid import UUID

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.leads import save_lead_and_notify
from app.main import app
from app.schemas import LeadRecord


ESTIMATE_ID = UUID("82c77659-19e0-4b81-81ef-eed4a84c61b1")
SETTINGS = Settings(
    google_leads_webhook_url="https://script.google.test/exec",
    google_leads_webhook_secret="test-secret",
    _env_file=None,
)


@pytest.mark.asyncio
async def test_lead_webhook_contains_only_six_requested_fields() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(__import__("json").loads(request.content))
        return httpx.Response(200, json={"ok": True})

    lead = LeadRecord(
        postcode="HP11 2AA",
        vehicle_type="car",
        callout_time="12:00",
        estimated_price=45,
        timestamp=datetime.now(timezone.utc),
        estimate_id=ESTIMATE_ID,
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await save_lead_and_notify(lead, SETTINGS, client)

    assert set(captured["lead"]) == {
        "postcode", "vehicle_type", "callout_time", "estimated_price",
        "timestamp", "estimate_id",
    }
    assert captured["secret"] == "test-secret"


@pytest.mark.asyncio
async def test_google_failure_fails_closed() -> None:
    lead = LeadRecord(
        postcode="HP11 2AA", vehicle_type="car", callout_time="12:00",
        estimated_price=45, timestamp=datetime.now(timezone.utc), estimate_id=ESTIMATE_ID,
    )
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"ok": False}))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(Exception) as error:
            await save_lead_and_notify(lead, SETTINGS, client)
    assert error.value.status_code == 503


def test_website_and_assets() -> None:
    client = TestClient(app)
    page = client.get("/website")
    assert page.status_code == 200
    assert 'id="estimate-form"' in page.text
    for name in ["styles.css", "script.js", "config.js", "assets/images/hero-jump-start.jpg"]:
        assert client.get("/static/" + name).status_code == 200
    assert client.get("/static/main.py").status_code == 404


def test_empty_inner_matrix() -> None:
    from unittest.mock import Mock
    from app.routing import calculate_driving_miles, RouteCalculationError
    routes = Mock()
    routes.calculate_route_matrix.return_value = {"RouteMatrix": [[]]}
    with pytest.raises(RouteCalculationError):
        calculate_driving_miles(routes, (0, 0), (1, 1))


def test_unrounded_distance_uses_correct_band() -> None:
    from unittest.mock import Mock
    from app.routing import calculate_driving_miles
    from app.pricing import calculate_car_price
    routes = Mock()
    routes.calculate_route_matrix.return_value = {"RouteMatrix": [[{"Distance": 8047}]]}
    assert calculate_car_price(calculate_driving_miles(routes, (0, 0), (1, 1))) == 55
