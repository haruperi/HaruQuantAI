"""Security and persistence checks for the host session authority."""

import hashlib
import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest
from app.core.host.persistence import HostPersistence
from app.core.host.session import SessionManager, SessionPersistenceError


@pytest.fixture
def authority(tmp_path):
    """Use the production session schema with an adjustable UTC clock."""
    path = tmp_path / "sessions.db"
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("""
            CREATE TABLE host_session (
                session_id TEXT PRIMARY KEY, token_hash TEXT NOT NULL UNIQUE,
                username TEXT NOT NULL, peer_id TEXT NOT NULL,
                created_at_utc TEXT NOT NULL, expires_at_utc TEXT NOT NULL,
                revoked_at_utc TEXT, status TEXT NOT NULL
            )
        """)
    clock = [datetime(2026, 10, 25, tzinfo=UTC)]
    persistence = HostPersistence(path)
    return SessionManager(persistence, clock=lambda: clock[0]), clock


def test_password_hashing_and_credentials():
    first = SessionManager.hash_password("secret")
    second = SessionManager.hash_password("secret")
    assert first != second
    assert SessionManager.verify_password("secret", first)
    assert not SessionManager.verify_password("incorrect", first)
    assert not SessionManager.verify_password("secret", "pbkdf2_sha256$999999999$a$b")
    assert not SessionManager.verify_password("secret", first[:-1] + "z")
    assert SessionManager.verify_credentials(
        "alice", "secret", expected_username="alice", password_hash=first
    )
    assert not SessionManager.verify_credentials(
        "bob", "secret", expected_username="alice", password_hash=first
    )


def test_legacy_password_hash_uses_text_salt_and_original_iterations():
    salt = "0123456789abcdef0123456789abcdef"
    digest = hashlib.pbkdf2_hmac("sha256", b"legacy-password", salt.encode(), 100_000)
    encoded = f"{salt}${digest.hex()}"
    assert SessionManager.verify_password("legacy-password", encoded)
    assert not SessionManager.verify_password("wrong", encoded)
    assert SessionManager.verify_credentials(
        "alice", "legacy-password", expected_username="alice", password_hash=encoded
    )
    assert not SessionManager.verify_password(
        "legacy-password", f"{'z' * 32}${digest.hex()}"
    )
    assert not SessionManager.verify_password("legacy-password", f"{salt}$short")
    assert SessionManager.hash_password("legacy-password").startswith(
        "pbkdf2_sha256$600000$"
    )


def test_digest_browser_binding_sliding_expiry_and_restart(authority):
    manager, clock = authority
    token = manager.create_session("alice", "browser")
    assert len(token) == 64
    row = manager.persistence.read_records("host_session")["data"]["records"][0]
    assert row["token_hash"] == hashlib.sha256(token.encode()).hexdigest()
    assert token not in str(row)
    assert manager.validate_session(token, "different-browser") is None
    clock[0] += timedelta(hours=23)
    restarted = SessionManager(manager.persistence, clock=lambda: clock[0])
    session = restarted.validate_session(token, "browser")
    assert session.expires_at_utc == clock[0] + timedelta(hours=24)
    clock[0] += timedelta(hours=24)
    assert restarted.validate_session(token, "browser") is None
    assert (
        manager.persistence.read_records("host_session")["data"]["records"][0]["status"]
        == "expired"
    )


def test_logout_is_persistent_and_idempotent(authority):
    manager, _ = authority
    token = manager.create_session("alice", "browser")
    assert not manager.revoke_session(token, "other")
    assert manager.revoke_session(token, "browser")
    assert manager.revoke_session(token, "browser")
    assert (
        SessionManager(manager.persistence).validate_session(token, "browser") is None
    )
    assert manager.validate_session("invalid", "browser") is None
    assert not manager.revoke_session("invalid", "browser")


@pytest.mark.parametrize(
    ("grants", "required", "expected"),
    [
        (["orders:read"], "orders:read", True),
        (["orders:*"], "orders:write", True),
        (["*:read"], "settings:read", True),
        (["*:*"], "orders:write", True),
        (["orders:read"], "orders:write", False),
        (["order*:read"], "orders:read", False),
        (["*:*"], "orders:*", False),
        ([], "orders:read", False),
        ("orders:read", "orders:read", False),
    ],
)
def test_scope_matching(grants, required, expected):
    assert SessionManager.has_scope(grants, required) is expected


