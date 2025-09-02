"""MCP server exposing Google Play tools.

This module wires together tool implementations and registers them with a
`FastMCP` instance so that they can be invoked by MCP clients.
"""

from fastmcp import FastMCP

from .models import (
    ListReviewsIn,
    ListReviewsOut,
    ReplyReviewIn,
    ReplyReviewOut,
    CrashRateIn,
    CrashRateOut,
    AnrRateIn,
    AnrRateOut,
    ExperimentCreateIn,
    ExperimentCreateOut,
    SubscriptionGetIn,
    SubscriptionGetOut,
    ListLocalizedListingsIn,
    ListLocalizedListingsOut,
    GetListingIn,
    GetListingOut,
    PatchListingIn,
    PatchListingOut,
    UpdateListingIn,
    UpdateListingOut,
    ImagesListIn,
    ImagesListOut,
    ImagesDeleteAllIn,
    ImagesDeleteAllOut,
    ImagesUploadIn,
    ImagesUploadOut,
    DetailsGetIn,
    DetailsGetOut,
    DetailsUpdateIn,
    DetailsUpdateOut,

    LocaleCoverageIn,
    LocaleCoverageOut,
    CloneListingToLocaleIn,
    CloneListingToLocaleOut,
    ValidateMetadataPolicyIn,
    ValidateMetadataPolicyOut,
    AssetSpecCheckIn,
    AssetSpecCheckOut,
)
from .tools.experiments import create_listing_experiment_impl
from .tools.listings import (
    list_localized_listings_impl,
    get_listing_impl,
    patch_listing_impl,
    update_listing_impl,
    images_list_impl,
    images_deleteall_impl,
    images_upload_impl,
    details_get_impl,
    details_update_impl,
)


from tools.localization import (
    list_locale_coverage_impl,
    clone_listing_to_locale_impl,
    validate_metadata_policy_impl,
    asset_spec_check_impl,
)
from .tools.purchases import subscriptions_v2_get_impl
from .tools.reviews import list_reviews_impl, reply_review_impl
# from .tools.reporting import crash_rate_query_impl, anr_rate_query_impl


# Human-friendly server name + instructions (visible to MCP clients)
mcp = FastMCP(
    name="googleplay-mcp",
    instructions=(
        "Tools for Google Play: reviews, replies, crash- and ANR-rate metrics, listing "
        "experiments, and subscription checks. Authenticated via Google Service Account."
    ),
)


@mcp.tool()
def list_reviews(payload: ListReviewsIn) -> ListReviewsOut:
    """Fetch recent Play Store reviews for a package.

    Args:
        payload: Parameters including the package name, maximum number of
            results to return and an optional translation language.

    Returns:
        ListReviewsOut: Review data returned by the Android Publisher API.
    """
    data = list_reviews_impl(
        package_name=payload.package_name,
        max_results=payload.max_results,
        translation_language=payload.translation_language,
    )
    return ListReviewsOut(data=data)


@mcp.tool()
def reply_to_review(payload: ReplyReviewIn) -> ReplyReviewOut:
    """Send a reply to a specific Play Store review.

    Args:
        payload: Includes the package name, the review identifier and the
            reply text.

    Returns:
        ReplyReviewOut: API response confirming the reply.
    """
    data = reply_review_impl(
        package_name=payload.package_name,
        review_id=payload.review_id,
        reply_text=payload.reply_text,
    )
    return ReplyReviewOut(data=data)


# @mcp.tool()
# def crash_rate(payload: CrashRateIn) -> CrashRateOut:
#     """Retrieve crash-rate metrics for a package over a date range.
#
#     Args:
#         payload: Contains the package name, start and end dates and an optional
#             timezone for interpreting the date range.
#
#     Returns:
#         CrashRateOut: Crash-rate metrics from the Play Developer Reporting API.
#     """
#     data = crash_rate_query_impl(
#         package_name=payload.package_name,
#         start_date=payload.start_date,
#         end_date=payload.end_date,
#         timezone=payload.timezone,
#     )
#     return CrashRateOut(data=data)
#
#
# @mcp.tool()
# def anr_rate(payload: AnrRateIn) -> AnrRateOut:
#     """Retrieve ANR-rate metrics for a package over a date range.
#
#     Args:
#         payload: Contains the package name, start and end dates and an optional
#             timezone for interpreting the date range.
#
#     Returns:
#         AnrRateOut: ANR-rate metrics from the Play Developer Reporting API.
#     """
#     data = anr_rate_query_impl(
#         package_name=payload.package_name,
#         start_date=payload.start_date,
#         end_date=payload.end_date,
#         timezone=payload.timezone,
#     )
#     return AnrRateOut(data=data)


@mcp.tool()
def get_subscription_v2(payload: SubscriptionGetIn) -> SubscriptionGetOut:
    """Verify a user's subscription purchase.

    Args:
        payload: Includes the application package name and the purchase token
            returned by the client.

    Returns:
        SubscriptionGetOut: Result from the
        `purchases.subscriptionsv2.get` API call.
    """
    data = subscriptions_v2_get_impl(
        package_name=payload.package_name,
        token=payload.token,
    )
    return SubscriptionGetOut(data=data)


@mcp.tool()
def create_listing_experiment(payload: ExperimentCreateIn) -> ExperimentCreateOut:
    """Create a store-listing experiment for a package.

    Args:
        payload: Includes the package name, experiment ID, variant ID and the
            traffic percentage assigned to the variant.

    Returns:
        ExperimentCreateOut: API response describing the created experiment.
    """
    data = create_listing_experiment_impl(
        package_name=payload.package_name,
        experiment_id=payload.experiment_id,
        variant_id=payload.variant_id,
        traffic_percent=payload.traffic_percent,
    )
    return ExperimentCreateOut(data=data)


