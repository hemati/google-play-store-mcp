from googleplay_mcp.models import CrashRateIn, AnrRateIn


def test_reporting_model_defaults():
    m = CrashRateIn(package_name="com.example.app", start_date="2025-01-01", end_date="2025-01-31")
    assert m.timezone == "Europe/Berlin"


def test_anr_model_defaults():
    m = AnrRateIn(package_name="com.example.app", start_date="2025-01-01", end_date="2025-01-31")
    assert m.timezone == "Europe/Berlin"
