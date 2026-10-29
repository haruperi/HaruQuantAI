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
