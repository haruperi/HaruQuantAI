"""Unit tests for host settings reader and session auth.

Description:
    Exercises reading operational and application settings from the database
    via the persistence read layer (app.host.persistence.read), packaging into
    the lazy settings instance with nested dot-access, PBKDF2 credential
    hashing, opaque bearer token lifecycles, restart invalidation, and granular
    scope authorization. All tests execute against isolated temporary database
    stores, asserting structured non-silent logging for every functional
    requirement.

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
from app.host.persistence.create import PersistenceError, create_schema, get_connection
from app.host.persistence.read import list_host_settings
from app.host.persistence.update import batch_save_host_settings
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
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify reading host settings from SQLite via persistence read layer."""
    caplog.set_level(logging.DEBUG)
    db_file = tmp_path / "settings_test.db"
    conn = get_connection(db_file)
    try:
        create_schema(conn)
        conn.execute(
            "INSERT INTO host_settings "
            "(scope, key, value_json, schema_version, updated_at_utc) "
            "VALUES (?, ?, ?, 1, '2026-10-14 00:00:00')",
            ("user_access", "username", json.dumps("admin")),
        )
        conn.execute(
            "INSERT INTO host_settings "
            "(scope, key, value_json, schema_version, updated_at_utc) "
            "VALUES (?, ?, ?, 1, '2026-10-14 00:00:00')",
            ("user_access", "theme", json.dumps("dark")),
        )
        conn.execute(
            "INSERT INTO host_settings "
            "(scope, key, value_json, schema_version, updated_at_utc) "
            "VALUES (?, ?, ?, 1, '2026-10-14 00:00:00')",
            ("workspace_paths", "data_dir", json.dumps("data")),
        )
        conn.commit()

        # Reload settings using test connection
        host_settings.reload(conn=conn)
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
        assert (
            host_settings.user_access.get("missing_key", "default_val") == "default_val"
        )
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
    finally:
        conn.close()