def test_authorization_refreshes_trusted_grants(authority):
    manager, clock = authority
    grants = ["orders:read"]
    manager = SessionManager(
        manager.persistence, scope_resolver=lambda _: grants, clock=lambda: clock[0]
    )
    token = manager.create_session("alice", "browser")
    assert manager.authorize(token, "browser", "orders:read")
    grants.clear()
    assert not manager.authorize(token, "browser", "orders:read")
    assert not manager.authorize(token, "other", "orders:read")


def test_storage_failure_does_not_issue_token(authority):
    manager, _ = authority
    with closing(sqlite3.connect(manager.persistence.database_path)) as connection:
        connection.execute("DROP TABLE host_session")
    with pytest.raises(SessionPersistenceError):
        manager.create_session("alice", "browser")


def test_lifecycle_logging_excludes_secrets(authority, monkeypatch):
    manager, clock = authority
    log = Mock()
    monkeypatch.setattr("app.core.host.session.logger", log)
    password_hash = manager.hash_password("private-password")
    assert manager.verify_credentials(
        "private-user",
        "private-password",
        expected_username="private-user",
        password_hash=password_hash,
    )
    token = manager.create_session("private-user", "private-browser")
    assert manager.validate_session(token, "private-browser") is not None
    assert not manager.authorize(token, "private-browser", "orders:write")
    assert manager.revoke_session(token, "private-browser")
    assert manager.validate_session(token, "private-browser") is None
    expired_token = manager.create_session("private-user", "private-browser")
    clock[0] += timedelta(hours=24)
    assert manager.validate_session(expired_token, "private-browser") is None
    calls = str(log.mock_calls)
    for event in (
        "Session created",
        "Session revoked",
        "Session expiration detected",
        "Session validated",
        "Authorization denied",
        "Credential verification",
    ):
        assert event in calls
    for secret in (
        token,
        expired_token,
        hashlib.sha256(token.encode()).hexdigest(),
        password_hash,
        "private-password",
        "private-user",
        "private-browser",
    ):
        assert secret not in calls


def test_resolve_peer(authority):
    manager, _ = authority
    token = manager.create_session("alice", "ui:browser123")
    assert manager.resolve_peer(token) == "ui:browser123"
    assert manager.resolve_peer("invalid") is None
    assert manager.resolve_peer("a" * 64) is None
    manager.revoke_session(token, "ui:browser123")
    assert manager.resolve_peer(token) is None


def test_foreign_reference_cannot_be_resolved_or_revoked():
    from app.core.host.session import WindowsCredentialVault

    vault = WindowsCredentialVault()
    with pytest.raises(OSError, match="unavailable"):
        vault.resolve("another-application/credential")
    with pytest.raises(OSError, match="unavailable"):
        vault.revoke("another-application/credential")


def test_unavailable_vault_never_falls_back_to_plaintext():
    from app.core.host.session import WindowsCredentialVault

    vault = WindowsCredentialVault()
    vault._api = None
    with pytest.raises(OSError, match="unavailable"):
        vault.store("non-production-test-value")
    with pytest.raises(OSError, match="unavailable"):
        vault.resolve("HaruQuantAI/test")
    with pytest.raises(OSError, match="unavailable"):
        vault.revoke("HaruQuantAI/test")


def test_windows_credential_vault_store_resolve_revoke():
    from app.core.host.session import WindowsCredentialVault

    vault = WindowsCredentialVault()
    if not vault._api:
        pytest.skip("Windows Credential API not available on this platform")

    # Invalid secret values
    with pytest.raises(ValueError, match="Supply a nonempty credential"):
        vault.store("")
    with pytest.raises(ValueError, match="Supply a nonempty credential"):
        vault.store("x" * 2500)

    # Valid secret lifecycle
    ref = vault.store("unit_test_password_value")
    try:
        assert ref.startswith("HaruQuantAI/")
        resolved = vault.resolve(ref)
        assert resolved == "unit_test_password_value"
    finally:
        vault.revoke(ref)

    # Idempotent revocation on already deleted reference
    vault.revoke(ref)

    # Resolving after revocation must raise
    with pytest.raises(OSError, match="unavailable"):
        vault.resolve(ref)


