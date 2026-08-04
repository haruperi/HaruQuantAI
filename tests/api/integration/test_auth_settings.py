"""Integration evidence for UI/API-owned identity and settings state."""

import sqlite3
from pathlib import Path

import pytest
from app.services.api import (
    authenticate_api_user,
    build_api_settings,
    create_api_app,
    create_api_session,
    get_system_settings,
    get_user_settings,
    register_api_user,
    resolve_api_credential_reference,
    revoke_api_session,
    run_api_migrations,
    store_api_credential,
    update_system_settings,
    update_user_settings,
    validate_api_csrf,
    validate_api_session,
)
from app.services.data import build_data_settings, data_settings_context
from app.utils import generate_id
from fastapi.testclient import TestClient
from pydantic import SecretStr


def test_login_settings_credentials_logout(tmp_path: Path) -> None:
    """Persist identity state without fallback users or plaintext credentials."""
    settings = build_data_settings(
        database_url="sqlite:///api-integration.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )
    key = b"k" * 32
    with data_settings_context(settings):
        migration = run_api_migrations(generate_id("req"))
        assert migration.status == "success"
        registered = register_api_user(
            username="api-integration-user",
            password="bounded integration password",  # pragma: allowlist secret
            permissions=("settings:admin", "settings:read", "settings:write"),
            request_id=generate_id("req"),
            tenant_or_environment="development",
            runtime_profile="simulation",
        )
        authenticated = authenticate_api_user(
            username="api-integration-user",
            password="bounded integration password",  # pragma: allowlist secret
            request_id=generate_id("req"),
        )
        assert authenticated.user_id == registered.user_id
        assert authenticated.tenant_or_environment == "development"
        assert authenticated.runtime_profile == "simulation"
        assert authenticated.roles == ("user",)
        assert authenticated.permissions == (
            "settings:admin",
            "settings:read",
            "settings:write",
        )
        with sqlite3.connect(tmp_path / "api-integration.db") as connection:
            compatibility_claims = connection.execute(
                "SELECT roles_json, permissions_json, scopes_json "
                "FROM api_accounts WHERE user_id = ?",
                (registered.user_id,),
            ).fetchone()
            role_binding = connection.execute(
                "SELECT role.role_name, permission.permission_key "
                "FROM api_role_bindings AS binding "
                "JOIN api_roles AS role ON role.role_id = binding.role_id "
                "JOIN api_role_permissions AS role_permission "
                "ON role_permission.role_id = role.role_id "
                "JOIN api_permissions AS permission "
                "ON permission.permission_id = role_permission.permission_id "
                "WHERE binding.account_id = ? ORDER BY permission.permission_key",
                (registered.user_id,),
            ).fetchall()
        assert compatibility_claims == ("[]", "[]", "[]")
        assert role_binding == [
            ("user", "settings:admin"),
            ("user", "settings:read"),
            ("user", "settings:write"),
        ]
        with pytest.raises(RuntimeError, match="ACCOUNT_REGISTRATION_FAILED"):
            register_api_user(
                username="conflicting-role-user",
                password="bounded conflicting password",  # pragma: allowlist secret
                permissions=("settings:read",),
                request_id=generate_id("req"),
            )
        session = create_api_session(
            authenticated,
            request_id=generate_id("req"),
            ttl_seconds=60,
        )
        restored = validate_api_session(
            session.session_token,
            request_id=generate_id("req"),
        )
        assert restored.user_id == registered.user_id
        assert restored.tenant_or_environment == "development"
        assert restored.runtime_profile == "simulation"
        validate_api_csrf(
            session.session_token,
            session.csrf_token,
            request_id=generate_id("req"),
        )
        initial = get_user_settings(
            registered.user_id,
            request_id=generate_id("req"),
        )
        updated = update_user_settings(
            registered.user_id,
            {"theme": "dark"},
            expected_version=initial.version,
            request_id=generate_id("req"),
        )
        assert updated.settings == {"theme": "dark"}
        assert updated.scope == "user"
        system_initial = get_system_settings(request_id=generate_id("req"))
        system_updated = update_system_settings(
            {"theme": "light"},
            actor_id=registered.user_id,
            expected_version=system_initial.version,
            request_id=generate_id("req"),
        )
        assert system_updated.scope == "system"
        assert system_updated.subject_id == "global"
        assert system_updated.settings == {"theme": "light"}
        with pytest.raises(ValueError, match="unsafe or oversized"):
            update_system_settings(
                {"api_key": "forbidden"},  # pragma: allowlist secret
                actor_id=registered.user_id,
                expected_version=system_updated.version,
                request_id=generate_id("req"),
            )
        with pytest.raises(RuntimeError, match="SETTINGS_VERSION_CONFLICT"):
            update_system_settings(
                {"theme": "dark"},
                actor_id=registered.user_id,
                expected_version=0,
                request_id=generate_id("req"),
            )
        with sqlite3.connect(tmp_path / "api-integration.db") as connection:
            setting_scopes = connection.execute(
                "SELECT scope, subject_id FROM api_settings ORDER BY scope"
            ).fetchall()
            legacy_table = connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name = 'api_user_settings'"
            ).fetchone()
        assert setting_scopes == [
            ("system", "global"),
            ("user", registered.user_id),
        ]
        assert legacy_table is None
        record = store_api_credential(
            owner_id=registered.user_id,
            label="paper-broker",
            material={"api_key": SecretStr("test-only-value")},
            key_set={"active": key},
            active_key_id="active",
            request_id=generate_id("req"),
        )
        resolved = resolve_api_credential_reference(
            record.reference,
            owner_id=registered.user_id,
            key_set={"active": key},
            request_id=generate_id("req"),
        )
        assert resolved["api_key"].get_secret_value() == "test-only-value"
        revoke_api_session(
            session.session_token,
            request_id=generate_id("req"),
        )


