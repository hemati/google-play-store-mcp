from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


# --- Reviews ---
class ListReviewsIn(BaseModel):
    """Input for listing Play Store reviews."""
    package_name: str = Field(..., description="Android package name, e.g. 'com.example.app'")
    max_results: int = Field(50, ge=1, le=500)
    translation_language: Optional[str] = Field(None, description="Optional BCP-47 code, e.g. 'en' or 'de'")


class ListReviewsOut(BaseModel):
    """Raw response from Android Publisher reviews.list."""
    data: Dict[str, Any]


class ReplyReviewIn(BaseModel):
    """Input for replying to a Play Store review."""
    package_name: str
    review_id: str
    reply_text: str


class ReplyReviewOut(BaseModel):
    data: Dict[str, Any]


# --- Reporting ---
class CrashRateIn(BaseModel):
    """Input for querying crash rate metrics via Reporting API."""
    package_name: str
    start_date: str  # ISO date YYYY-MM-DD
    end_date: str  # ISO date YYYY-MM-DD
    timezone: str = "Europe/Berlin"


class CrashRateOut(BaseModel):
    data: Dict[str, Any]


class AnrRateIn(BaseModel):
    """Input for querying ANR rate metrics via Reporting API."""
    package_name: str
    start_date: str  # ISO date YYYY-MM-DD
    end_date: str  # ISO date YYYY-MM-DD
    timezone: str = "Europe/Berlin"


class AnrRateOut(BaseModel):
    data: Dict[str, Any]


# --- Experiments ---
class ExperimentCreateIn(BaseModel):
    """Input for creating a store-listing experiment."""
    package_name: str
    experiment_id: str
    variant_id: str
    traffic_percent: int = Field(50, ge=1, le=99)


class ExperimentCreateOut(BaseModel):
    data: Dict[str, Any]


# --- Purchases ---
class SubscriptionGetIn(BaseModel):
    """Input for checking a subscription purchase using SubscriptionsV2."""
    package_name: str
    token: str  # purchase token from the client app


class SubscriptionGetOut(BaseModel):
    data: Dict[str, Any]
