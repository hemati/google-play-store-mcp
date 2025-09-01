import os

import pytest


@pytest.fixture(autouse=True)
def _env_defaults(monkeypatch):
    # Point to a dummy/non-existent SA file for unit-level import safety.
    # Integration tests should override with a real path.
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON",
                       os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "./secrets/service_account.json"))
