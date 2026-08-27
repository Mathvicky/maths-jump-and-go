from fastapi import FastAPI

from app.pricing import calculate_car_price
from app.schemas import (
    QuoteEstimateRequest,
    QuoteEstimateResponse,
)


app = FastAPI(
    title="Math's Jump & Go API",
    version="0.2.0",
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "service": "Math's Jump & Go API",
        "status": "running",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.post(
    "/api/quotes/estimate",
    response_model=QuoteEstimateResponse,
)
def estimate_quote(
    request: QuoteEstimateRequest,
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

    price = calculate_car_price(
        driving_miles=request.driving_miles,
        evening_or_weekend=request.evening_or_weekend,
    )

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
