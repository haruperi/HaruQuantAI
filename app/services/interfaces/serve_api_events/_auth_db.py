"""Database-backed authentication and session persistence for D-IFACE.

Interacts directly with the SQLite database at data/database/haruquantai.db
using the 'users' and 'sessions' tables.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Final

_DEFAULT_DB_PATH: Final[Path] = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "data"
    / "database"
    / "haruquantai.db"
)

_ALGORITHM: Final = "scrypt"
_N: Final = 2**14
_R: Final = 8
_P: Final = 1
_SALT_BYTES: Final = 16
_KEY_BYTES: Final = 32
_MAX_MEMORY_BYTES: Final = 64 * 1024 * 1024
_SESSION_TTL_DAYS: Final = 7
_MIN_PASSWORD_LEN: Final = 6
_EXPECTED_HASH_PARTS: Final = 6
_USERNAME_PATTERN: Final = re.compile(r"^[a-zA-Z0-9_\-\.]{3,64}$")


def _resolve_db_path(db_path: Path | str | None) -> Path:
    if db_path is None:
        return _DEFAULT_DB_PATH
    return Path(db_path)


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    target = _resolve_db_path(db_path)
    if not target.exists():
        msg = f"Database not found at {target}"
        raise FileNotFoundError(msg)
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    return conn


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    """Hash one password using standard-library scrypt.

    Args:
        password: Plaintext password to hash.

    Returns:
        Encoded password hash string.

    Raises:
        ValueError: If password is empty.
    """
    if not password:
        msg = "Password must not be empty"
        raise ValueError(msg)
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_N,
        r=_R,
        p=_P,
        maxmem=_MAX_MEMORY_BYTES,
        dklen=_KEY_BYTES,
    )
    salt_text = base64.urlsafe_b64encode(salt).decode("ascii")
    digest_text = base64.urlsafe_b64encode(digest).decode("ascii")
    return f"{_ALGORITHM}${_N}${_R}${_P}${salt_text}${digest_text}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password candidate against versioned scrypt hash record.

    Args:
        password: Plaintext password candidate.
        stored_hash: Stored encoded scrypt record.

    Returns:
        True if password matches, False otherwise.
    """
    if not password or not stored_hash or stored_hash == "disabled":
        return False
    try:
        parts = stored_hash.split("$")
        if len(parts) != _EXPECTED_HASH_PARTS or parts[0] != _ALGORITHM:
            return False
        _, n_str, r_str, p_str, salt_text, digest_text = parts
        n, r, p = int(n_str), int(r_str), int(p_str)
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            maxmem=_MAX_MEMORY_BYTES,
            dklen=len(expected),
        )
        return hmac.compare_digest(actual, expected)
    except ValueError, TypeError:
        return False


