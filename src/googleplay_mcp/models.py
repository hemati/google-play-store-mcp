from typing import Any, Dict, Optional, List

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


# --- Listings (text/video) ---
class ListLocalizedListingsIn(BaseModel):
    package_name: str


class ListLocalizedListingsOut(BaseModel):
    data: Dict[str, Any]


class GetListingIn(BaseModel):
    package_name: str
    language: str = Field(..., description="BCP-47, e.g. 'en-US'")


class GetListingOut(BaseModel):
    data: Dict[str, Any]


class PatchListingIn(BaseModel):
    package_name: str
    language: str
    title: Optional[str] = None
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    video: Optional[str] = None
    changes_not_sent_for_review: bool = False


class PatchListingOut(BaseModel):
    data: Dict[str, Any]


class UpdateListingIn(BaseModel):
    package_name: str
    language: str
    title: str
    short_description: str
    full_description: str
    video: Optional[str] = None
    changes_not_sent_for_review: bool = False


class UpdateListingOut(BaseModel):
    data: Dict[str, Any]


# --- Images (assets) ---
class ImagesListIn(BaseModel):
    package_name: str
    language: str
    image_type: str = Field(
        ...,
        description=(
            "AppImageType, e.g. 'phoneScreenshots', 'sevenInchScreenshots', 'tenInchScreenshots',\n"
            "'tvScreenshots', 'wearScreenshots', 'icon', 'featureGraphic', 'tvBanner'"
        ),
    )


class ImagesListOut(BaseModel):
    data: Dict[str, Any]


class ImagesDeleteAllIn(BaseModel):
    package_name: str
    language: str
    image_type: str
    changes_not_sent_for_review: bool = False


class ImagesDeleteAllOut(BaseModel):
    data: Dict[str, Any]


class ImagesUploadIn(BaseModel):
    package_name: str
    language: str
    image_type: str
    file_path: str = Field(..., description="Path to local image file")
    mime_type: Optional[str] = None
    changes_not_sent_for_review: bool = False


class ImagesUploadOut(BaseModel):
    data: Dict[str, Any]


# --- App details ---
class DetailsGetIn(BaseModel):
    package_name: str


class DetailsGetOut(BaseModel):
    data: Dict[str, Any]


class DetailsUpdateIn(BaseModel):
    package_name: str
    default_language: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_website: Optional[str] = None
    changes_not_sent_for_review: bool = False


class DetailsUpdateOut(BaseModel):
    data: Dict[str, Any]


# --- Localization Ops ---
class LocaleCoverageIn(BaseModel):
    package_name: str
    target_locales: Optional[List[str]] = Field(
        default=None,
        description="Optional: list of BCP-47 locales to compare against",
    )


class LocaleCoverageOut(BaseModel):
    data: Dict[str, Any]


class CloneListingToLocaleIn(BaseModel):
    package_name: str
    src_language: str
    dst_language: str
    copy_text: bool = True
    copy_video: bool = True
    copy_assets: bool = False
    mirror_image_types: Optional[List[str]] = None
    changes_not_sent_for_review: bool = False


class CloneListingToLocaleOut(BaseModel):
    data: Dict[str, Any]


class ValidateMetadataPolicyIn(BaseModel):
    title: Optional[str] = None
    short_description: Optional[str] = None
    full_description: Optional[str] = None


class ValidateMetadataPolicyOut(BaseModel):
    data: Dict[str, Any]


class AssetSpecCheckIn(BaseModel):
    image_type: str = Field(
        ...,
        description=(
            "'icon' | 'featureGraphic' | 'phoneScreenshots' | 'sevenInchScreenshots' |\n"
            "'tenInchScreenshots' | 'tvScreenshots' | 'wearScreenshots'"
        ),
    )
    file_path: str


class AssetSpecCheckOut(BaseModel):
    data: Dict[str, Any]


class VariantSpecModel(BaseModel):
    label: str
    title: Optional[str] = None
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    video: Optional[str] = None
    assets: Optional[List[List[str]]] = Field(
        default=None,
        description="List of [image_type, file_path] pairs",
    )


class ExperimentsCreatePlanIn(BaseModel):
    package_name: str
    language: str
    name: str
    hypothesis: Optional[str] = None
    metric: str = Field("cvr", description="Optimization metric: e.g., 'cvr' or 'acquisitions'")
    traffic_proportion: float = Field(1.0, ge=0.1, le=1.0)
    type: str = Field("text", description="'text' | 'graphics' | 'mixed'")
    variants: List[VariantSpecModel]
    notes: Optional[str] = None


class ExperimentsCreatePlanOut(BaseModel):
    plan: Dict[str, Any]


class ExperimentsListPlansOut(BaseModel):
    plans: List[Dict[str, Any]]


class ExperimentsGetPlanIn(BaseModel):
    plan_id: str


class ExperimentsGetPlanOut(BaseModel):
    plan: Dict[str, Any]


class ExperimentsDeletePlanIn(BaseModel):
    plan_id: str


class ExperimentsDeletePlanOut(BaseModel):
    deleted: bool


class ExperimentsStartManualIn(BaseModel):
    plan_id: str


class ExperimentsStartManualOut(BaseModel):
    plan_id: str
    status: str
    instructions: List[str]
    variants: List[Dict[str, Any]]
    note: str


class ExperimentsComputeSignificanceIn(BaseModel):
    plan_id: str
    metrics: Dict[str, Dict[str, int]] = Field(
        ..., description="{variant_id: {visitors: int, conversions: int}}"
    )
    samples: int = 20000


class ExperimentsComputeSignificanceOut(BaseModel):
    plan_id: str
    result: Dict[str, Any]


class ExperimentsApplyWinnerIn(BaseModel):
    plan_id: str
    variant_id: str
    changes_not_sent_for_review: bool = False


class ExperimentsApplyWinnerOut(BaseModel):
    plan_id: str
    applied_variant: str
    text_patch: Dict[str, Any]
    asset_uploads: List[Dict[str, Any]]
    status: str


class ExperimentsStopIn(BaseModel):
    plan_id: str


class ExperimentsStopOut(BaseModel):
    plan_id: str
    status: str


class GuardExperimentReadinessIn(BaseModel):
    package_name: str
    language: str


class GuardExperimentReadinessOut(BaseModel):
    locale_present: bool
    present_locales: List[str]
