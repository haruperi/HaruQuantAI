"""Unit and lifecycle tests for the administer-settings feature."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from uuid import uuid7

import pytest
from app.contracts.workspace.models import (
    AdministerSettingsRequest,
    AdministerSettingsSuccess,
    BridgeRuntimeSettings,
)
from app.services.workspace.administer_settings.administer_settings import (
    SettingsService,
    read_bridge_runtime,
)
from app.services.workspace.administer_settings.config import AdministerSettingsConfig
from app.services.workspace.administer_settings.manifest import SPEC


def _init_settings_db(db_path: Path) -> None:
    """Create schema for settings and settings_history tables in test db."""
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                value TEXT NOT NULL,
                value_type TEXT NOT NULL,
                category TEXT NOT NULL,
                label TEXT NOT NULL,
                description TEXT NOT NULL,
                is_secret INTEGER NOT NULL DEFAULT 0,
                is_readonly INTEGER NOT NULL DEFAULT 0,
                default_value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT NOT NULL,
                changed_by TEXT NOT NULL DEFAULT 'system',
                changed_at TEXT NOT NULL
            );
            """
        )


def _request(operation: str, **kwargs: object) -> AdministerSettingsRequest:
    """Build one operation request."""
    return AdministerSettingsRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation=operation,  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )


def test_manifest_spec() -> None:
    """Verify feature specification and declared durable state."""
    assert SPEC.feature_id == "FEAT-WS-ADMINISTER_SETTINGS"
    (provided,) = SPEC.provides
    assert provided.identifier == "workspace.administer-settings@1"
    assert SPEC.state is not None
    assert SPEC.state.namespace == "workspace.administer_settings"
    SPEC.validate()


def test_read_bridge_runtime_defaults(tmp_path: Path) -> None:
    """Verify bridge runtime fallback when no db rows exist."""
    db_file = tmp_path / "test_settings.db"
    _init_settings_db(db_file)
    bridge = read_bridge_runtime(db_path=db_file)
    assert isinstance(bridge, BridgeRuntimeSettings)
    assert bridge.host == "127.0.0.1"
    assert bridge.port == 9001
    assert bridge.source_id == "mt5-terminal-1"
    assert bridge.symbols == "EURUSD,GBPUSD,USDJPY,XAUUSD"


@pytest.mark.asyncio
async def test_settings_service_operations(tmp_path: Path) -> None:
    """Verify READ_SYSTEM, UPDATE_SYSTEM, READ_MANIFEST, CREDENTIAL_STATUS, and STORE_CREDENTIAL."""
    db_file = tmp_path / "test_settings.db"
    _init_settings_db(db_file)
    service = SettingsService(AdministerSettingsConfig(database_path=db_file))

    # Read manifest
    manifest_res = await service.administer_settings(_request("READ_MANIFEST"))
    assert isinstance(manifest_res, AdministerSettingsSuccess)
    assert len(manifest_res.manifest) == 59

    # Read system settings (seeds defaults)
    read_res = await service.administer_settings(_request("READ_SYSTEM"))
    assert isinstance(read_res, AdministerSettingsSuccess)
    assert read_res.system is not None
    assert read_res.system.scope == "system"
    assert "ACCOUNT_MODE" in read_res.system.settings

    # Update system settings
    update_res = await service.administer_settings(
        _request(
            "UPDATE_SYSTEM",
            settings={"ACCOUNT_MODE": "demo"},
            changed_by="admin_test",
        )
    )
    assert isinstance(update_res, AdministerSettingsSuccess)
    assert update_res.system is not None
    assert update_res.system.settings["ACCOUNT_MODE"] == "demo"
    assert update_res.system.version >= 1

    # Credential status
    cred_res = await service.administer_settings(_request("READ_CREDENTIALS"))
    assert isinstance(cred_res, AdministerSettingsSuccess)
    assert len(cred_res.credentials) > 0
    google_slot = next(c for c in cred_res.credentials if c.slot == "google")
    assert google_slot.configured is False

    # Store credential
    store_res = await service.administer_settings(
        _request(
            "UPDATE_CREDENTIAL",
            slot="google",
            material={
                "credentials.google_api_key": "SecretKey123",  # pragma: allowlist secret
            },
            changed_by="admin_test",
        )
    )
    assert isinstance(store_res, AdministerSettingsSuccess)
    assert store_res.credential_updated is True

    # Re-check credential status
    cred_res2 = await service.administer_settings(_request("READ_CREDENTIALS"))
    assert isinstance(cred_res2, AdministerSettingsSuccess)
    google_slot2 = next(c for c in cred_res2.credentials if c.slot == "google")
    assert google_slot2.configured is True

    # Read bridge runtime
    bridge_res = await service.administer_settings(_request("READ_BRIDGE_RUNTIME"))
    assert isinstance(bridge_res, AdministerSettingsSuccess)
    assert bridge_res.bridge is not None
    assert bridge_res.bridge.host == "127.0.0.1"