def register_user(
    username: str,
    password: str,
    runtime_profile: str = "research",
    db_path: Path | str | None = None,
) -> tuple[dict[str, Any], str, str]:
    """Register a new user in the SQLite database and create an active session.

    Args:
        username: Login username.
        password: Raw password.
        runtime_profile: Account execution profile.
        db_path: Optional explicit SQLite database path.

    Returns:
        tuple of (user_data_dict, session_token, csrf_token).

    Raises:
        ValueError: If username or password does not meet requirements
            or username is already taken.
    """
    clean_username = username.strip()
    if not _USERNAME_PATTERN.match(clean_username):
        msg = (
            "Username must be 3-64 alphanumeric, underscore, hyphen, or dot characters"
        )
        raise ValueError(msg)
    if len(password) < _MIN_PASSWORD_LEN:
        msg = "Password must be at least 6 characters"
        raise ValueError(msg)
    if runtime_profile not in ("research", "simulation", "demo", "live"):
        runtime_profile = "research"

    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM users WHERE LOWER(username) = LOWER(?)", (clean_username,)
        )
        if cur.fetchone() is not None:
            msg = "Username is already taken"
            raise ValueError(msg)

        user_id = f"usr_{secrets.token_hex(8)}"
        pwd_hash = hash_password(password)
        now = _utc_now_iso()
        expires_at = (
            (datetime.now(UTC) + timedelta(days=_SESSION_TTL_DAYS))
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

        cur.execute(
            """
            INSERT INTO users (
                user_id, username, password_hash, roles_json, permissions_json,
                environment, active, verified, created_at, runtime_profile
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                clean_username,
                pwd_hash,
                '["user"]',
                "[]",
                "development",
                1,
                1,
                now,
                runtime_profile,
            ),
        )

        session_token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)

        cur.execute(
            """
            INSERT INTO sessions (
                session_digest, user_id, csrf_digest, created_at, expires_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                _digest(session_token),
                user_id,
                _digest(csrf_token),
                now,
                expires_at,
            ),
        )

        conn.commit()

        user_data = {
            "user_id": user_id,
            "username": clean_username,
            "expires_at": expires_at,
            "runtime_profile": runtime_profile,
        }
        return user_data, session_token, csrf_token
    finally:
        conn.close()


def login_user(
    username: str,
    password: str,
    db_path: Path | str | None = None,
) -> tuple[dict[str, Any], str, str]:
    """Authenticate an existing user and create an active session.

    Args:
        username: Login username.
        password: Raw password.
        db_path: Optional explicit SQLite database path.

    Returns:
        tuple of (user_data_dict, session_token, csrf_token).

    Raises:
        ValueError: If username or password is invalid or account inactive.
    """
    clean_username = username.strip()
    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT user_id, username, password_hash, active, verified, runtime_profile
            FROM users
            WHERE LOWER(username) = LOWER(?)
            """,
            (clean_username,),
        )
        row = cur.fetchone()
        if row is None:
            msg = "Invalid username or password"
            raise ValueError(msg)

        if not bool(row["active"]) or not bool(row["verified"]):
            msg = "Account is inactive or unverified"
            raise ValueError(msg)

        if not verify_password(password, str(row["password_hash"])):
            msg = "Invalid username or password"
            raise ValueError(msg)

        now = _utc_now_iso()
        expires_at = (
            (datetime.now(UTC) + timedelta(days=_SESSION_TTL_DAYS))
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

        session_token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)

        cur.execute(
            """
            INSERT INTO sessions (
                session_digest, user_id, csrf_digest, created_at, expires_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                _digest(session_token),
                row["user_id"],
                _digest(csrf_token),
                now,
                expires_at,
            ),
        )

        cur.execute(
            "UPDATE users SET last_login_at = ? WHERE user_id = ?",
            (now, row["user_id"]),
        )

        conn.commit()

        user_data = {
            "user_id": str(row["user_id"]),
            "username": str(row["username"]),
            "expires_at": expires_at,
            "runtime_profile": str(row["runtime_profile"]),
        }
        return user_data, session_token, csrf_token
    finally:
        conn.close()


def get_session_identity(
    session_token: str | None,
    db_path: Path | str | None = None,
) -> dict[str, Any] | None:
    """Validate a session token and return identity claims if active and valid.

    Args:
        session_token: Raw session token from cookie.
        db_path: Optional explicit SQLite database path.

    Returns:
        Dict of user identity if valid, None otherwise.
    """
    if not session_token:
        return None

    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                u.user_id,
                u.username,
                u.runtime_profile,
                s.expires_at,
                s.revoked_at,
                u.active
            FROM sessions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.session_digest = ?
            """,
            (_digest(session_token),),
        )
        row = cur.fetchone()
        if row is None:
            return None

        if row["revoked_at"] is not None:
            return None

        if not bool(row["active"]):
            return None

        now = _utc_now_iso()
        if str(row["expires_at"]) <= now:
            return None

        return {
            "user_id": str(row["user_id"]),
            "username": str(row["username"]),
            "expires_at": str(row["expires_at"]),
            "runtime_profile": str(row["runtime_profile"]),
        }
    finally:
        conn.close()


def logout_session(
    session_token: str | None,
    db_path: Path | str | None = None,
) -> None:
    """Revoke an active session token.

    Args:
        session_token: Raw session token from cookie.
        db_path: Optional explicit SQLite database path.
    """
    if not session_token:
        return

    conn = _get_connection(db_path)
    try:
        now = _utc_now_iso()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE sessions
            SET revoked_at = ?
            WHERE session_digest = ? AND revoked_at IS NULL
            """,
            (now, _digest(session_token)),
        )
        conn.commit()
    finally:
        conn.close()
