from collections.abc import AsyncIterator
from typing import Any, Annotated

import boto3
import httpx
from fastapi import Depends, HTTPException
from botocore.exceptions import BotoCoreError, ClientError

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

    try:
        return boto3.client("geo-routes", region_name=settings.aws_region)
    except (BotoCoreError, ClientError) as error:
        raise HTTPException(503, "The quote service is temporarily unavailable.") from error


PostcodeClientDependency = Annotated[
    httpx.AsyncClient,
    Depends(get_postcode_client),
]

RoutesClientDependency = Annotated[
    Any,
    Depends(get_routes_client),
]
