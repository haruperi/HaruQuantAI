"""Lifecycle, isolation, and withdrawal evidence for FEAT-WS-ADMINISTER_SETTINGS.

Covers:
- test_trc_administer_settings_nfr_001: ATN-WS-ADMINISTER_SETTINGS-001 (withdrawal leaves siblings usable and database intact)
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid7

import pytest
from app.contracts.workspace.capabilities import ADMINISTER_SETTINGS_CAPABILITY
from app.contracts.workspace.models import (
    AdministerSettingsRequest,
    AdministerSettingsSuccess,
)
from app.kernel.capability import CapabilityKey
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.workspace.administer_settings._store import init_settings_db
from app.services.workspace.administer_settings.feature import feature


def _context(
    instance: Any,
    registry: ServiceRegistry,
    scope: FeatureScope,
) -> DefaultFeatureContext:
    def register(
        capability: CapabilityKey[Any],
        implementation: object,
        owner_scope: FeatureScope,
    ) -> None:
        registry.register(
            capability,
            implementation,
            owner_id=instance.spec.feature_id,
            scope=owner_scope,
        )

    return DefaultFeatureContext(
        spec=instance.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register,
        event_bus=EventBus(),
    )


def _request(operation: str, **values: object) -> AdministerSettingsRequest:
    return AdministerSettingsRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation=operation,  # type: ignore[arg-type]
        **values,  # type: ignore[arg-type]
    )


@pytest.mark.asyncio
async def test_trc_administer_settings_nfr_001(tmp_path: Path) -> None:
    """ATN-WS-ADMINISTER_SETTINGS-001: exact withdrawal retains state and siblings."""
    db_file = tmp_path / "lifecycle_settings.db"
    init_settings_db(db_file)

    registry = ServiceRegistry()

    # Register an unrelated sibling capability
    unrelated_key: CapabilityKey[object] = CapabilityKey("test.unrelated", 1)
    unrelated = object()
    unrelated_scope = FeatureScope(owner_id="TEST-UNRELATED")
    registry.register(
        unrelated_key,
        unrelated,
        owner_id="TEST-UNRELATED",
        scope=unrelated_scope,
    )

    # Mount AdministerSettingsFeature
    feat = feature()
    feat_scope = FeatureScope(owner_id=feat.spec.feature_id)
    ctx = _context(feat, registry, feat_scope)
    await feat.mount(ctx, {"database_path": db_file})

    provider = registry.require(ADMINISTER_SETTINGS_CAPABILITY)
    assert provider is not None

    # Perform an update to persist custom state
    update_res = await provider.administer_settings(
        _request(
            "UPDATE_SYSTEM",
            settings={"APP_NAME": "HaruQuant AI Prod", "THEME": "dark"},
            changed_by="lifecycle_tester",
        )
    )
    assert isinstance(update_res, AdministerSettingsSuccess)
    assert update_res.system is not None
    persisted_version = update_res.system.version

    # Unmount / withdraw capability
    await feat_scope.close()

    # Verify capability is withdrawn from registry
    assert registry.resolve(ADMINISTER_SETTINGS_CAPABILITY) is None

    # Verify sibling capability remains completely unaffected and resolvable
    assert registry.resolve(unrelated_key) is unrelated

    # Verify database file and underlying tables remain fully intact
    conn = sqlite3.connect(str(db_file))
    try:
        cur = conn.cursor()
        settings_count = cur.execute("SELECT count(*) FROM settings").fetchone()[0]
        history_count = cur.execute("SELECT count(*) FROM settings_history").fetchone()[
            0
        ]
        assert settings_count > 0
        assert history_count > 0

        # Verify saved key is still in SQLite
        row = cur.execute(
            "SELECT value FROM settings WHERE key = 'system.app_name'"
        ).fetchone()
        assert row is not None
        assert row[0] == "HaruQuant AI Prod"
    finally:
        conn.close()

    # Re-mount with a new feature instance
    remount_feat = feature()
    remount_scope = FeatureScope(owner_id=remount_feat.spec.feature_id)
    remount_ctx = _context(remount_feat, registry, remount_scope)
    await remount_feat.mount(remount_ctx, {"database_path": db_file})

    retained_provider = registry.require(ADMINISTER_SETTINGS_CAPABILITY)
    read_res = await retained_provider.administer_settings(_request("READ_SYSTEM"))
    assert isinstance(read_res, AdministerSettingsSuccess)
    assert read_res.system is not None
    assert read_res.system.settings["APP_NAME"] == "HaruQuant AI Prod"
    assert read_res.system.settings["THEME"] == "dark"
    assert read_res.system.version == persisted_version

    await remount_scope.close()
    await unrelated_scope.close()
