import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.dependencies import (
    PostcodeClientDependency,
    RoutesClientDependency,
    SettingsDependency,
)
from app.postcodes import PostcodeNotFoundError
from app.quote_service import estimate_car_quote_from_postcode
from app.routing import RouteCalculationError
from app.schemas import (
    QuoteEstimateRequest,
    QuoteEstimateResponse,
)


app = FastAPI(
    title="Math's Jump & Go API",
    version="0.3.0",
)
app.mount("/static", StaticFiles(directory="app"), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse("app/index.html")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.post(
    "/api/quotes/estimate",
    response_model=QuoteEstimateResponse,
)
async def estimate_quote(
    request: QuoteEstimateRequest,
    settings: SettingsDependency,
    postcode_client: PostcodeClientDependency,
    routes_client: RoutesClientDependency,
) -> QuoteEstimateResponse:
    if request.vehicle_type == "van":
        return QuoteEstimateResponse(
            pricing_status="confirmation_required",
            estimated_price=None,
            message="Van price requires confirmation before dispatch.",
        )

    if request.vehicle_type == "large":
        return QuoteEstimateResponse(
            pricing_status="manual_quote",
            estimated_price=None,
            message="Large vehicles require a manual quote.",
        )

    try:
        price, _driving_miles = (
            await estimate_car_quote_from_postcode(
                customer_postcode=request.postcode,
                evening_or_weekend=request.evening_or_weekend,
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
    except (RouteCalculationError, httpx.HTTPError) as error:
        raise HTTPException(
            status_code=503,
            detail="The quote service is temporarily unavailable.",
        ) from error

    if price is None:
        return QuoteEstimateResponse(
            pricing_status="manual_quote",
            estimated_price=None,
            message=(
                "This location is outside the standard service area. "
                "Please request a manual quote."
            ),
        )

    return QuoteEstimateResponse(
        pricing_status="estimated",
        estimated_price=price,
        message="Final price will be confirmed before dispatch.",
    )
