from typing import Any

import httpx

from app.config import Settings
from app.postcodes import lookup_postcode
from app.pricing import calculate_car_price
from app.routing import GeoRoutesClient, calculate_driving_miles


async def estimate_car_quote_from_postcode(
    customer_postcode: str,
    evening_or_weekend: bool,
    settings: Settings,
    postcode_client: httpx.AsyncClient,
    routes_client: GeoRoutesClient,
) -> tuple[int | None, float]:
    """Calculate a car quote using a customer postcode."""

    base_coordinates = await lookup_postcode(
        settings.service_base_postcode,
        postcode_client,
    )

    customer_coordinates = await lookup_postcode(
        customer_postcode,
        postcode_client,
    )

    driving_miles = calculate_driving_miles(
        client=routes_client,
        origin=base_coordinates,
        destination=customer_coordinates,
    )

    estimated_price = calculate_car_price(
        driving_miles=driving_miles,
        evening_or_weekend=evening_or_weekend,
    )

    return estimated_price, driving_miles
