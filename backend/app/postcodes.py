from urllib.parse import quote
from dataclasses import dataclass

import httpx


POSTCODES_API_URL = "https://api.postcodes.io/postcodes"


class PostcodeNotFoundError(ValueError):
    """Raised when a UK postcode cannot be found."""


@dataclass(frozen=True)
class PostcodeLocation:
    postcode: str
    latitude: float
    longitude: float
    place_name: str


def normalise_postcode(postcode: str) -> str:
    return " ".join(postcode.strip().upper().split())


async def lookup_postcode(
    postcode: str,
    client: httpx.AsyncClient,
) -> tuple[float, float]:
    location = await lookup_postcode_location(postcode, client)
    return location.latitude, location.longitude


async def lookup_postcode_location(
    postcode: str,
    client: httpx.AsyncClient,
) -> PostcodeLocation:
    normalised = normalise_postcode(postcode)

    if not normalised:
        raise PostcodeNotFoundError("A postcode is required.")

    encoded_postcode = quote(normalised, safe="")

    response = await client.get(
        f"{POSTCODES_API_URL}/{encoded_postcode}",
        timeout=5.0,
    )

    if response.status_code == 404:
        raise PostcodeNotFoundError("Postcode could not be found.")

    response.raise_for_status()

    payload = response.json()
    result = payload["result"]

    normalised_result = normalise_postcode(result.get("postcode") or normalised)
    place_parts = []
    parish = result.get("parish")
    if parish and "unparished" not in parish.lower():
        place_parts.append(parish)
    for value in (result.get("admin_district"), result.get("region")):
        if value and value not in place_parts:
            place_parts.append(value)

    return PostcodeLocation(
        postcode=normalised_result,
        latitude=result["latitude"],
        longitude=result["longitude"],
        place_name=", ".join(place_parts) or normalised_result,
    )
