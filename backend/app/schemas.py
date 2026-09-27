from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class QuoteEstimateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    vehicle_type: Literal["car", "van", "large"]
    postcode: str = Field(
        min_length=5,
        max_length=8,
        examples=["HP11 2AA"],
    )
    callout_time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    estimate_id: UUID


class QuoteEstimateResponse(BaseModel):
    pricing_status: Literal[
        "estimated",
        "confirmation_required",
        "manual_quote",
    ]
    estimated_price: int | None
    currency: str = "GBP"
    message: str
    estimate_label: str
    rate_notice: str | None = None
    estimate_id: UUID
    created_at: datetime
    postcode: str
    location: str
    driving_miles: float
    base_postcode: str


class LeadRecord(BaseModel):
    """The complete and deliberately minimal data sent to Google."""

    postcode: str
    vehicle_type: Literal["car", "van", "large"]
    callout_time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    estimated_price: int | None
    timestamp: datetime
    estimate_id: UUID
