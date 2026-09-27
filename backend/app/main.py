import httpx
import logging
from datetime import datetime, timezone
from pathlib import Path
from botocore.exceptions import BotoCoreError, ClientError
from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.dependencies import (
    PostcodeClientDependency,
    RoutesClientDependency,
    SettingsDependency,
)
from app.postcodes import PostcodeNotFoundError, normalise_postcode
from app.leads import save_lead_in_background
from app.quote_service import estimate_car_quote_from_postcode
from app.routing import RouteCalculationError
from app.schemas import (
    QuoteEstimateRequest,
    QuoteEstimateResponse,
    LeadRecord,
)
from app.config import get_settings


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Math's Jump & Go API",
    version="0.3.0",
)
frontend_directory = Path(__file__).resolve().parents[2] / "frontend"
if not frontend_directory.exists():
    frontend_directory = Path(__file__).resolve().parents[2] / "app"
app.mount("/static", StaticFiles(directory=frontend_directory, html=True), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().allowed_origins,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "service": "Math's Jump & Go API",
        "status": "running",
    }
@app.get("/website")
async def serve_frontend():
    return RedirectResponse("/static/index.html")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.post(
    "/api/quotes/estimate",
    response_model=QuoteEstimateResponse,
)
async def estimate_quote(
    request: QuoteEstimateRequest,
    background_tasks: BackgroundTasks,
    settings: SettingsDependency,
    postcode_client: PostcodeClientDependency,
    routes_client: RoutesClientDependency,
) -> QuoteEstimateResponse:
    created_at = datetime.now(timezone.utc)

    async def save_and_respond(
        pricing_status: str,
        estimated_price: int | None,
        message: str,
        estimate_label: str,
        rate_notice: str | None,
        driving_miles: float,
        postcode: str,
        location: str,
    ) -> QuoteEstimateResponse:
        lead = LeadRecord(
            postcode=normalise_postcode(request.postcode),
            vehicle_type=request.vehicle_type,
            callout_time=request.callout_time,
            estimated_price=estimated_price,
            timestamp=created_at,
            estimate_id=request.estimate_id,
        )
        background_tasks.add_task(
            save_lead_in_background,
            lead,
            settings,
        )
        return QuoteEstimateResponse(
            pricing_status=pricing_status,
            estimated_price=estimated_price,
            message=message,
            estimate_label=estimate_label,
            rate_notice=rate_notice,
            estimate_id=request.estimate_id,
            created_at=created_at,
            postcode=postcode,
            location=location,
            driving_miles=round(driving_miles, 1),
            base_postcode=normalise_postcode(settings.service_base_postcode),
        )

    try:
        if not settings.service_base_postcode:
            raise HTTPException(503, "Online estimates are not available yet.")
        price, driving_miles, postcode, location, night_rate, out_of_area = (
            await estimate_car_quote_from_postcode(
                customer_postcode=request.postcode,
                callout_time=request.callout_time,
                settings=settings,
                postcode_client=postcode_client,
                routes_client=routes_client,
            )
        )
    except PostcodeNotFoundError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except (RouteCalculationError, httpx.HTTPError, BotoCoreError, ClientError, KeyError, ValueError) as error:
        logger.exception("Quote calculation failed")
        raise HTTPException(
            status_code=503,
            detail="The quote service is temporarily unavailable.",
        ) from error

    if request.vehicle_type == "van":
        return await save_and_respond(
            "confirmation_required",
            None,
            "Van price requires confirmation. Call or WhatsApp us now.",
            "Your estimate requires confirmation",
            None,
            driving_miles,
            postcode,
            location,
        )

    if request.vehicle_type == "large":
        return await save_and_respond(
            "manual_quote",
            None,
            "Large vehicles require a manual quote. Call or WhatsApp us now.",
            "Manual quote required",
            None,
            driving_miles,
            postcode,
            location,
        )

    estimate_label = "Out-of-area estimate" if out_of_area else "Your estimate is ready"
    if night_rate and out_of_area:
        rate_notice = "Night/out-of-area rate applies."
    elif night_rate:
        rate_notice = "Night call-out rate applies."
    elif out_of_area:
        rate_notice = "Out-of-area rate applies."
    else:
        rate_notice = None

    return await save_and_respond(
        "estimated",
        price,
        "Estimated call-out price. Final price is confirmed before dispatch.",
        estimate_label,
        rate_notice,
        driving_miles,
        postcode,
        location,
    )
