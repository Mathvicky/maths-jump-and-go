from collections.abc import AsyncIterator
from typing import Any, Annotated

import boto3
import httpx
from fastapi import Depends

from app.config import Settings, get_settings


SettingsDependency = Annotated[
    Settings,
    Depends(get_settings),
]


async def get_postcode_client() -> AsyncIterator[httpx.AsyncClient]:
    """Provide an HTTP client and close it after the request."""

    async with httpx.AsyncClient() as client:
        yield client


def get_routes_client(
    settings: SettingsDependency,
) -> Any:
    """Provide an authenticated Amazon Location client."""

    return boto3.client(
        "geo-routes",
        region_name=settings.aws_region,
    )


PostcodeClientDependency = Annotated[
    httpx.AsyncClient,
    Depends(get_postcode_client),
]

RoutesClientDependency = Annotated[
    Any,
    Depends(get_routes_client),
]
