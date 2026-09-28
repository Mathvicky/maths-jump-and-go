from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_base_postcode: str = "HP12 3GH"
    aws_region: str = "eu-west-2"
    environment: str = "development"
    google_leads_webhook_url: str = ""
    google_leads_webhook_secret: str = ""
    allowed_origins: list[str] = []
    night_rate_start_hour: int = Field(default=22, ge=0, le=23)
    night_rate_end_hour: int = Field(default=7, ge=0, le=23)
    vehicle_12v_adjustment: int = Field(default=0, ge=0)
    vehicle_24v_adjustment: int = Field(default=30, ge=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
