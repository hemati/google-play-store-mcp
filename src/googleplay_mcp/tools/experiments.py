from typing import Any, Dict

from googleapiclient.discovery import build

from ..auth import service_account_credentials, ANDROID_PUBLISHER_SCOPE


def create_listing_experiment_impl(
    package_name: str,
    experiment_id: str,
    variant_id: str,
    traffic_percent: int = 50,
) -> Dict[str, Any]:
    """Create a simple store-listing experiment.

    Args:
        package_name: Application package name.
        experiment_id: Identifier for the new experiment.
        variant_id: Identifier for the experiment variant.
        traffic_percent: Percentage of traffic allocated to the variant.

    Returns:
        Dict[str, Any]: API response describing the created experiment.
    """
    creds = service_account_credentials(ANDROID_PUBLISHER_SCOPE)
    svc = build("androidpublisher", "v3", credentials=creds, cache_discovery=False)

    edit = svc.edits().insert(packageName=package_name, body={}).execute()
    edit_id = edit["id"]
    body = {
        "experimentId": experiment_id,
        "trafficPercent": traffic_percent,
        "type": "STORE_LISTING",
        "variants": [
            {
                "experimentVariantId": variant_id,
            }
        ],
    }
    resp = (
        svc.edits()
        .experiments()
        .create(packageName=package_name, editId=edit_id, body=body)
        .execute()
    )
    svc.edits().commit(packageName=package_name, editId=edit_id).execute()
    return resp