def test_prepare_credentials_staging_and_rollback():
    from app.core.host.session import prepare_credentials
    from app.core.host.transport import TransportError

    vault = Mock()
    vault.store.side_effect = lambda s: f"HaruQuantAI/{s}"

    # Normal staging
    values = {
        "name": "Live MT5",
        "provider": "mt5",
        "endpoint": "http://127.0.0.1:8000",
        "credentials": {"password": "test_pass"},
    }
    record, staged = prepare_credentials(vault, values)
    assert staged == ["HaruQuantAI/test_pass"]
    assert record.vault_refs["password"] == "HaruQuantAI/test_pass"
    vault.resolve.assert_called_once_with("HaruQuantAI/test_pass")

    # Empty secret removes reference
    values2 = {
        "name": "Live MT5",
        "provider": "mt5",
        "endpoint": "http://127.0.0.1:8000",
        "vault_refs": {"password": "old_ref"},
        "credentials": {"password": ""},
    }
    record2, staged2 = prepare_credentials(vault, values2)
    assert "password" not in record2.vault_refs

    # Non-string credentials reject
    with pytest.raises(ValueError, match=r"Credentials must contain string fields"):
        prepare_credentials(vault, {"credentials": {"password": 12345}})

    # Missing vault when credentials provided
    with pytest.raises(TransportError):
        prepare_credentials(
            None,
            {
                "name": "Live MT5",
                "provider": "mt5",
                "endpoint": "http://127.0.0.1:8000",
                "credentials": {"password": "pass"},
            },
        )

    # Rollback on validation failure
    vault_rb = Mock()
    vault_rb.store.return_value = "HaruQuantAI/staged_to_revoke"
    bad_values = {
        "name": "Live MT5",
        "provider": "mt5",
        "endpoint": "ftp://bad-scheme.local",
        "credentials": {"key": "secret"},
    }
    with pytest.raises(ValueError, match="Invalid endpoint URL"):
        prepare_credentials(vault_rb, bad_values)
    vault_rb.revoke.assert_called_once_with("HaruQuantAI/staged_to_revoke")


def test_endpoint_url_validation():
    from app.core.host.session import _endpoint

    assert _endpoint("http://localhost:8000") == ("localhost", 8000)
    assert _endpoint("https://example.com") == ("example.com", 443)
    assert _endpoint("http://127.0.0.1") == ("127.0.0.1", 80)

    for invalid in (
        "ftp://example.com",
        "http://user:pass@example.com",
        "http://example.com?query=true",
        "http://example.com#fragment",
        "http://",
        "not-a-url",
    ):
        with pytest.raises(ValueError, match="Invalid endpoint URL"):
            _endpoint(invalid)


def test_session_manager_edge_cases(authority):
    from app.core.host.session import _identity

    manager, clock = authority

    with pytest.raises(ValueError, match="A non-empty identity is required"):
        _identity("")
    with pytest.raises(ValueError, match="A non-empty identity is required"):
        _identity("   ")

    assert not manager.verify_password(12345, "some_hash")
    assert not manager.verify_password("password", 12345)
    assert not manager.verify_password(
        "password", "pbkdf2_sha256$not_an_int$salt$digest"
    )

    # Scope validation
    assert not manager.has_scope(["settings:read"], "invalid-scope-no-colon")
    assert not manager.has_scope("not-an-iterable-grants", "settings:read")
    assert not manager.has_scope(["settings:read"], "settings:*")

    # Naive clock raises
    naive_manager = SessionManager(
        manager.persistence,
        clock=lambda: datetime(2026, 1, 1, tzinfo=None),  # noqa: DTZ001
    )
    with pytest.raises(
        ValueError, match="Session clock must return an aware UTC timestamp"
    ):
        naive_manager.create_session("alice", "cli")

    # Token and peer resolution
    assert manager.resolve_peer("not-a-token") is None
    assert not manager.revoke_session("not-a-token", "cli")
    assert not manager.revoke_session("0" * 64, "")
