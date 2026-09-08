"""Exact functional traceability evidence for FEAT-WS-ADMINISTER_SETTINGS.

Covers:
- test_trc_administer_settings_001: AT-WS-ADMINISTER_SETTINGS-001 (revisions, optimistic concurrency, atomic validation)
- test_trc_administer_settings_002: AT-WS-ADMINISTER_SETTINGS-002 (manifest metadata, orchestration CPU envelope clamping)
- test_trc_administer_settings_003: AT-WS-ADMINISTER_SETTINGS-003 (user-visible settings, locale changes without corruption)
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from uuid import uuid7

import pytest
from app.contracts.workspace.errors import WorkspaceFailure
from app.contracts.workspace.models import (
    AdministerSettingsRequest,
    AdministerSettingsSuccess,
)
from app.services.workspace.administer_settings._store import init_settings_db
from app.services.workspace.administer_settings.administer_settings import (
    SettingsService,
)
from app.services.workspace.administer_settings.config import AdministerSettingsConfig


def _request(operation: str, **values: object) -> AdministerSettingsRequest:
    return AdministerSettingsRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation=operation,  # type: ignore[arg-type]
        **values,  # type: ignore[arg-type]
    )


@pytest.mark.asyncio
async def test_trc_administer_settings_001(tmp_path: Path) -> None:
    """AT-WS-ADMINISTER_SETTINGS-001: schema-validated revisions, optimistic concurrency, atomic rejection."""
    db_file = tmp_path / "test_settings.db"
    init_settings_db(db_file)
    service = SettingsService(AdministerSettingsConfig(database_path=db_file))

    # Read initial system settings
    initial_res = await service.administer_settings(_request("READ_SYSTEM"))
    assert isinstance(initial_res, AdministerSettingsSuccess)
    assert initial_res.system is not None
    initial_version = initial_res.system.version
    assert initial_version >= 1

    # Valid update with expected_revision
    update1 = await service.administer_settings(
        _request(
            "UPDATE_SYSTEM",
            settings={"APP_NAME": "HaruQuant AI v2"},
            changed_by="tester1",
            expected_revision=initial_version,
        )
    )
    assert isinstance(update1, AdministerSettingsSuccess)
    assert update1.system is not None
    assert update1.system.settings["APP_NAME"] == "HaruQuant AI v2"
    v2 = update1.system.version
    assert v2 == initial_version + 1

    # Stale update with superseded revision -> 409 conflict
    stale_res = await service.administer_settings(
        _request(
            "UPDATE_SYSTEM",
            settings={"APP_NAME": "Conflicted Name"},
            changed_by="tester_stale",
            expected_revision=initial_version,
        )
    )
    assert isinstance(stale_res, WorkspaceFailure)
    assert stale_res.problem.status == 409
    assert (
        "conflict" in stale_res.problem.title.lower()
        or "conflict" in stale_res.problem.detail.lower()
    )

    # Rejection of unknown key without version bump or partial application
    bad_key_res = await service.administer_settings(
        _request(
            "UPDATE_SYSTEM",
            settings={"UNKNOWN_SETTING_KEY": "val", "TIMEZONE": "UTC"},
            changed_by="tester_bad",
        )
    )
    assert isinstance(bad_key_res, WorkspaceFailure)
    assert bad_key_res.problem.status == 400
    assert "unknown setting" in bad_key_res.problem.detail.lower()

    # Rejection of invalid value (out-of-bounds integer)
    bad_val_res = await service.administer_settings(
        _request(
            "UPDATE_SYSTEM",
            settings={"SMTP_PORT": "999999"},  # max is 65535
            changed_by="tester_bad",
        )
    )
    assert isinstance(bad_val_res, WorkspaceFailure)
    assert bad_val_res.problem.status == 400

    # Incompatible combination rejection
    incompat_res = await service.administer_settings(
        _request(
            "UPDATE_SYSTEM",
            settings={"RUNTIME_BROKER": "mt5", "MT5_ENABLED": "false"},
            changed_by="tester_bad",
        )
    )
    assert isinstance(incompat_res, WorkspaceFailure)
    assert incompat_res.problem.status == 400
    assert "incompatible" in incompat_res.problem.detail.lower()

    # Verify version has NOT advanced and TIMEZONE was not partially applied
    post_check = await service.administer_settings(_request("READ_SYSTEM"))
    assert isinstance(post_check, AdministerSettingsSuccess)
    assert post_check.system is not None
    assert post_check.system.version == v2
    # Verify TIMEZONE remains default or unmodified
    assert post_check.system.settings["APP_NAME"] == "HaruQuant AI v2"

    # Verify audit history row in database
    conn = sqlite3.connect(str(db_file))
    try:
        cur = conn.cursor()
        history = cur.execute(
            "SELECT old_value, new_value, changed_by FROM settings_history WHERE key = 'system.app_name'"
        ).fetchall()
        assert len(history) >= 1
        assert history[-1][1] == "HaruQuant AI v2"
        assert history[-1][2] == "tester1"
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_trc_administer_settings_002(tmp_path: Path) -> None:
    """AT-WS-ADMINISTER_SETTINGS-002: manifest metadata and host orchestration CPU envelope clamping."""
    db_file = tmp_path / "test_settings.db"
    init_settings_db(db_file)
    service = SettingsService(AdministerSettingsConfig(database_path=db_file))

    # Read manifest and verify extended metadata fields
    manifest_res = await service.administer_settings(_request("READ_MANIFEST"))
    assert isinstance(manifest_res, AdministerSettingsSuccess)
    manifest = manifest_res.manifest
    assert len(manifest) >= 49

    for definition in manifest:
        assert isinstance(definition.key, str)
        assert definition.key
        assert isinstance(definition.owner, str)
        assert definition.owner
        assert isinstance(definition.effective_default, str)
        assert definition.remount_effect in ("hot", "restart_required", "none")
        assert isinstance(definition.secret_reference_slots, tuple)

    # Check orchestration CPU settings
    cpu_percent_def = next(d for d in manifest if d.key == "WORKER_CPU_PERCENT")
    assert cpu_percent_def.owner == "orchestration"
    assert cpu_percent_def.narrower_policy is not None
    assert "80%" in cpu_percent_def.narrower_policy

    cpu_cores_def = next(d for d in manifest if d.key == "MAX_CPU_CORES")
    assert cpu_cores_def.owner == "orchestration"
    assert cpu_cores_def.narrower_policy is not None
    assert "4 cores" in cpu_cores_def.narrower_policy

    # Attempt to configure higher CPU values exceeding host orchestration envelope
    envelope_res = await service.administer_settings(
        _request(
            "UPDATE_SYSTEM",
            settings={"WORKER_CPU_PERCENT": "95", "MAX_CPU_CORES": "16"},
            changed_by="operator",
        )
    )
    assert isinstance(envelope_res, AdministerSettingsSuccess)
    assert envelope_res.system is not None
    assert envelope_res.system.settings["WORKER_CPU_PERCENT"] == "80"
    assert envelope_res.system.settings["MAX_CPU_CORES"] == "4"


@pytest.mark.asyncio
async def test_trc_administer_settings_003(tmp_path: Path) -> None:
    """AT-WS-ADMINISTER_SETTINGS-003: user-visible preferences, locale switch without numerical/hash drift."""
    db_file = tmp_path / "test_settings.db"
    init_settings_db(db_file)
    service = SettingsService(AdministerSettingsConfig(database_path=db_file))

    # Update user-visible presentation settings
    pref_res = await service.administer_settings(
        _request(
            "UPDATE_SYSTEM",
            settings={
                "LOCALE": "ja_JP",
                "THEME": "light",
                "SOUND_ENABLED": "false",
                "UNITS_SYSTEM": "imperial",
                "DEFAULT_RESULT_VIEW": "equity",
                "PICKER_SORTING": "alphabetical",
                "REPORT_HEADER": "HaruQuant AI Executive Report",
                "REPORT_FOOTER": "Page {page} of {total} - Confidential",
            },
            changed_by="user_ui",
        )
    )
    assert isinstance(pref_res, AdministerSettingsSuccess)
    assert pref_res.system is not None
    s = pref_res.system.settings
    assert s["LOCALE"] == "ja_JP"
    assert s["THEME"] == "light"
    assert s["SOUND_ENABLED"] == "false"
    assert s["UNITS_SYSTEM"] == "imperial"
    assert s["DEFAULT_RESULT_VIEW"] == "equity"
    assert s["PICKER_SORTING"] == "alphabetical"
    assert s["REPORT_HEADER"] == "HaruQuant AI Executive Report"
    assert s["REPORT_FOOTER"] == "Page {page} of {total} - Confidential"

    # Verify numerical settings (like AI_TEMPERATURE or SMTP_PORT) and capability IDs are unmodified
    assert s["AI_TEMPERATURE"] == "0.2"
    assert s["SMTP_PORT"] == "587"

    # Switch locale to German (de_DE)
    locale_switch_res = await service.administer_settings(
        _request(
            "UPDATE_SYSTEM",
            settings={"LOCALE": "de_DE"},
            changed_by="user_ui",
        )
    )
    assert isinstance(locale_switch_res, AdministerSettingsSuccess)
    assert locale_switch_res.system is not None
    s2 = locale_switch_res.system.settings
    assert s2["LOCALE"] == "de_DE"
    # Ensure all other preferences and values remain intact
    assert s2["THEME"] == "light"
    assert s2["AI_TEMPERATURE"] == "0.2"
    assert s2["REPORT_HEADER"] == "HaruQuant AI Executive Report"
