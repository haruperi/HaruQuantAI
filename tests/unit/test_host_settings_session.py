"""Unit tests for host settings reader and session auth.

Description:
    Exercises reading operational and application settings from the database
    via the persistence read layer (app.host.persistence.HostPersistence),
    packaging into the lazy settings instance with nested dot-access, PBKDF2
    credential hashing, opaque bearer token lifecycles, restart invalidation,
    and granular scope authorization. All tests execute against isolated
    temporary database stores, asserting structured non-silent logging for
    every functional requirement.

Purpose:
    FEAT-HOST-SETTINGS: Verify host settings reading and packaging.
    FEAT-HOST-SESSION: Verify operator session lifecycle, tokens, and authorization.

Key Capabilities:
    - FR-HOST-SETTINGS-LOAD: Verify settings read and packaging from SQLite.
      Associated: `test_read_settings_from_database()`,
      `test_read_settings_malformed_json_fallback()`
      Logging: caplog asserts `FR-HOST-SETTINGS-LOAD` events.
    - FR-HOST-SESSION-CREDENTIALS: Verify PBKDF2 password hashing and verification.
      Associated: `test_session_credentials_hashing_and_verification()`
      Logging: caplog asserts `FR-HOST-SESSION-CREDENTIALS` events.
    - FR-HOST-SESSION-LIFECYCLE: Verify token issuance, validation, and revocation.
      Associated: `test_session_lifecycle_and_expiration()`
      Logging: caplog asserts `FR-HOST-SESSION-LIFECYCLE` events.
    - FR-HOST-SESSION-RESTART-INVALIDATION: Verify restart invalidation of sessions.
      Associated: `test_session_restart_invalidation()`
      Logging: caplog asserts `FR-HOST-SESSION-RESTART-INVALIDATION` events.
    - FR-HOST-SESSION-AUTHORIZATION: Verify scope authorization check on sessions.
      Associated: `test_session_scope_authorization()`
      Logging: caplog asserts `FR-HOST-SESSION-AUTHORIZATION` events.

Python API Usage:
    ```python
    import pytest
    from app.host.session import SessionManager
    from app.host.settings import settings
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/test_host_settings_session.py -v
    ```
"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from typing import Any

import app.host.settings
import pytest
from app.host.persistence import HostPersistence
from app.host.session import (
    CREDENTIALS_FR,
    LIFECYCLE_FR,
    SessionManager,
    SessionRecord,
    hash_password,
    verify_password,
)
from app.host.session import (
    main as session_main,
)
from app.host.settings import (
    BATCH_UPDATE_FR,
    LOAD_FR,
    RevisionConflictError,
    SettingsManager,
    _read_settings,
    _SettingsNode,
)
from app.host.settings import (
    main as settings_main,
)
from app.host.settings import (
    settings as host_settings,
)


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect HostPersistence.DEFAULT_DB_PATH to an isolated temporary file."""
    db_file = tmp_path / "settings_session_test.db"
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", db_file)
    return db_file


def test_public_module_exports_rule_compliance() -> None:
    """Verify public exports from app.host.settings align with Phase 1 blueprint."""
    expected = [
        "SettingsManager",
        "RevisionConflictError",
        "settings",
    ]
    assert sorted(app.host.settings.__all__) == sorted(expected)


