from typing import Any, Dict

from googleapiclient.discovery import build

from ..auth import service_account_credentials, REPORTING_SCOPE


def _parse_date(date_str: str) -> Dict[str, int]:
    """Parse a ``YYYY-MM-DD`` string into year/month/day dict."""
    parts = date_str.split("-")
    return {"year": int(parts[0]), "month": int(parts[1]), "day": int(parts[2])}


def _make_datetime(date_str: str, hours: int = 0) -> Dict[str, Any]:
    """Build a ``google.type.DateTime`` structured object.

    The Play Developer Reporting API only accepts year/month/day/hours —
    minutes, seconds, nanos, utcOffset, and timeZone must be unset.
    """
    dt = _parse_date(date_str)
    dt["hours"] = hours
    return dt


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
        timezone: Unused, kept for backwards compatibility.

    Returns:
        Dict[str, Any]: Crash-rate metrics grouped by version code.
    """
    creds = service_account_credentials(REPORTING_SCOPE)
    svc = build("playdeveloperreporting", "v1beta1", credentials=creds, cache_discovery=False)

    name = f"apps/{package_name}/crashRateMetricSet"
    body = {
        "timelineSpec": {
            "startTime": _make_datetime(start_date),
            "endTime": _make_datetime(end_date),
            "aggregationPeriod": "DAILY",
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
        timezone: Unused, kept for backwards compatibility.

    Returns:
        Dict[str, Any]: ANR-rate metrics grouped by version code.
    """
    creds = service_account_credentials(REPORTING_SCOPE)
    svc = build("playdeveloperreporting", "v1beta1", credentials=creds, cache_discovery=False)

    name = f"apps/{package_name}/anrRateMetricSet"
    body = {
        "timelineSpec": {
            "startTime": _make_datetime(start_date),
            "endTime": _make_datetime(end_date),
            "aggregationPeriod": "DAILY",
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
