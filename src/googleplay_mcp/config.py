"""Environment-driven configuration helpers for the MCP server."""

import base64
import binascii
import json
import logging
import os
from pathlib import Path
from typing import Final

from pydantic import BaseModel

mod_path = Path(__file__).parent

SERVICE_ACCOUNT_ENV: Final[str] = "GOOGLE_SERVICE_ACCOUNT_JSON"
SERVICE_ACCOUNT_CONTENT_ENV: Final[str] = "GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT"
SERVICE_ACCOUNT_BASE64_ENV: Final[str] = "GOOGLE_SERVICE_ACCOUNT_JSON_BASE64"
SERVICE_ACCOUNT_INLINE_DESTINATION: Final[Path] = Path("/tmp/googleplay-service-account.json")

logger = logging.getLogger(__name__)


class Settings(BaseModel):
    """Application settings resolved from the environment."""

    service_account_json: str
    default_timezone: str = os.environ.get("DEFAULT_TZ", "Europe/Berlin")

    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings based on environment variables.

        This helper ensures the Google service account credentials are available
        locally. Inline credentials can be supplied via
        ``GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT`` or the base64 encoded
        ``GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`` variables. When inline content is
        provided it is written to a temporary file and the
        ``GOOGLE_SERVICE_ACCOUNT_JSON`` variable is updated to reference that
        path.

        Returns:
            Settings: An initialized settings instance with validated
            credentials.

        Raises:
            RuntimeError: If the credentials cannot be located or decoded, or if
            the JSON document is not a valid service account key.
        """

        path = _resolve_service_account_path()
        _validate_service_account(path)
        return cls(service_account_json=path)


def _resolve_service_account_path() -> str:
    """Locate the service account credentials file on disk.

    Returns:
        str: Absolute path to the service account JSON document.

    Raises:
        RuntimeError: If the credentials cannot be located or inline content
        cannot be decoded.
    """

    path = os.environ.get(SERVICE_ACCOUNT_ENV)
    inline_content = os.environ.get(SERVICE_ACCOUNT_CONTENT_ENV)
    inline_base64 = os.environ.get(SERVICE_ACCOUNT_BASE64_ENV)

    if inline_base64:
        try:
            inline_content = base64.b64decode(inline_base64).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError) as exc:
            raise RuntimeError(
                "Failed to decode GOOGLE_SERVICE_ACCOUNT_JSON_BASE64. Ensure the value "
                "is base64 encoded UTF-8 JSON."
            ) from exc

    if inline_content:
        destination = Path(path) if path else SERVICE_ACCOUNT_INLINE_DESTINATION
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(inline_content, encoding="utf-8")
        path = str(destination.resolve())
        os.environ[SERVICE_ACCOUNT_ENV] = path
        logger.info("Service account JSON written to %s from inline content.", path)

    if not path:
        default_path = mod_path / "../.." / "secrets" / "service_account.json"
        if default_path.exists():
            path = str(default_path.resolve())

    if not path:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON is not set and ./secrets/service_account.json was not found. "
            "Set the env var, provide GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT, or place a Service Account JSON at ./secrets/service_account.json."
        )

    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise RuntimeError(f"Credentials file not found at: {path}")

    return path


def _validate_service_account(path: str) -> None:
    """Validate that the file at ``path`` is a service account JSON key.

    Args:
        path: Absolute path to the credentials file.

    Raises:
        RuntimeError: If the file contents cannot be parsed or if the JSON does
        not represent a service account key.
    """

    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:
        raise RuntimeError(f"Failed to read credentials JSON at {path}: {exc}") from exc

    if data.get("type") != "service_account" or not data.get("private_key") or not data.get("client_email"):
        raise RuntimeError(
            "The credentials JSON is not a Service Account key. Download a Service Account key "
            "(type=service_account) from GCP (IAM > Service Accounts > Keys) and provide its contents via "
            "GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT."
        )
