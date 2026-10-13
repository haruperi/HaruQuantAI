"""Unit tests for the dedicated host settings REST API router.

Description:
    Validates that the host settings REST API is decoupled from the host
    business logic and lives cleanly under app.api. Verifies route behavior,
    public projections, secret updates, conflict resolution, revision
    notifications, and architectural boundary invariants.

Purpose:
    FEAT-API-SETTINGS-TEST: Focused verification of app.api.settings endpoints.

Key Capabilities:
    - FR-API-TEST-INVARIANTS: Assert clean module separation and zero FastAPI
      leakage in app.host.settings.
      Associated: `test_architectural_separation_invariants()`
      Logging: DEBUG invariant test step assertions.
    - FR-API-TEST-READ: Assert GET /settings behavior and response payloads.
      Associated: `test_get_settings_endpoint()`
      Logging: DEBUG endpoint response evaluation.
    - FR-API-TEST-UPDATE: Assert PUT /settings revision updates and conflict codes.
      Associated: `test_put_settings_endpoint_and_conflict()`
      Logging: DEBUG endpoint update evaluation.
    - FR-API-TEST-CATALOGUE: Assert GET /settings/catalogue projection.
      Associated: `test_catalogue_endpoint()`
      Logging: DEBUG catalogue evaluation.
    - FR-API-TEST-SECRETS: Assert PUT /settings/secrets write-only updates.
      Associated: `test_secrets_endpoint()`
      Logging: DEBUG secret endpoint evaluation.

Python API Usage:
    ```python
    pytest tests/unit/api/test_settings_api.py
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/api/test_settings_api.py --no-cov
    ```
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.api.router import create_api_router
from app.api.settings import create_settings_router
from app.host import settings as host_settings_module
from app.host.logging import get_logger
from app.host.persistence import SettingsStore
from app.host.settings import HostSettings
from fastapi import FastAPI
from fastapi.testclient import TestClient

logger = get_logger(__name__)


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Provide isolated SQLite database for settings tests."""
    return tmp_path / "test_api_settings.db"


def test_architectural_separation_invariants() -> None:
    """Assert app.host.settings has zero FastAPI dependencies and no router."""
    logger.debug("Verifying architectural separation invariants")
    assert not hasattr(host_settings_module, "create_settings_router")
    assert not hasattr(host_settings_module, "_create_catalogue_router")
    assert not hasattr(host_settings_module, "_extract_put_payload")
    assert not hasattr(host_settings_module, "_extract_secret_payload")
    assert not hasattr(host_settings_module, "_public_settings_snapshot")

    # Assert no fastapi symbol in app.host.settings.__dict__
    for key, val in host_settings_module.__dict__.items():
        if isinstance(val, type) or callable(val):
            module_name = getattr(val, "__module__", "") or ""
            assert not module_name.startswith("fastapi"), (
                f"Leaked FastAPI dependency {key} from {module_name}"
            )


def test_get_settings_endpoint(temp_db: Path) -> None:
    """Test reading settings projection via dedicated API router."""
    store = SettingsStore(temp_db)
    store.initialize()
    host_settings = HostSettings(temp_db)
    router = create_settings_router(host_settings)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.get("/settings")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "values" in body["data"]
    assert "revision" in body["data"]
    assert body["data"]["revision"] >= 1


def test_put_settings_endpoint_and_conflict(temp_db: Path) -> None:
    """Test updating settings with revision guard and conflict detection."""
    store = SettingsStore(temp_db)
    store.initialize()
    host_settings = HostSettings(temp_db)
    revisions: list[int] = []
    router = create_settings_router(host_settings, on_updated=revisions.append)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    # Successful update
    current_rev = host_settings.revision
    update_payload = {
        "expected_revision": current_rev,
        "changes": {
            "app.general": {"theme": "light"},
        },
    }
    response = client.put("/settings", json=update_payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    new_rev = body["data"]["revision"]
    assert new_rev > current_rev
    assert revisions == [new_rev]

    # Stale revision returns 409 Conflict
    stale_payload = {
        "expected_revision": current_rev,
        "changes": {
            "app.general": {"theme": "dark"},
        },
    }
    conflict_response = client.put("/settings", json=stale_payload)
    assert conflict_response.status_code == 409
    conflict_body = conflict_response.json()
    assert conflict_body["status"] == "error"
    assert conflict_body["error"]["code"] == "REVISION_CONFLICT"

    # Invalid payload returns 422
    invalid_payload = {
        "expected_revision": new_rev,
        "changes": {
            "app.general": {"theme": "invalid-theme-value"},
        },
    }
    invalid_response = client.put("/settings", json=invalid_payload)
    assert invalid_response.status_code == 422


def test_catalogue_endpoint(temp_db: Path) -> None:
    """Test safe settings catalogue projection without secret exposure."""
    store = SettingsStore(temp_db)
    store.initialize()
    host_settings = HostSettings(temp_db)
    router = create_settings_router(host_settings)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.get("/settings/catalogue")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    data = body["data"]
    assert "fields" in data
    assert "revision" in data
    # Ensure no secret values are leaked in the catalogue
    for field in data["fields"]:
        if field.get("secret", False):
            assert "value" not in field
            assert "configured" in field


def test_secrets_endpoint(temp_db: Path) -> None:
    """Test write-only secret updates through dedicated API."""
    store = SettingsStore(temp_db)
    store.initialize()
    host_settings = HostSettings(temp_db)
    router = create_settings_router(host_settings)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    current_rev = host_settings.revision
    secret_payload = {
        "expected_revision": current_rev,
        "changes": {
            "notify.email": {"password": "secret-smtp-password"},
        },
    }
    response = client.put("/settings/secrets", json=secret_payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    # Returned catalogue should show configured=True, never the raw password
    fields = {
        f["key"]: f for f in body["data"]["fields"] if f.get("group") == "notify_email"
    }
    assert fields["password"]["configured"] is True
    assert "value" not in fields["password"]


def test_central_api_router_composition(temp_db: Path) -> None:
    """Test mounting settings through create_api_router root aggregator."""
    store = SettingsStore(temp_db)
    store.initialize()
    host_settings = HostSettings(temp_db)
    root_router = create_api_router(host_settings, prefix="/api/v1")

    app = FastAPI()
    app.include_router(root_router)
    client = TestClient(app)

    response = client.get("/api/v1/settings")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
