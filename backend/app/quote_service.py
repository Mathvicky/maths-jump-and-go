from typing import Any

import httpx
from botocore.exceptions import BotoCoreError, ClientError

from app.config import Settings
from app.postcodes import lookup_postcode_location
from app.pricing import calculate_car_price, is_night_time
from app.routing import (
    GeoRoutesClient,
    calculate_driving_miles,
    calculate_osrm_driving_miles,
)


async def estimate_car_quote_from_postcode(
    customer_postcode: str,
    callout_time: str,
    settings: Settings,
    postcode_client: httpx.AsyncClient,
    routes_client: GeoRoutesClient,
) -> tuple[int, float, str, str, bool, bool]:
    """Calculate a car quote using a customer postcode."""

    base_location = await lookup_postcode_location(
        settings.service_base_postcode,
        postcode_client,
    )

    customer_location = await lookup_postcode_location(
        customer_postcode,
        postcode_client,
    )

    origin = (base_location.latitude, base_location.longitude)
    destination = (customer_location.latitude, customer_location.longitude)
    try:
        driving_miles = calculate_driving_miles(
            client=routes_client,
            origin=origin,
            destination=destination,
        )
    except (BotoCoreError, ClientError):
        driving_miles = await calculate_osrm_driving_miles(
            client=postcode_client,
            origin=origin,
            destination=destination,
        )

    night_rate = is_night_time(
        callout_time,
        settings.night_rate_start_hour,
        settings.night_rate_end_hour,
    )
    out_of_area = driving_miles > 15
    estimated_price = calculate_car_price(
        driving_miles=driving_miles,
        night_rate=night_rate,
    )

    return (
        estimated_price,
        driving_miles,
        customer_location.postcode,
        customer_location.place_name,
        night_rate,
        out_of_area,
    )
