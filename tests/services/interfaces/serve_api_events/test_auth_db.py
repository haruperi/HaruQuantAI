"""Unit tests for the SQLite-backed auth and session persistence helper."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from app.services.interfaces.serve_api_events._auth_db import (
    get_session_identity,
    hash_password,
    login_user,
    logout_session,
    register_user,
    verify_password,
)


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Create a temporary SQLite database initialized with users and sessions tables."""
    db_file = tmp_path / "test_auth.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE users (
            user_id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            roles_json TEXT NOT NULL,
            permissions_json TEXT NOT NULL,
            environment TEXT NOT NULL,
            active INTEGER NOT NULL CHECK (active IN (0, 1)),
            verified INTEGER NOT NULL CHECK (verified IN (0, 1)),
            created_at TEXT NOT NULL,
            last_login_at TEXT,
            runtime_profile TEXT NOT NULL DEFAULT 'research' CHECK (
                runtime_profile IN ('research', 'simulation', 'demo', 'live')
            )
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE sessions (
            session_digest TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            csrf_digest TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            revoked_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        """
    )
    conn.commit()
    conn.close()
    return db_file


def test_password_hashing_and_verification() -> None:
    """Verify standard scrypt hashing and verification."""
    raw = "MySecretPassword123!"  # pragma: allowlist secret
    hashed = hash_password(raw)
    assert hashed.startswith("scrypt$16384$8$1$")
    assert verify_password(raw, hashed) is True
    assert verify_password("wrong", hashed) is False  # pragma: allowlist secret
    assert verify_password("", hashed) is False
    assert verify_password(raw, "disabled") is False
    assert verify_password(raw, "invalid_hash_format") is False

    with pytest.raises(ValueError, match="Password must not be empty"):
        hash_password("")


def test_register_and_login_flow(temp_db: Path) -> None:
    """Verify registering a user, creating session, and logging in."""
    user, sess_tok, csrf_tok = register_user(
        "alice_quant",
        "P@ssword123",  # pragma: allowlist secret
        runtime_profile="simulation",
        db_path=temp_db,
    )
    assert user["username"] == "alice_quant"
    assert user["runtime_profile"] == "simulation"
    assert len(sess_tok) > 20
    assert len(csrf_tok) > 20

    # Test identity recovery
    identity = get_session_identity(sess_tok, db_path=temp_db)
    assert identity is not None
    assert identity["username"] == "alice_quant"
    assert identity["runtime_profile"] == "simulation"

    # Duplicate registration fails
    with pytest.raises(ValueError, match="already taken"):
        register_user(
            "ALICE_QUANT",
            "P@ssword123",  # pragma: allowlist secret
            db_path=temp_db,
        )

    # Login succeeds
    logged_in, new_sess, _ = login_user(
        "alice_quant",
        "P@ssword123",  # pragma: allowlist secret
        db_path=temp_db,
    )
    assert logged_in["username"] == "alice_quant"
    assert new_sess != sess_tok

    # Bad login fails
    with pytest.raises(ValueError, match="Invalid username or password"):
        login_user(
            "alice_quant",
            "WrongPassword",  # pragma: allowlist secret
            db_path=temp_db,
        )


def test_registration_validation(temp_db: Path) -> None:
    """Verify username and password validation constraints."""
    with pytest.raises(ValueError, match="Username must be 3-64"):
        register_user(
            "a",
            "ValidPass123",  # pragma: allowlist secret
            db_path=temp_db,
        )

    with pytest.raises(ValueError, match="Username must be 3-64"):
        register_user(
            "bad username with spaces",
            "ValidPass123",  # pragma: allowlist secret
            db_path=temp_db,
        )

    with pytest.raises(ValueError, match="Password must be at least 6 characters"):
        register_user("valid_user", "12345", db_path=temp_db)


def test_session_lifecycle_and_revocation(temp_db: Path) -> None:
    """Verify session expiration and explicit logout revocation."""
    _, sess_tok, _ = register_user(
        "bob_trader",
        "SecurePassword123",  # pragma: allowlist secret
        db_path=temp_db,
    )
    assert get_session_identity(sess_tok, db_path=temp_db) is not None

    # Revoke session
    logout_session(sess_tok, db_path=temp_db)
    assert get_session_identity(sess_tok, db_path=temp_db) is None

    # Nonexistent token
    assert get_session_identity(uuid4().hex, db_path=temp_db) is None
    assert get_session_identity(None, db_path=temp_db) is None
