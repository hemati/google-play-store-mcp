from typing import Any, Dict

from googleapiclient.discovery import build

from ..auth import service_account_credentials, REPORTING_SCOPE


def crash_rate_query_impl(
    package_name: str,
    start_date: str,
    end_date: str,
    timezone: str = "Europe/Berlin",
) -> Dict[str, Any]:
    """Query crash-rate metrics for an app.

    Args:
        package_name: Application package name.
        start_date: Start date in ``YYYY-MM-DD`` format.
        end_date: End date in ``YYYY-MM-DD`` format.
        timezone: IANA timezone identifier for the date range.

    Returns:
        Dict[str, Any]: Crash-rate metrics grouped by version code.
    """
    creds = service_account_credentials(REPORTING_SCOPE)
    svc = build("playdeveloperreporting", "v1beta1", credentials=creds, cache_discovery=False)

    name = f"apps/{package_name}/crashRateMetricSet"
    body = {
        "timelineSpec": {
            "startTime": f"{start_date}T00:00:00Z",
            "endTime": f"{end_date}T23:59:59Z",
            "aggregationPeriod": "DAILY",
            "timezone": timezone,
        },
        "metrics": [
            "crashRate",
            "crashRate7dUserWeighted",
            "crashRate28dUserWeighted",
        ],
        "dimensions": ["versionCode"],
        "pageSize": 1000,
    }
    return svc.vitals().crashrate().query(name=name, body=body).execute()

def anr_rate_query_impl(
    package_name: str,
    start_date: str,
    end_date: str,
    timezone: str = "Europe/Berlin",
) -> Dict[str, Any]:
    """Query ANR-rate metrics for an app.

    Args:
        package_name: Application package name.
        start_date: Start date in ``YYYY-MM-DD`` format.
        end_date: End date in ``YYYY-MM-DD`` format.
        timezone: IANA timezone identifier for the date range.

    Returns:
        Dict[str, Any]: ANR-rate metrics grouped by version code.
    """
    creds = service_account_credentials(REPORTING_SCOPE)
    svc = build("playdeveloperreporting", "v1beta1", credentials=creds, cache_discovery=False)

    name = f"apps/{package_name}/anrRateMetricSet"
    body = {
        "timelineSpec": {
            "startTime": f"{start_date}T00:00:00Z",
            "endTime": f"{end_date}T23:59:59Z",
            "aggregationPeriod": "DAILY",
            "timezone": timezone,
        },
        "metrics": [
            "anrRate",
            "anrRate7dUserWeighted",
            "anrRate28dUserWeighted",
        ],
        "dimensions": ["versionCode"],
        "pageSize": 1000,
    }
    return svc.vitals().anrrate().query(name=name, body=body).execute()
