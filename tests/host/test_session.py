"""Unit test suite for host session authority, credential hashing, and revocation.

Description:
    Verifies that SessionAuthority implements salted PBKDF2 password hashing,
    ephemeral HMAC bearer token issuance, sliding-window per-peer retry throttling,
    signature and persistence verification, and durable SQLite token revocation.

Purpose:
    FEAT-HOST-SESSION: Operator Authentication, Ephemeral Tokens, and Revocation.
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime
from pathlib import Path

import pytest
from app.host.session import (
    DEFAULT_PBKDF2_ITERATIONS,
    InvalidTokenError,
    RateLimitExceededError,
    SessionAuthority,
    TokenExpiredError,
    TokenRevokedError,
)


def test_schema_initialization_idempotency(tmp_path: Path) -> None:
    """Verify that initialize() creates host_session table and is idempotent."""
    db_file = tmp_path / "test_sessions.db"
    authority = SessionAuthority(db_path=db_file)
    authority.initialize()
    authority.initialize()  # Must not raise on second call

    with authority._connect(query_only=True) as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='host_session'"
        )
        assert cursor.fetchone() is not None


def test_credential_hashing_and_verification(tmp_path: Path) -> None:
    """Verify FR-HOST-SESSION-CREDENTIAL-VERIFICATION hashing and verification."""
    db_file = tmp_path / "test_auth.db"
    authority = SessionAuthority(db_path=db_file)
    authority.initialize()

    # Test fresh hashing
    pw_hash, pw_salt = authority.hash_password("SuperSecretPass123!")
    assert len(pw_hash) == 64
    assert len(pw_salt) == 32

    # Verification success
    assert authority.verify_password(
        "SuperSecretPass123!",
        expected_hash_hex=pw_hash,
        salt_hex=pw_salt,
        peer_id="peer-1",
    )

    # Verification failure on incorrect credential
    assert not authority.verify_password(
        "WrongPassword",
        expected_hash_hex=pw_hash,
        salt_hex=pw_salt,
        peer_id="peer-1",
    )

    # Verification with known baseline (haruquantai credential)
    haru_salt = "fbb1cfea980055086e83ebd09be6e0ee"
    haru_hash = "d4609e5eb3dd800258c5aaaf07cf686e47543749ba9217acb3b59405b34c5b6f"
    assert authority.verify_password(
        "haruquantai",
        expected_hash_hex=haru_hash,
        salt_hex=haru_salt,
        iterations=DEFAULT_PBKDF2_ITERATIONS,
        peer_id="peer-haru",
    )


def test_token_issuance_and_persistence(tmp_path: Path) -> None:
    """Verify FR-HOST-SESSION-TOKEN-ISSUANCE generates signed token in host_session."""
    db_file = tmp_path / "test_tokens.db"
    authority = SessionAuthority(db_path=db_file)
    authority.initialize()

    issued = authority.create_session(
        username="quant_operator",
        peer_id="192.168.1.50",
        ttl_seconds=3600,
    )

    assert issued.token
    parts = issued.token.split(".")
    assert len(parts) == 3
    assert parts[0] == issued.record.session_id

    # Verify database persistence
    with authority._connect(query_only=True) as conn:
        row = conn.execute(
            "SELECT * FROM host_session WHERE session_id = ?",
            (issued.record.session_id,),
        ).fetchone()
        assert row is not None
        assert row["username"] == "quant_operator"
        assert row["peer_id"] == "192.168.1.50"
        assert row["status"] == "ACTIVE"
        assert row["token_hash"] == hashlib.sha256(issued.token.encode()).hexdigest()
        assert row["revoked_at_utc"] is None


def test_sliding_window_rate_limiting(tmp_path: Path) -> None:
    """Verify FR-HOST-SESSION-RATE-LIMITING throttles retries per peer."""
    db_file = tmp_path / "test_rate_limit.db"
    authority = SessionAuthority(
        db_path=db_file,
        rate_limit_attempts=3,
        rate_limit_window_seconds=1.0,
    )
    authority.initialize()

    peer = "attacker_ip"
    _, salt = authority.hash_password("correct_pass")
    fake_hash = "0" * 64

    # 1st and 2nd failed attempts
    assert not authority.verify_password(
        "bad1", expected_hash_hex=fake_hash, salt_hex=salt, peer_id=peer
    )
    assert authority.check_rate_limit(peer)

    assert not authority.verify_password(
        "bad2", expected_hash_hex=fake_hash, salt_hex=salt, peer_id=peer
    )
    assert authority.check_rate_limit(peer)

    # 3rd failed attempt hits the limit
    assert not authority.verify_password(
        "bad3", expected_hash_hex=fake_hash, salt_hex=salt, peer_id=peer
    )
    assert not authority.check_rate_limit(peer)

    # Further attempt is rejected by rate limiter
    assert not authority.verify_password(
        "bad4", expected_hash_hex=fake_hash, salt_hex=salt, peer_id=peer
    )

    # Creating session when rate limited raises RateLimitExceededError
    with pytest.raises(RateLimitExceededError):
        authority.create_session(username="victim", peer_id=peer)

    # Wait for sliding window to elapse
    time.sleep(1.05)
    assert authority.check_rate_limit(peer)


def test_token_verification_lifecycle(tmp_path: Path) -> None:
    """Verify FR-HOST-SESSION-TOKEN-VERIFICATION handles valid and invalid tokens."""
    db_file = tmp_path / "test_verify.db"
    authority = SessionAuthority(db_path=db_file)
    authority.initialize()

    issued = authority.create_session(username="alice", peer_id="10.0.0.1")

    # Valid token verification
    verified = authority.verify_token(issued.token)
    assert verified.session_id == issued.record.session_id
    assert verified.username == "alice"
    assert verified.status == "ACTIVE"

    # Malformed token structure
    with pytest.raises(InvalidTokenError, match="Malformed bearer token"):
        authority.verify_token("invalid.token")

    # Tampered signature
    parts = issued.token.split(".")
    tampered_sig_token = f"{parts[0]}.{parts[1]}.tampered_signature"
    with pytest.raises(InvalidTokenError, match="signature"):
        authority.verify_token(tampered_sig_token)

    # Tampered payload
    tampered_payload_token = f"{parts[0]}.fake_payload.{parts[2]}"
    with pytest.raises(InvalidTokenError):
        authority.verify_token(tampered_payload_token)

    # Unrecorded token with valid signature from another authority
    other_authority = SessionAuthority(db_path=tmp_path / "other.db")
    other_authority.initialize()
    other_token = other_authority.create_session(username="bob")
    with pytest.raises(InvalidTokenError):
        authority.verify_token(other_token.token)


def test_token_expiration_handling(tmp_path: Path) -> None:
    """Verify that expired tokens are rejected and marked EXPIRED."""
    db_file = tmp_path / "test_expiry.db"
    authority = SessionAuthority(db_path=db_file)
    authority.initialize()

    # Create session with -10 second TTL (already expired)
    issued = authority.create_session(
        username="charlie", peer_id="local", ttl_seconds=-10
    )

    with pytest.raises(TokenExpiredError, match="expired"):
        authority.verify_token(issued.token)

    # Check status in database updated to EXPIRED
    with authority._connect(query_only=True) as conn:
        row = conn.execute(
            "SELECT status FROM host_session WHERE session_id = ?",
            (issued.record.session_id,),
        ).fetchone()
        assert row is not None
        assert row["status"] == "EXPIRED"


def test_durable_revocation_by_session_id_and_token(tmp_path: Path) -> None:
    """Verify FR-HOST-SESSION-DURABLE-REVOCATION immediately revokes active sessions."""
    db_file = tmp_path / "test_revoke.db"
    authority = SessionAuthority(db_path=db_file)
    authority.initialize()

    # Revoke by session_id
    issued_1 = authority.create_session(username="user1", peer_id="client1")
    assert authority.revoke_session(issued_1.record.session_id)
    # Subsequent revocation attempt returns False (already revoked)
    assert not authority.revoke_session(issued_1.record.session_id)

    with pytest.raises(TokenRevokedError, match="revoked"):
        authority.verify_token(issued_1.token)

    # Revoke by raw token
    issued_2 = authority.create_session(username="user2", peer_id="client2")
    assert authority.revoke_token(issued_2.token)
    assert not authority.revoke_token(issued_2.token)

    with pytest.raises(TokenRevokedError, match="revoked"):
        authority.verify_token(issued_2.token)

    # Check database rows have revoked_at_utc populated
    with authority._connect(query_only=True) as conn:
        rows = conn.execute(
            "SELECT session_id, status, revoked_at_utc FROM host_session"
        ).fetchall()
        assert len(rows) == 2
        for r in rows:
            assert r["status"] == "REVOKED"
            assert r["revoked_at_utc"] is not None
            # Verify valid ISO format timestamp
            datetime.fromisoformat(r["revoked_at_utc"])