def test_repeated_invalid_login_is_rate_limited(tmp_path: Path) -> None:
    """Bound repeated invalid credentials without a fallback identity."""
    settings = build_data_settings(
        database_url="sqlite:///api-rate-limit.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )
    with data_settings_context(settings):
        assert run_api_migrations(generate_id("req")).status == "success"
        register_api_user(
            username="rate-limited-user",
            password="correct bounded password",  # pragma: allowlist secret
            request_id=generate_id("req"),
        )
        for _ in range(5):
            with pytest.raises(RuntimeError, match="AUTHENTICATION_REQUIRED"):
                authenticate_api_user(
                    username="rate-limited-user",
                    password="incorrect bounded password",  # pragma: allowlist secret
                    request_id=generate_id("req"),
                )
        with pytest.raises(RuntimeError, match="RATE_LIMITED"):
            authenticate_api_user(
                username="rate-limited-user",
                password="correct bounded password",  # pragma: allowlist secret
                request_id=generate_id("req"),
            )


def test_http_session_cookies_and_csrf_logout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Preserve browser cookies while enveloping authentication responses."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///api-http-identity.db")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1.0")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "10.0")
    app = create_api_app(build_api_settings())
    with TestClient(app) as client:
        registered = client.post(
            "/api/v1/auth/register",
            json={
                "username": "http-identity-user",
                "password": "bounded http password",  # pragma: allowlist secret
            },
        )
        assert registered.status_code == 201
        assert registered.json()["status"] == "success"
        assert client.cookies.get("hq_session")
        csrf_token = client.cookies.get("hq_csrf")
        assert csrf_token

        recovered = client.get("/api/v1/auth/me")
        assert recovered.status_code == 200
        assert recovered.json()["data"]["username"] == "http-identity-user"
        assert "session_token" not in str(recovered.json())

        missing_csrf = client.post("/api/v1/auth/logout")
        assert missing_csrf.status_code == 403
        assert missing_csrf.json()["error"]["code"] == "CSRF_REQUIRED"

        logged_out = client.post(
            "/api/v1/auth/logout",
            headers={"X-CSRF-Token": csrf_token},
        )
        assert logged_out.status_code == 204
        assert logged_out.content == b""
        assert client.cookies.get("hq_session") is None

        missing_session = client.get("/api/v1/auth/me")
        assert missing_session.status_code == 401


def test_system_settings_route_requires_admin_permission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep global settings inaccessible to ordinary settings readers."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///api-system-settings.db")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1.0")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "10.0")
    app = create_api_app(build_api_settings())
    with TestClient(app) as client:
        admin = register_api_user(
            username="settings-admin",
            password="bounded admin password",  # pragma: allowlist secret
            roles=("admin",),
            permissions=("settings:admin",),
            request_id=generate_id("req"),
        )
        reader = register_api_user(
            username="settings-reader",
            password="bounded reader password",  # pragma: allowlist secret
            roles=("reader",),
            permissions=("settings:read",),
            request_id=generate_id("req"),
        )
        admin_session = create_api_session(
            admin,
            request_id=generate_id("req"),
            ttl_seconds=60,
        )
        reader_session = create_api_session(
            reader,
            request_id=generate_id("req"),
            ttl_seconds=60,
        )

        denied = client.get(
            "/api/v1/settings?scope=system",
            headers={"Authorization": f"Bearer {reader_session.session_token}"},
        )
        assert denied.status_code == 403
        assert denied.json()["error"]["code"] == "AUTHORIZATION_DENIED"

        updated = client.put(
            "/api/v1/settings",
            headers={
                "Authorization": f"Bearer {admin_session.session_token}",
                "Idempotency-Key": "system-settings-update-1",
            },
            json={
                "scope": "system",
                "settings": {"theme": "light"},
                "expected_version": 0,
            },
        )
        assert updated.status_code == 200
        assert updated.json()["data"]["scope"] == "system"

        read = client.get(
            "/api/v1/settings?scope=system",
            headers={"Authorization": f"Bearer {admin_session.session_token}"},
        )
        assert read.status_code == 200
        assert read.json()["data"]["settings"] == {"theme": "light"}
