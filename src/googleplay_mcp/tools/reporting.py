from typing import Any, Dict

from googleapiclient.discovery import build

from ..auth import service_account_credentials, REPORTING_SCOPE


def crash_rate_query_impl(package_name: str, start_date: str, end_date: str, timezone: str = "Europe/Berlin") -> Dict[
    str, Any]:
    """Query crash rate metrics for an app between two dates using Reporting API."""
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
            "crashRate28dUserWeighted"
        ],
        "dimensions": ["versionCode"],
        "pageSize": 1000,
    }
    return svc.vitals().crashrate().query(name=name, body=body).execute()
