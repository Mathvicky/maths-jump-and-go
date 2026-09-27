import httpx
import pytest

from app.postcodes import lookup_postcode_location


@pytest.mark.asyncio
async def test_postcode_is_converted_to_coordinates_and_place() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/HP12 3GH")
        return httpx.Response(200, json={
            "result": {
                "postcode": "HP12 3GH",
                "latitude": 51.6201,
                "longitude": -0.7692,
                "parish": "Chepping Wycombe",
                "admin_district": "Buckinghamshire",
                "region": "South East",
            }
        })

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        location = await lookup_postcode_location(" hp12 3gh ", client)

    assert location.postcode == "HP12 3GH"
    assert location.latitude == 51.6201
    assert location.longitude == -0.7692
    assert location.place_name == "Chepping Wycombe, Buckinghamshire, South East"


@pytest.mark.asyncio
async def test_unparished_label_is_not_shown() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "result": {
                "postcode": "HP11 2AA",
                "latitude": 51.6,
                "longitude": -0.7,
                "parish": "Wycombe unparished area",
                "admin_district": "Buckinghamshire",
                "region": "South East",
            }
        })

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        location = await lookup_postcode_location("HP11 2AA", client)

    assert location.place_name == "Buckinghamshire, South East"
