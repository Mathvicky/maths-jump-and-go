from typing import Any

import httpx
import pytest

from app.config import Settings
from app.postcodes import PostcodeLocation
from app.quote_service import estimate_car_quote_from_postcode
import app.quote_service as quote_service


class FakeRoutesClient:
    pass


@pytest.mark.asyncio
async def test_estimate_car_quote_from_postcode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    postcode_calls: list[str] = []

    async def fake_lookup_postcode_location(
        postcode: str,
        client: httpx.AsyncClient,
    ) -> PostcodeLocation:
        postcode_calls.append(postcode)

        coordinates = {
            "HP00 0AA": (51.6287, -0.7482),
            "HP11 2AA": (51.6000, -0.7000),
        }

        latitude, longitude = coordinates[postcode]
        return PostcodeLocation(postcode, latitude, longitude, "High Wycombe")

    def fake_calculate_driving_miles(
        client: Any,
        origin: tuple[float, float],
        destination: tuple[float, float],
    ) -> float:
        assert origin == (51.6287, -0.7482)
        assert destination == (51.6000, -0.7000)

        return 4.0

    monkeypatch.setattr(
        quote_service,
        "lookup_postcode_location",
        fake_lookup_postcode_location,
    )

    monkeypatch.setattr(
        quote_service,
        "calculate_driving_miles",
        fake_calculate_driving_miles,
    )

    settings = Settings(
        service_base_postcode="HP00 0AA",
        aws_region="eu-west-2",
        environment="testing",
        _env_file=None,
    )

    async with httpx.AsyncClient() as postcode_client:
        estimated_price, driving_miles, postcode, location, night_rate, out_of_area = (
            await estimate_car_quote_from_postcode(
                customer_postcode="HP11 2AA",
                callout_time="12:00",
                settings=settings,
                postcode_client=postcode_client,
                routes_client=FakeRoutesClient(),
            )
        )

    assert postcode_calls == [
        "HP00 0AA",
        "HP11 2AA",
    ]
    assert driving_miles == 4.0
    assert estimated_price == 45
    assert postcode == "HP11 2AA"
    assert location == "High Wycombe"
    assert night_rate is False
    assert out_of_area is False


@pytest.mark.asyncio
async def test_orchestration_applies_night_multiplier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_lookup_postcode_location(
        postcode: str,
        client: httpx.AsyncClient,
    ) -> PostcodeLocation:
        return PostcodeLocation(postcode, 51.6287, -0.7482, "High Wycombe")

    def fake_calculate_driving_miles(
        client: Any,
        origin: tuple[float, float],
        destination: tuple[float, float],
    ) -> float:
        return 4.0

    monkeypatch.setattr(
        quote_service,
        "lookup_postcode_location",
        fake_lookup_postcode_location,
    )

    monkeypatch.setattr(
        quote_service,
        "calculate_driving_miles",
        fake_calculate_driving_miles,
    )

    settings = Settings(
        service_base_postcode="HP00 0AA",
        aws_region="eu-west-2",
        environment="testing",
        _env_file=None,
    )

    async with httpx.AsyncClient() as postcode_client:
        estimated_price, driving_miles, _postcode, _location, night_rate, out_of_area = (
            await estimate_car_quote_from_postcode(
                customer_postcode="HP11 2AA",
                callout_time="23:00",
                settings=settings,
                postcode_client=postcode_client,
                routes_client=FakeRoutesClient(),
            )
        )

    assert driving_miles == 4.0
    assert estimated_price == 90
    assert night_rate is True
    assert out_of_area is False


@pytest.mark.asyncio
async def test_orchestration_prices_over_15_miles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_lookup_postcode_location(
        postcode: str,
        client: httpx.AsyncClient,
    ) -> PostcodeLocation:
        return PostcodeLocation(postcode, 51.6287, -0.7482, "High Wycombe")

    def fake_calculate_driving_miles(
        client: Any,
        origin: tuple[float, float],
        destination: tuple[float, float],
    ) -> float:
        return 15.1

    monkeypatch.setattr(
        quote_service,
        "lookup_postcode_location",
        fake_lookup_postcode_location,
    )

    monkeypatch.setattr(
        quote_service,
        "calculate_driving_miles",
        fake_calculate_driving_miles,
    )

    settings = Settings(
        service_base_postcode="HP00 0AA",
        aws_region="eu-west-2",
        environment="testing",
        _env_file=None,
    )

    async with httpx.AsyncClient() as postcode_client:
        estimated_price, driving_miles, _postcode, _location, night_rate, out_of_area = (
            await estimate_car_quote_from_postcode(
                customer_postcode="HP11 2AA",
                callout_time="12:00",
                settings=settings,
                postcode_client=postcode_client,
                routes_client=FakeRoutesClient(),
            )
        )

    assert driving_miles == 15.1
    assert estimated_price == 120
    assert night_rate is False
    assert out_of_area is True
