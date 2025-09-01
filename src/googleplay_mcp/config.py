import os

from pydantic import BaseModel


class Settings(BaseModel):
    service_account_json: str
    default_timezone: str = os.environ.get("DEFAULT_TZ", "Europe/Berlin")

    @classmethod
    def from_env(cls) -> "Settings":
        path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not path:
            raise RuntimeError(
                "GOOGLE_SERVICE_ACCOUNT_JSON is not set. Point it to your Service Account JSON file."
            )
        return cls(service_account_json=path)
