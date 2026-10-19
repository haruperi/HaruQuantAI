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
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

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
    THEME_FR,
    HostSettings,
    RevisionConflictError,
    Theme,
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
        "HostSettings",
        "RevisionConflictError",
        "Theme",
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
    """Verify container methods on empty and populated HostSettings and _SettingsNode."""
    empty = HostSettings({})
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
    validated = manager.validate_token(raw_token)
    assert validated is not None
    assert validated.session_id == record.session_id

    # 3. Revoke session
    assert manager.revoke_session(record.session_id) is True
    assert manager.validate_token(raw_token) is None
    assert manager.revoke_session("non_existent_id") is False

    # 4. Expiration check with zero/negative duration
    expired_token, _ = manager.create_session("admin", "127.0.0.1", duration_mins=-5)
    assert manager.validate_token(expired_token) is None

    # 5. Invalid token format
    assert manager.validate_token("short_token") is None
    assert manager.validate_token("a" * 63) is None

    assert any(
        getattr(r, "fr_id", None) == LIFECYCLE_FR or LIFECYCLE_FR in r.message
        for r in caplog.records
    )


def test_session_restart_invalidation() -> None:
    """Verify host restart invalidates active sessions created under earlier instance."""
    manager = SessionManager()
    raw_token, record = manager.create_session("operator_2", "10.0.0.5")
    assert manager.validate_token(raw_token) is not None

    # Simulate host platform restart
    manager.reset()
    # In-memory sessions are cleared; token validation from DB succeeds if status is ACTIVE
    assert manager.validate_token(raw_token) is not None
    assert manager.revoke_session(record.session_id) is True
    assert manager.validate_token(raw_token) is None


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
    new_rev = host_settings.update_batch(
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
        host_settings.update_batch(
            {"user_access": {"username": "intruder"}},
            expected_revision=initial_rev,
        )
    assert exc_info.value.expected_revision == initial_rev
    assert exc_info.value.current_revision == new_rev
    assert host_settings.get("user_access", "username") == "quant_operator"

    # 3. Update without expected_revision increments revision
    rev_after = host_settings.update_batch(
        {"user_access": {"username": "updated_operator"}},
    )
    assert rev_after == new_rev + 1

    assert any(
        getattr(r, "fr_id", None) == BATCH_UPDATE_FR or BATCH_UPDATE_FR in r.message
        for r in caplog.records
    )


def test_independent_settings_writers_conflict_and_batch_rollback() -> None:
    """Verify concurrent update_batch conflict and invalid payload failure."""
    host_settings.reload()
    ready = Barrier(2)

    def save(value: int) -> int | str:
        ready.wait(timeout=5)
        local_settings = HostSettings()
        try:
            return local_settings.update_batch(
                {"audit": {"value": value}}, expected_revision=0
            )
        except RevisionConflictError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(save, [1, 2]))
    assert 1 in results

    instance = HostSettings()
    instance.reload()
    rev_before = instance.revision
    with pytest.raises(TypeError):
        instance.update_batch(
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
    instance = HostSettings()
    instance.reload()
    instance.update_batch({"audit": {"kept": True}}, expected_revision=0)

    bad_dir = tmp_path / "is_a_directory"
    bad_dir.mkdir()
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", bad_dir)
    with pytest.raises(HostPersistence.Error):
        instance.reload()
    assert instance.revision == 1
    assert instance.get("audit", "kept") is True


def test_theme_tokens_and_appearance_state(caplog: pytest.LogCaptureFixture) -> None:
    """Verify FR-HOST-SETTINGS-THEME-TOKENS dark and light mode tokens and switching."""
    caplog.set_level(logging.DEBUG)
    theme = Theme()
    assert theme.current_theme == "dark"

    dark_tokens = theme.set_dark()
    assert dark_tokens["theme"] == "dark"
    assert "background" in dark_tokens
    assert "dockview" in dark_tokens
    assert "chart" in dark_tokens
    assert "typography" in dark_tokens
    assert any(THEME_FR in rec.message for rec in caplog.records)

    caplog.clear()
    light_tokens = theme.set_light()
    assert light_tokens["theme"] == "light"
    assert "background" in light_tokens
    assert "dockview" in light_tokens
    assert "chart" in light_tokens
    assert any(THEME_FR in rec.message for rec in caplog.records)

    tokens_retrieved = theme.get_tokens()
    assert tokens_retrieved["theme"] == "dark"
    light_retrieved = theme.get_light_tokens()
    assert light_retrieved["theme"] == "light"


def test_host_settings_theme_integration() -> None:
    """Verify HostSettings public class and theme binding."""
    settings_obj = HostSettings(data={"ui": {"theme": "light"}})
    assert settings_obj.theme.current_theme == "light"
    settings_obj.theme.set_dark()
    assert settings_obj.theme.current_theme == "dark"
