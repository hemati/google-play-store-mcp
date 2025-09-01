from typing import Any, Dict

from googleapiclient.discovery import build

from ..auth import service_account_credentials, ANDROID_PUBLISHER_SCOPE


def subscriptions_v2_get_impl(package_name: str, token: str) -> Dict[str, Any]:
    """Check the status of a user's subscription.

    Args:
        package_name: The application package name.
        token: Purchase token returned by the client.

    Returns:
        Dict[str, Any]: Raw response from the Android Publisher API.
    """
    creds = service_account_credentials(ANDROID_PUBLISHER_SCOPE)
    svc = build("androidpublisher", "v3", credentials=creds, cache_discovery=False)
    # SubscriptionsV2 does not require subscriptionId; the token encodes it.
    return (
        svc.purchases()
        .subscriptionsv2()
        .get(packageName=package_name, token=token)
        .execute()
    )
