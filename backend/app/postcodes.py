from urllib.parse import quote

import httpx


POSTCODES_API_URL = "https://api.postcodes.io/postcodes"


class PostcodeNotFoundError(ValueError):
    """Raised when a UK postcode cannot be found."""


def normalise_postcode(postcode: str) -> str:
    return " ".join(postcode.strip().upper().split())


async def lookup_postcode(
    postcode: str,
    client: httpx.AsyncClient,
) -> tuple[float, float]:
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

    return result["latitude"], result["longitude"]