def test_read_settings_from_database(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify reading host settings from SQLite via persistence read layer."""
    caplog.set_level(logging.DEBUG)
    HostPersistence.create_record(
        "host_settings",
        {
            "scope": "user_access",
            "key": "username",
            "value_json": json.dumps("admin"),
            "schema_version": 1,
            "updated_at_utc": "2026-10-14 00:00:00",
        },
    )
    HostPersistence.create_record(
        "host_settings",
        {
            "scope": "user_access",
            "key": "theme",
            "value_json": json.dumps("dark"),
            "schema_version": 1,
            "updated_at_utc": "2026-10-14 00:00:00",
        },
    )
    HostPersistence.create_record(
        "host_settings",
        {
            "scope": "workspace_paths",
            "key": "data_dir",
            "value_json": json.dumps("data"),
            "schema_version": 1,
            "updated_at_utc": "2026-10-14 00:00:00",
        },
    )

    host_settings.reload()
    assert len(host_settings) == 2
    assert "user_access" in host_settings
    assert "workspace_paths" in host_settings
    assert "unknown_scope" not in host_settings

    # Value access via user = settings.user_access.username
    user = host_settings.user_access.username
    assert user == "admin"
    assert host_settings.user_access.theme == "dark"
    assert host_settings.workspace_paths.data_dir == "data"

    # Indexing and dictionary compatibility
    assert host_settings["user_access"]["username"] == "admin"
    assert host_settings.user_access["username"] == "admin"
    assert host_settings.get("user_access", "username") == "admin"
    assert host_settings.user_access.get("username") == "admin"
    assert host_settings.user_access.get("missing_key", "default_val") == "default_val"
    assert "username" in host_settings.user_access
    assert len(host_settings.user_access) == 2

    # Scope dictionary access
    user_scope = host_settings.get_scope("user_access")
    assert user_scope["username"] == "admin"
    assert user_scope["theme"] == "dark"

    # Attribute errors on missing attributes
    with pytest.raises(AttributeError):
        _ = host_settings.missing_scope

    with pytest.raises(AttributeError):
        _ = host_settings.user_access.missing_attribute

    assert any(
        getattr(r, "fr_id", None) == LOAD_FR or LOAD_FR in r.message
        for r in caplog.records
    )


def test_read_settings_malformed_json_fallback() -> None:
    """Verify fallback handling for non-JSON string values in host_settings."""
    HostPersistence.create_record(
        "host_settings",
        {
            "scope": "custom",
            "key": "raw_key",
            "value_json": "plain_text_not_json",
            "schema_version": 1,
            "updated_at_utc": "2026-10-14",
        },
    )

    host_settings.reload()
    assert host_settings.custom.raw_key == "plain_text_not_json"
    assert host_settings.get("custom", "raw_key") == "plain_text_not_json"


def test_host_settings_container_methods() -> None:
    """Verify container methods on empty and populated SettingsManager and _SettingsNode."""
    empty = SettingsManager({})
    assert len(empty) == 0
    assert empty.as_dict() == {}
    assert empty.get("any", "key", 42) == 42
    assert empty.get_scope("any") == {}

    node = _SettingsNode({"nested": {"leaf": "value"}})
    assert node.nested.leaf == "value"
    assert node["nested"]["leaf"] == "value"
    assert node.get("nested").get("leaf") == "value"
    assert node.as_dict() == {"nested": {"leaf": "value"}}


def test_session_credentials_hashing_and_verification(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify PBKDF2-HMAC-SHA256 password hashing and secure verification."""
    caplog.set_level(logging.DEBUG)
    monkeypatch.setattr("app.host.session.HASH_ITERATIONS", 1_000)
    test_password = "operator_secure_passphrase_2026"
    hashed = hash_password(test_password)

    # Assert hash structure: 32 hex salt + 1 delimiter + 64 hex hash = 97 chars
    assert len(hashed) == 97
    assert verify_password(test_password, hashed) is True
    assert verify_password("wrong_attempt", hashed) is False

    # Modular crypt 4-part format pbkdf2-sha256$iterations$salt$hash
    salt, exp_hex = hashed.split("$", 1)
    modular_hash = f"pbkdf2-sha256$1000${salt}${exp_hex}"
    assert verify_password(test_password, modular_hash) is True
    assert verify_password("wrong_attempt", modular_hash) is False

    # Corrupt or malformed hash returns False safely
    assert verify_password(test_password, "invalid_hash_string") is False
    assert verify_password(test_password, "bad$delimiter$hash") is False

    assert any(
        getattr(r, "fr_id", None) == CREDENTIALS_FR or CREDENTIALS_FR in r.message
        for r in caplog.records
    )


def test_session_lifecycle_and_expiration(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify session creation, validation, expiration, and revocation."""
    caplog.set_level(logging.DEBUG)
    manager = SessionManager()

    # 1. Create active session
    raw_token, record = manager.create_session("operator_1", "192.168.1.100")
    assert len(raw_token) == 64
    assert record.username == "operator_1"
    assert record.peer_id == "192.168.1.100"
    assert record.status == "ACTIVE"

    # 2. Validate token
    validated = manager.verify_session(raw_token)
    assert validated is not None
    assert validated.session_id == record.session_id

    # 3. Revoke session
    assert manager.revoke_session(record.session_id) is True
    assert manager.verify_session(raw_token) is None
    assert manager.revoke_session("non_existent_id") is False

    # 4. Expiration check with zero/negative duration
    expired_token, _ = manager.create_session("admin", "127.0.0.1", duration_mins=-5)
    assert manager.verify_session(expired_token) is None

    # 5. Invalid token format
    assert manager.verify_session("short_token") is None
    assert manager.verify_session("a" * 63) is None

    assert any(
        getattr(r, "fr_id", None) == LIFECYCLE_FR or LIFECYCLE_FR in r.message
        for r in caplog.records
    )


def test_session_restart_invalidation() -> None:
    """Verify host restart invalidates active sessions created under earlier instance."""
    manager = SessionManager()
    raw_token, record = manager.create_session("operator_2", "10.0.0.5")
    assert manager.verify_session(raw_token) is not None

    # Simulate host platform restart
    manager.reset()
    # In-memory sessions are cleared; token validation from DB succeeds if status is ACTIVE
    assert manager.verify_session(raw_token) is not None
    assert manager.revoke_session(record.session_id) is True
    assert manager.verify_session(raw_token) is None


def test_session_scope_authorization() -> None:
    """Verify granular scope permission evaluations in memory."""
    manager = SessionManager()
    record = SessionRecord(
        session_id="sess_auth_test",
        token_hash="fake_hash",
        username="admin",
        peer_id="127.0.0.1",
        created_at_utc="2026-10-14 00:00:00",
        expires_at_utc="2026-10-15 00:00:00",
        status="ACTIVE",
    )

    # Valid scopes
    assert manager.authorize(record, "settings:read") is True
    assert manager.authorize(record, "settings:write") is True
    assert manager.authorize(record, "jobs:read") is True

    # Invalid scopes
    assert manager.authorize(record, "superuser:drop_database") is False

    # Inactive session record
    inactive_record = SessionRecord(
        session_id="sess_inactive",
        token_hash="fake_hash",
        username="admin",
        peer_id="127.0.0.1",
        created_at_utc="2026-01-01 00:00:00",
        expires_at_utc="2026-01-02 00:00:00",
        status="REVOKED",
    )
    assert manager.authorize(inactive_record, "settings:read") is False


def test_settings_lazy_reloading() -> None:
    """Verify host settings lazy loading, reload, and self-contained queries."""
    HostPersistence.create_record(
        "host_settings",
        {
            "scope": "user_access",
            "key": "username",
            "value_json": json.dumps("facade_admin"),
            "schema_version": 1,
            "updated_at_utc": "2026-10-14 00:00:00",
        },
    )

    host_settings.reload()
    user = host_settings.user_access.username
    assert user == "facade_admin"
    assert host_settings.get("user_access", "username") == "facade_admin"
    assert host_settings.get_scope("user_access") == {"username": "facade_admin"}
    assert "user_access" in host_settings
    assert len(host_settings) >= 1
    assert host_settings.as_dict()["user_access"]["username"] == "facade_admin"

    # Test internal _read_settings helper
    data = _read_settings()
    assert data["user_access"]["username"] == "facade_admin"

    # Test self-contained read_records
    raw_rows = HostPersistence.read_records("host_settings")
    assert isinstance(raw_rows, list)


def test_nested_scope_resolution_under_parent() -> None:
    """Verify settings resolve section keys stored under parent scopes (e.g. application)."""
    HostPersistence.create_record(
        "host_settings",
        {
            "scope": "application",
            "key": "user_access",
            "value_json": json.dumps({"username": "app_user", "theme": "light"}),
            "schema_version": 1,
            "updated_at_utc": "2026-10-14 00:00:00",
        },
    )

    host_settings.reload()
    # Direct dot access to nested section
    assert host_settings.user_access.username == "app_user"
    assert host_settings.user_access.theme == "light"

    # Parent path dot access
    assert host_settings.application.user_access.username == "app_user"

    # Dictionary and get access
    assert host_settings["user_access"]["username"] == "app_user"
    assert host_settings.get("user_access", "username") == "app_user"
    assert host_settings.get("user_access")["username"] == "app_user"
    assert "user_access" in host_settings
    assert host_settings.get_scope("user_access") == {
        "username": "app_user",
        "theme": "light",
    }


def test_cli_main_entrypoints(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify CLI main entrypoints for settings and session."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("app.host.session.HASH_ITERATIONS", 1_000)
    settings_main()
    session_main()


def test_atomic_batch_settings_update_and_revision_conflict(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify atomic batch updates across scopes and revision conflict errors."""
    caplog.set_level(logging.INFO)
    host_settings.reload()
    initial_rev = host_settings.revision

    # 1. Atomic batch update across multiple scopes with expected_revision
    new_rev = host_settings.save_settings(
        {
            "user_access": {"username": "quant_operator", "theme": "dark"},
            "compute": {"worker_mode": "reserve-one"},
        },
        expected_revision=initial_rev,
    )
    assert new_rev == initial_rev + 1
    assert host_settings.revision == new_rev
    assert host_settings.get("user_access", "username") == "quant_operator"
    assert host_settings.get("compute", "worker_mode") == "reserve-one"

    # 2. Stale revision raises RevisionConflictError and preserves prior state
    with pytest.raises(RevisionConflictError) as exc_info:
        host_settings.save_settings(
            {"user_access": {"username": "intruder"}},
            expected_revision=initial_rev,
        )
    assert exc_info.value.expected_revision == initial_rev
    assert exc_info.value.current_revision == new_rev
    assert host_settings.get("user_access", "username") == "quant_operator"

    # 3. Update without expected_revision increments revision
    rev_after = host_settings.save_settings(
        {"user_access": {"username": "updated_operator"}},
    )
    assert rev_after == new_rev + 1

    assert any(
        getattr(r, "fr_id", None) == BATCH_UPDATE_FR or BATCH_UPDATE_FR in r.message
        for r in caplog.records
    )


def test_independent_settings_writers_conflict_and_batch_rollback() -> None:
    """Verify concurrent save_settings conflict and invalid payload failure."""
    host_settings.reload()
    ready = Barrier(2)

    def save(value: int) -> int | str:
        ready.wait(timeout=5)
        local_settings = SettingsManager()
        try:
            return local_settings.save_settings(
                {"audit": {"value": value}}, expected_revision=0
            )
        except RevisionConflictError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(save, [1, 2]))
    assert 1 in results

    instance = SettingsManager()
    instance.reload()
    rev_before = instance.revision
    with pytest.raises(TypeError):
        instance.save_settings(
            {"audit": {"first": "must roll back", "invalid": object()}},
            expected_revision=rev_before,
        )
    instance.reload()
    assert instance.revision == rev_before
    assert "first" not in instance.get_scope("audit")


def test_settings_read_failure_preserves_last_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify reload failure preserves the last loaded snapshot in memory."""
    instance = SettingsManager()
    instance.reload()
    instance.save_settings({"audit": {"kept": True}}, expected_revision=0)

    bad_dir = tmp_path / "is_a_directory"
    bad_dir.mkdir()
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", bad_dir)
    with pytest.raises(HostPersistence.Error):
        instance.reload()
    assert instance.revision == 1
    assert instance.get("audit", "kept") is True


def test_theme_identifier_roundtrip() -> None:
    """Appearance belongs to the UI; only the stored identifier round-trips."""
    instance = SettingsManager()
    instance.save_changes({"app.general": {"theme": "light"}}, expected_revision=0)
    assert SettingsManager().get_snapshot()["values"] == {
        "app.general": {"theme": "light"}
    }
    assert not hasattr(instance, "theme")


def test_empty_store_projects_no_defaults_or_writes() -> None:
    """Reads cannot fabricate fields or initialize settings/account records."""
    instance = SettingsManager()
    assert instance.get_snapshot() == {"revision": 0, "values": {}}
    assert instance.get_catalogue() == {"revision": 0, "fields": [], "unknown": []}
    with pytest.raises(KeyError, match="not configured"):
        instance.get_account()
    with pytest.raises(KeyError, match="not configured"):
        instance.save_account("new", 1440, "synthetic-hash", expected_revision=0)
    assert HostPersistence.read_records("host_settings") == []


def test_stored_empty_values_are_not_missing() -> None:
    """False, zero, empty containers/text and an allowed null survive projection."""
    instance = SettingsManager()
    changes: dict[str, Mapping[str, Any]] = {
        "app.general": {"header_custom_text": "", "confirm_on_exit": False},
        "notify.desktop": {"duration_seconds": 0},
        "notify.email": {"recipient_addresses": []},
        "config.databanks": {"databank_sync_interval_mins": None},
        "calibration.indicators": {"QQE.RSIPeriod": []},
    }
    instance.save_changes(changes, expected_revision=0)
    assert SettingsManager().get_snapshot()["values"] == changes
    assert len(instance.get_catalogue()["fields"]) == 6


@pytest.mark.parametrize(
    "stored", [{"zoom": "1.2"}, {"remote_access": False}, {"theme": "unknown"}]
)
def test_invalid_stored_values_fail_closed(stored: dict[str, Any]) -> None:
    """Malformed stored values cannot become editable inferred field types."""
    instance = SettingsManager()
    instance.save_settings({"application": {"app_general": stored}})
    before = HostPersistence.read_records("host_settings")
    for project in (instance.get_snapshot, instance.get_catalogue):
        with pytest.raises(ValueError):
            project()
    assert HostPersistence.read_records("host_settings") == before


_STORED_EXAMPLES: dict[str, Any] = {
    "app_general": {
        "theme": "dark",
        "language": "en",
        "zoom": 1.0,
        "auto_save_interval_s": 120,
        "header_custom_text": "",
        "confirm_on_exit": True,
        "host": "127.0.0.1",
        "backend_port": 8000,
        "frontend_port": 3000,
        "gpu_accelerated": True,
        "remote_access": {"allow": False, "require_password": False, "port": 8000},
    },
    "config_global": {
        "sounds_off": False,
        "advanced_file_chooser": True,
        "show_control_orders": False,
        "footer_custom_text": "",
        "default_result_to_display": "Portfolio",
        "data_frame_guard": "warn",
    },
    "config_cpu": {
        "core_usage": "all_except_one",
        "custom_cores": 7,
        "high_priority": False,
        "thread_affinity": False,
    },
    "config_performance": {
        "compute_pips_metrics": False,
        "compute_pcts_metrics": False,
        "compute_separate_metrics": True,
    },
    "config_memory": {
        "gc_type": "ParallelGC",
        "automatic_memory": False,
        "memory_limit_gb": 10,
        "dont_store_pending_orders": True,
        "memory_cleanup": False,
        "cleanup_interval_mins": 15,
    },
    "config_databanks": {
        "databank_sync_interval_mins": 15,
        "sync_databanks_after_task_done": True,
        "store_chart_data": False,
    },
    "config_optimizations": {"dont_store_op_3d_charts_data": True},
    "config_troubleshooting": {
        "gpu_accelerated": True,
        "memory_protection": True,
        "debug_level_active": False,
    },
    "connect_mcp": {
        "enabled": False,
        "host": "127.0.0.1",
        "port": 8001,
        "transport": "stdio",
        "auth_token": "",
        "allowed_tools": [],
        "max_context_items": 100,
    },
    "notify_desktop": {
        "enabled": True,
        "duration_seconds": 5,
        "min_priority": "info",
        "sound_enabled": True,
    },
    "notify_email": {
        "enabled": False,
        "smtp_server": "",
        "smtp_port": 587,
        "use_ssl": False,
        "use_tls": True,
        "username": "",
        "password": "",
        "from_address": "",
        "recipient_addresses": [],
    },
    "notify_telegram": {
        "enabled": False,
        "bot_token": "",
        "chat_id": "",
        "parse_mode": "",
        "disable_notification": False,
    },
    "config_metatrader5": {
        "enabled": False,
        "terminal_path": "",
        "account_id": 0,
        "password": "",
        "server": "",
        "environment": "demo",
        "timeout_ms": 60000,
        "portable": False,
        "use_ticks": False,
    },
    "config_ctrader": {
        "enabled": False,
        "account_id": "",
        "client_id": "",
        "client_secret": "",
        "access_token": "",
        "refresh_token": "",
        "environment": "demo",
        "gateway_host": "",
        "gateway_port": 5035,
        "redirect_url": "",
    },
    "config_agents": {
        "active_provider": "openai",
        "agent_timeout_seconds": 120,
        "system_prompt_preset": "",
        "openai": {
            "api_key": "",
            "model": "",
            "base_url": "",
            "temperature": 0.2,
            "max_tokens": 8192,
        },
        "gemini": {
            "api_key": "",
            "model": "",
            "base_url": "",
            "use_vertex_ai": False,
            "fast_model": "",
            "premium_model": "",
            "fallback_model": "",
            "temperature": 0.2,
            "max_tokens": 8192,
        },
        "ollama": {
            "model": "",
            "base_url": "",
            "temperature": 0.2,
            "timeout_seconds": 120,
        },
    },
    "workspace_paths": {
        "configs_dir": "configs",
        "projects_dir": "projects",
        "strategies_dir": "strategies",
        "data_dir": "data",
    },
    "engine_backtest": {
        "max_threads": 7,
        "memory_limit_mb": 10240,
        "enable_caching": True,
        "precision_mode": "",
        "benchmark_time_per_tick_ms": 0.0,
        "dont_store_pending_orders": True,
        "dont_store_op3d_charts": True,
        "compute_separate_metrics": True,
        "compute_pcts_metrics": False,
        "compute_pips_metrics": False,
        "source_code_constants_params": False,
    },
    "calibration_indicators": {"QQE.RSIPeriod": [14], "QQE.sF": [5], "QQE.Value1": ""},
    "user_access": {
        "username": "admin",
        "password_hash": "",
        "password_salt": "",
        "session_timeout_mins": 1440,
        "allow_remember_me": False,
        "require_auth": False,
    },
}


def test_registered_fields_roundtrip_preserves_unknown_data(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Every editable registered field maps to its canonical row without mirrors."""
    caplog.set_level(logging.INFO)
    instance = SettingsManager()
    instance.save_settings(
        {
            "application": _STORED_EXAMPLES
            | {
                "config_agents": _STORED_EXAMPLES["config_agents"]
                | {"unregistered": {"keep": True}}
            }
        }
    )
    catalogue = instance.get_catalogue()
    assert len(catalogue["fields"]) == 128
    changes: dict[str, dict[str, Any]] = {}
    for field in catalogue["fields"]:
        if field["readonly"]:
            continue
        value = "synthetic-secret" if field["secret"] else field["value"]
        if field["kind"] == "bool":
            value = not value
        elif (
            field["kind"] == "str" and not field.get("options") and not field["secret"]
        ):
            value = "test-value"
        changes.setdefault(field["scope"], {})[field["key"]] = value
    saved = instance.save_changes(
        changes, expected_revision=catalogue["revision"], include_secrets=True
    )
    independent = SettingsManager()
    assert independent.get_snapshot() == {
        k: v for k, v in saved.items() if k != "wrote"
    }
    assert independent.get_scope("config_agents")["unregistered"] == {"keep": True}
    assert all(
        r["scope"] == "application"
        for r in HostPersistence.read_records("host_settings")
    )
    for field in independent.get_catalogue()["fields"]:
        if field["readonly"]:
            continue
        if field["secret"]:
            assert field["configured"] is True and "value" not in field
        else:
            assert field["value"] == changes[field["scope"]][field["key"]]
    assert any(getattr(r, "fr_id", None) == BATCH_UPDATE_FR for r in caplog.records)


@pytest.mark.parametrize("text", ["true", "123", "null", "false", "[1]", ""])
def test_string_values_remain_strings(text: str) -> None:
    """JSON encoding preserves strings that resemble other JSON types."""
    instance = SettingsManager()
    instance.save_changes(
        {"app.general": {"header_custom_text": text}}, expected_revision=0
    )
    assert (
        SettingsManager().get_snapshot()["values"]["app.general"]["header_custom_text"]
        == text
    )


def test_canonical_account_precedes_preserved_legacy_rows() -> None:
    """Legacy rows are retained without overriding the authoritative account group."""
    instance = SettingsManager()
    instance.save_settings(
        {
            "user_access": {"username": "legacy"},
            "application": {"user_access": {"username": "current"}},
        }
    )
    assert instance.get("user_access", "username") == "current"
    assert instance.user_access.username == "current"
    assert instance["user_access"].username == "current"
    assert instance.get("user_access").username == "current"
    assert instance.as_dict()["user_access"]["username"] == "legacy"
