import os
import json

from pydantic import BaseModel


class Settings(BaseModel):
    service_account_json: str
    default_timezone: str = os.environ.get("DEFAULT_TZ", "Europe/Berlin")

    @classmethod
    def from_env(cls) -> "Settings":
        path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
        # Fallback to conventional local path if env var not set
        if not path:
            default_path = os.path.abspath(os.path.join("./secrets", "service_account.json"))
            if os.path.exists(default_path):
                path = default_path
            else:
                raise RuntimeError(
                    "GOOGLE_SERVICE_ACCOUNT_JSON is not set and ./secrets/service_account.json was not found. "
                    "Set the env var or place a Service Account JSON at ./secrets/service_account.json."
                )

        # Normalize to absolute path
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise RuntimeError(f"Credentials file not found at: {path}")

        # Validate that it's a Service Account key (not OAuth client credentials)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to read credentials JSON at {path}: {e}")

        # Service account keys contain type == "service_account" and required fields
        if data.get("type") != "service_account" or not data.get("private_key") or not data.get("client_email"):
            raise RuntimeError(
                "The credentials JSON is not a Service Account key. "
                "Download a Service Account key (type=service_account) from GCP (IAM > Service Accounts > Keys) "
                "and set GOOGLE_SERVICE_ACCOUNT_JSON to its path."
            )

        return cls(service_account_json=path)
