from typing import Any, Dict

from googleapiclient.discovery import build

from ..auth import service_account_credentials, ANDROID_PUBLISHER_SCOPE


def list_reviews_impl(package_name: str, max_results: int = 50, translation_language: str | None = None) -> Dict[
    str, Any]:
    """Call Android Publisher API reviews.list."""
    creds = service_account_credentials(ANDROID_PUBLISHER_SCOPE)
    svc = build("androidpublisher", "v3", credentials=creds, cache_discovery=False)
    req = svc.reviews().list(packageName=package_name, maxResults=max_results)
    if translation_language:
        req = req.add_query_parameter("translationLanguage", translation_language)
    return req.execute()


def reply_review_impl(package_name: str, review_id: str, reply_text: str) -> Dict[str, Any]:
    """Call Android Publisher API reviews.reply."""
    creds = service_account_credentials(ANDROID_PUBLISHER_SCOPE)
    svc = build("androidpublisher", "v3", credentials=creds, cache_discovery=False)
    body = {"replyText": reply_text}
    return svc.reviews().reply(packageName=package_name, reviewId=review_id, body=body).execute()
