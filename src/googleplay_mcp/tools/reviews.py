from typing import Any, Dict

from googleapiclient.discovery import build

from ..auth import service_account_credentials, ANDROID_PUBLISHER_SCOPE


def list_reviews_impl(
        package_name: str,
        max_results: int = 50,
        translation_language: str | None = None,
) -> Dict[str, Any]:
    """List recent reviews for an app.

    Args:
        package_name: Application package name.
        max_results: Maximum number of reviews to return.
        translation_language: Optional BCP-47 language code for translations.

    Returns:
        Dict[str, Any]: Review data from the Android Publisher API.
    """
    creds = service_account_credentials(ANDROID_PUBLISHER_SCOPE)
    svc = build("androidpublisher", "v3", credentials=creds, cache_discovery=False)
    req = svc.reviews().list(packageName=package_name, maxResults=max_results)
    if translation_language:
        req = req.add_query_parameter("translationLanguage", translation_language)
    return req.execute()


def reply_review_impl(package_name: str, review_id: str, reply_text: str) -> Dict[str, Any]:
    """Post a developer reply to a review.

    Args:
        package_name: Application package name.
        review_id: Identifier of the review to reply to.
        reply_text: Text of the developer reply.

    Returns:
        Dict[str, Any]: API response containing the updated review state.
    """
    creds = service_account_credentials(ANDROID_PUBLISHER_SCOPE)
    svc = build("androidpublisher", "v3", credentials=creds, cache_discovery=False)
    body = {"replyText": reply_text}
    return svc.reviews().reply(packageName=package_name, reviewId=review_id, body=body).execute()
