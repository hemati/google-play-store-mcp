from google.oauth2 import service_account

from .config import Settings

ANDROID_PUBLISHER_SCOPE = "https://www.googleapis.com/auth/androidpublisher"
REPORTING_SCOPE = "https://www.googleapis.com/auth/playdeveloperreporting"


def service_account_credentials(scope: str):
    """Return Google credentials for a given scope based on env config."""
    settings = Settings.from_env()
    creds = service_account.Credentials.from_service_account_file(
        settings.service_account_json, scopes=[scope]
    )
    return creds