@mcp.tool()
def list_localized_listings(payload: ListLocalizedListingsIn) -> ListLocalizedListingsOut:
    """Return all localized store listings for the current edit."""
    data = list_localized_listings_impl(package_name=payload.package_name)
    return ListLocalizedListingsOut(data=data)


@mcp.tool()
def get_listing(payload: GetListingIn) -> GetListingOut:
    """Get a single localized listing by language (BCP-47)."""
    data = get_listing_impl(package_name=payload.package_name, language=payload.language)
    return GetListingOut(data=data)


@mcp.tool()
def patch_listing(payload: PatchListingIn) -> PatchListingOut:
    """Patch fields of a localized listing (send only fields you want to change)."""
    data = patch_listing_impl(
        package_name=payload.package_name,
        language=payload.language,
        title=payload.title,
        short_description=payload.short_description,
        full_description=payload.full_description,
        video=payload.video,
        changes_not_sent_for_review=payload.changes_not_sent_for_review,
    )
    return PatchListingOut(data=data)


@mcp.tool()
def update_listing(payload: UpdateListingIn) -> UpdateListingOut:
    """Create or replace a localized listing (full object)."""
    data = update_listing_impl(
        package_name=payload.package_name,
        language=payload.language,
        title=payload.title,
        short_description=payload.short_description,
        full_description=payload.full_description,
        video=payload.video,
        changes_not_sent_for_review=payload.changes_not_sent_for_review,
    )
    return UpdateListingOut(data=data)


@mcp.tool()
def images_list(payload: ImagesListIn) -> ImagesListOut:
    """List images for a language & type (e.g., 'phoneScreenshots')."""
    data = images_list_impl(
        package_name=payload.package_name,
        language=payload.language,
        image_type=payload.image_type,
    )
    return ImagesListOut(data=data)


@mcp.tool()
def images_deleteall(payload: ImagesDeleteAllIn) -> ImagesDeleteAllOut:
    """Delete all images for a language & type."""
    data = images_deleteall_impl(
        package_name=payload.package_name,
        language=payload.language,
        image_type=payload.image_type,
        changes_not_sent_for_review=payload.changes_not_sent_for_review,
    )
    return ImagesDeleteAllOut(data=data)


@mcp.tool()
def images_upload(payload: ImagesUploadIn) -> ImagesUploadOut:
    """Upload a single image for a language & type and commit the edit."""
    data = images_upload_impl(
        package_name=payload.package_name,
        language=payload.language,
        image_type=payload.image_type,
        file_path=payload.file_path,
        mime_type=payload.mime_type,
        changes_not_sent_for_review=payload.changes_not_sent_for_review,
    )
    return ImagesUploadOut(data=data)


@mcp.tool()
def details_get(payload: DetailsGetIn) -> DetailsGetOut:
    """Fetch app details (default language & support contacts)."""
    data = details_get_impl(package_name=payload.package_name)
    return DetailsGetOut(data=data)


@mcp.tool()
def details_update(payload: DetailsUpdateIn) -> DetailsUpdateOut:
    """Update default language and developer support contacts for the app."""
    data = details_update_impl(
        package_name=payload.package_name,
        default_language=payload.default_language,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        contact_website=payload.contact_website,
        changes_not_sent_for_review=payload.changes_not_sent_for_review,
    )
    return DetailsUpdateOut(data=data)


@mcp.tool()
def list_locale_coverage(payload: LocaleCoverageIn) -> LocaleCoverageOut:
    """List existing localized listing languages and (optionally) compare to a target set."""
    data = list_locale_coverage_impl(
        package_name=payload.package_name,
        target_locales=payload.target_locales,
    )
    return LocaleCoverageOut(data=data)


@mcp.tool()
def clone_listing_to_locale(payload: CloneListingToLocaleIn) -> CloneListingToLocaleOut:
    """Clone a localized listing from `src_language` to `dst_language`. Optionally mirror assets and video."""
    data = clone_listing_to_locale_impl(
        package_name=payload.package_name,
        src_language=payload.src_language,
        dst_language=payload.dst_language,
        copy_text=payload.copy_text,
        copy_video=payload.copy_video,
        copy_assets=payload.copy_assets,
        mirror_image_types=payload.mirror_image_types,
        changes_not_sent_for_review=payload.changes_not_sent_for_review,
    )
    return CloneListingToLocaleOut(data=data)


@mcp.tool()
def validate_metadata_policy(payload: ValidateMetadataPolicyIn) -> ValidateMetadataPolicyOut:
    """Validate metadata strings (title/short/full) against Play policy and limits."""
    data = validate_metadata_policy_impl(
        title=payload.title,
        short_description=payload.short_description,
        full_description=payload.full_description,
    )
    return ValidateMetadataPolicyOut(data=data)


@mcp.tool()
def asset_spec_check(payload: AssetSpecCheckIn) -> AssetSpecCheckOut:
    """Validate a local image file against Google Play size/format requirements."""
    data = asset_spec_check_impl(image_type=payload.image_type, file_path=payload.file_path)
    return AssetSpecCheckOut(data=data)


if __name__ == "__main__":
    # Default: STDIO transport (works with local MCP clients like Claude Desktop / MCP Inspector)
    mcp.run(transport="streamable-http")