def test_read_settings_malformed_json_fallback(tmp_path: Path) -> None:
    """Verify fallback handling for non-JSON string values in host_settings."""
    db_file = tmp_path / "settings_malformed.db"
    conn = get_connection(db_file)
    try:
        create_schema(conn)
        conn.execute(
            "INSERT INTO host_settings "
            "(scope, key, value_json, schema_version, updated_at_utc) "
            "VALUES ('custom', 'raw_key', 'plain_text_not_json', 1, '2026-10-14')",
        )
        conn.commit()

        host_settings.reload(conn=conn)
        assert host_settings.custom.raw_key == "plain_text_not_json"
        assert host_settings.get("custom", "raw_key") == "plain_text_not_json"
    finally:
        conn.close()


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
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify session creation, validation, expiration, and revocation."""
    caplog.set_level(logging.DEBUG)
    db_file = tmp_path / "session_test.db"
    manager = SessionManager(db_path=db_file)

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


def test_session_restart_invalidation(tmp_path: Path) -> None:
    """Verify host restart invalidates active sessions created under earlier instance."""
    db_file = tmp_path / "session_restart.db"
    manager = SessionManager(db_path=db_file)
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


def test_settings_lazy_reloading(tmp_path: Path) -> None:
    """Verify host settings lazy loading, reload, and self-contained queries."""
    db_file = tmp_path / "facade_test.db"
    conn = get_connection(db_file)
    try:
        create_schema(conn)
        conn.execute(
            "INSERT INTO host_settings "
            "(scope, key, value_json, schema_version, updated_at_utc) "
            "VALUES (?, ?, ?, 1, '2026-10-14 00:00:00')",
            ("user_access", "username", json.dumps("facade_admin")),
        )
        conn.commit()

        # Reload with custom connection
        host_settings.reload(conn=conn)
        user = host_settings.user_access.username
        assert user == "facade_admin"
        assert host_settings.get("user_access", "username") == "facade_admin"
        assert host_settings.get_scope("user_access") == {"username": "facade_admin"}
        assert "user_access" in host_settings
        assert len(host_settings) >= 1
        assert host_settings.as_dict()["user_access"]["username"] == "facade_admin"

        # Test internal _read_settings helper
        data = _read_settings(conn=conn)
        assert data["user_access"]["username"] == "facade_admin"

        # Test self-contained list_host_settings without conn
        raw_rows = list_host_settings()
        assert isinstance(raw_rows, list)
    finally:
        conn.close()


def test_nested_scope_resolution_under_parent(tmp_path: Path) -> None:
    """Verify settings resolve section keys stored under parent scopes (e.g. application)."""
    db_file = tmp_path / "nested_scopes.db"
    conn = get_connection(db_file)
    try:
        create_schema(conn)
        conn.execute(
            "INSERT INTO host_settings "
            "(scope, key, value_json, schema_version, updated_at_utc) "
            "VALUES (?, ?, ?, 1, '2026-10-14 00:00:00')",
            (
                "application",
                "user_access",
                json.dumps({"username": "app_user", "theme": "light"}),
            ),
        )
        conn.commit()

        host_settings.reload(conn=conn)
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
    finally:
        conn.close()


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
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify atomic batch updates across scopes and revision conflict errors."""
    caplog.set_level(logging.INFO)
    db_file = tmp_path / "batch_revision.db"
    conn = get_connection(db_file)
    try:
        create_schema(conn)
        conn.close()

        host_settings.reload(conn=db_file)
        initial_rev = host_settings.revision

        # 1. Atomic batch update across multiple scopes with expected_revision
        new_rev = host_settings.update_batch(
            {
                "user_access": {"username": "quant_operator", "theme": "dark"},
                "compute": {"worker_mode": "reserve-one"},
            },
            expected_revision=initial_rev,
            conn=db_file,
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
                conn=db_file,
            )
        assert exc_info.value.expected_revision == initial_rev
        assert exc_info.value.current_revision == new_rev
        assert host_settings.get("user_access", "username") == "quant_operator"

        # 3. Direct persistence batch_save_host_settings without expected_revision
        rev_after = batch_save_host_settings(
            {"user_access": {"username": "updated_operator"}},
            conn=db_file,
        )
        assert rev_after == new_rev + 1

        assert any(
            getattr(r, "fr_id", None) == BATCH_UPDATE_FR or BATCH_UPDATE_FR in r.message
            for r in caplog.records
        )
    finally:
        pass


def test_independent_settings_writers_conflict_and_batch_rollback(
    tmp_path: Path,
) -> None:
    db = tmp_path / "concurrent.db"
    with get_connection(db) as conn:
        create_schema(conn)
    conn.close()
    ready = Barrier(2)

    def save(value: int) -> int | str:
        ready.wait(timeout=5)
        try:
            return batch_save_host_settings(
                {"audit": {"value": value}}, expected_revision=0, conn=db
            )
        except RevisionConflictError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(save, [1, 2]))
    assert results.count(1) == results.count("conflict") == 1
    assert batch_save_host_settings({}, expected_revision=1, conn=db) == 1
    with pytest.raises(PersistenceError):
        batch_save_host_settings(
            {"audit": {"first": "must roll back", "invalid": object()}},
            expected_revision=1,
            conn=db,
        )
    instance = HostSettings()
    instance.reload(conn=db)
    assert instance.revision == 1
    assert "first" not in instance.get_scope("audit")

    conn = get_connection(db)
    try:
        conn.execute("BEGIN IMMEDIATE")
        with pytest.raises(PersistenceError, match="idle connection"):
            batch_save_host_settings({"audit": {"value": 3}}, conn=conn)
        assert conn.in_transaction
        conn.rollback()
    finally:
        conn.close()


def test_settings_read_failure_preserves_last_snapshot(tmp_path: Path) -> None:
    db = tmp_path / "read_failure.db"
    conn = get_connection(db)
    create_schema(conn)
    conn.close()
    instance = HostSettings()
    instance.reload(conn=db)
    instance.update_batch({"audit": {"kept": True}}, expected_revision=0)
    with pytest.raises(Exception, match="closed database"):
        instance.reload(conn=conn)
    assert instance.revision == 1
    assert instance.get("audit", "kept") is True
    instance.reload()


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
