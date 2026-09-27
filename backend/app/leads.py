"""Send the minimal estimate lead to the private Google Apps Script webhook."""

import logging
import httpx
from fastapi import HTTPException

from app.config import Settings
from app.schemas import LeadRecord


logger = logging.getLogger(__name__)


async def save_lead_and_notify(
    lead: LeadRecord,
    settings: Settings,
    client: httpx.AsyncClient,
) -> None:
    if not settings.google_leads_webhook_url or not settings.google_leads_webhook_secret:
        raise HTTPException(503, "Online estimates are not available yet.")

    try:
        response = await client.post(
            settings.google_leads_webhook_url,
            json={
                "secret": settings.google_leads_webhook_secret,
                "lead": lead.model_dump(mode="json"),
            },
            timeout=10.0,
            follow_redirects=True,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("ok") is not True:
            raise ValueError("Google lead webhook did not confirm the write.")
    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(
            503,
            "We could not save your estimate. Please use the call or WhatsApp option instead.",
        ) from error


async def save_lead_in_background(
    lead: LeadRecord,
    settings: Settings,
) -> None:
    """Attempt delivery after the estimate response without exposing failures."""
    try:
        async with httpx.AsyncClient() as client:
            await save_lead_and_notify(lead, settings, client)
    except Exception:
        logger.exception("Estimate lead delivery failed for %s", lead.estimate_id)
