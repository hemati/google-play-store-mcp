from mcp.server.fastmcp import FastMCP

from .models import (
    ListReviewsIn, ListReviewsOut,
    ReplyReviewIn, ReplyReviewOut,
    CrashRateIn, CrashRateOut,
    SubscriptionGetIn, SubscriptionGetOut,
)
from .tools.purchases import subscriptions_v2_get_impl
from .tools.reporting import crash_rate_query_impl
from .tools.reviews import list_reviews_impl, reply_review_impl

# Human-friendly server name + instructions (visible to MCP clients)
mcp = FastMCP(
    name="googleplay-mcp",
    instructions=(
        "Tools for Google Play: reviews, replies, crash-rate metrics, and subscription checks. "
        "Authenticated via Google Service Account."
    ),
)


@mcp.tool()
def list_reviews(payload: ListReviewsIn) -> ListReviewsOut:
    """Return recent Play Store reviews for a given package."""
    data = list_reviews_impl(
        package_name=payload.package_name,
        max_results=payload.max_results,
        translation_language=payload.translation_language,
    )
    return ListReviewsOut(data=data)


@mcp.tool()
def reply_to_review(payload: ReplyReviewIn) -> ReplyReviewOut:
    """Reply to a specific Play Store review by its reviewId."""
    data = reply_review_impl(
        package_name=payload.package_name,
        review_id=payload.review_id,
        reply_text=payload.reply_text,
    )
    return ReplyReviewOut(data=data)


@mcp.tool()
def crash_rate(payload: CrashRateIn) -> CrashRateOut:
    """Query crash-rate metrics for a package between two dates (DAILY aggregation)."""
    data = crash_rate_query_impl(
        package_name=payload.package_name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        timezone=payload.timezone,
    )
    return CrashRateOut(data=data)


@mcp.tool()
def get_subscription_v2(payload: SubscriptionGetIn) -> SubscriptionGetOut:
    """Verify a subscription using purchases.subscriptionsv2.get."""
    data = subscriptions_v2_get_impl(
        package_name=payload.package_name,
        token=payload.token,
    )
    return SubscriptionGetOut(data=data)


if __name__ == "__main__":
    # Default: STDIO transport (works with local MCP clients like Claude Desktop / MCP Inspector)
    mcp.run()
