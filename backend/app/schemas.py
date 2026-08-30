from typing import Literal

from pydantic import BaseModel, Field


class QuoteEstimateRequest(BaseModel):
    vehicle_type: Literal["car", "van", "large"]
    postcode: str = Field(
        min_length=5,
        max_length=8,
        examples=["HP11 2AA"],
    )
    evening_or_weekend: bool = False


class QuoteEstimateResponse(BaseModel):
    pricing_status: Literal[
        "estimated",
        "confirmation_required",
        "manual_quote",
    ]
    estimated_price: int | None
    currency: str = "GBP"
    message: str
