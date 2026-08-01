"""Integration evidence for UI/API-owned identity and settings state."""

from pathlib import Path

import pytest
from app.services.api import (
    authenticate_api_user,
    build_api_settings,
    create_api_app,
    create_api_session,
    get_user_settings,
    register_api_user,
    resolve_api_credential_reference,
    revoke_api_session,
    run_api_migrations,
    store_api_credential,
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
            permissions=("settings:read", "settings:write"),
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
