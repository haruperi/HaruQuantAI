"""Account and session management service.

Purpose:
    Own the workstation's account registry and opaque server-side
    sessions behind the ``workspace.manage-accounts@1`` capability:
    registration with scrypt password hashing, login, session-token
    validation, and revocation.

Key capabilities:
    * Register users into the shared workspace database with a versioned
      scrypt password record and an initial 7-day session.
    * Authenticate users with constant-time hash and token comparison.
    * Validate opaque session tokens against digest-only storage.
    * Revoke sessions on logout.

Python API usage:
    service = AccountService(ManageAccountsConfig())
    result = await service.manage_accounts(request)

CLI usage:
    uv run python -m app.services.workspace.manage_accounts.accounts
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import hmac
import re
import secrets
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Final, cast
from uuid import uuid7

from app.contracts.common.models import ProblemDetails
from app.contracts.workspace.errors import WorkspaceFailure
from app.contracts.workspace.models import (
    AccountRecord,
    ManageAccountsRequest,
    ManageAccountsSuccess,
)
from app.services.workspace.manage_accounts.config import ManageAccountsConfig

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
_RUNTIME_PROFILES: Final = ("research", "simulation", "demo", "live")


_TIMESTAMP_FORMAT: Final = "%Y-%m-%dT%H:%M:%S.%fZ"


def _utc_now_iso() -> str:
    """Return the current UTC instant formatted as UtcTimestamp."""
    return datetime.now(UTC).strftime(_TIMESTAMP_FORMAT)


def _expiry_iso() -> str:
    """Return the session expiry instant formatted as UtcTimestamp."""
    return (datetime.now(UTC) + timedelta(days=_SESSION_TTL_DAYS)).strftime(
        _TIMESTAMP_FORMAT
    )


def _normalize_iso(val: object) -> str:
    """Normalize any date/time value to canonical UtcTimestamp wire format.

    Args:
        val: Input datetime, string, or None.

    Returns:
        Canonical UtcTimestamp formatted string.
    """
    if not val:
        return datetime.now(UTC).strftime(_TIMESTAMP_FORMAT)
    text = str(val)
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC).strftime(_TIMESTAMP_FORMAT)
    except ValueError, TypeError:
        return datetime.now(UTC).strftime(_TIMESTAMP_FORMAT)


def _digest(token: str) -> str:
    """Return the storage digest for one opaque token."""
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
        message = "Password must not be empty"
        raise ValueError(message)
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


def _registration_failure(
    request: ManageAccountsRequest, detail: str
) -> WorkspaceFailure:
    """Build one registration-policy failure envelope.

    Args:
        request: Account request.
        detail: Human-readable failure detail.

    Returns:
        Structured workspace failure envelope.
    """
    return WorkspaceFailure(
        request_id=request.request_id,
        code="ACCOUNT_REGISTRATION_FAILED",
        problem=ProblemDetails(
            title="Registration failed",
            status=400,
            code="ACCOUNT_REGISTRATION_FAILED",
            detail=detail,
        ),
    )


def _authentication_failure(
    request: ManageAccountsRequest, detail: str
) -> WorkspaceFailure:
    """Build one authentication failure envelope.

    Args:
        request: Account request.
        detail: Human-readable failure detail.

    Returns:
        Structured workspace failure envelope.
    """
    return WorkspaceFailure(
        request_id=request.request_id,
        code="ACCOUNT_AUTHENTICATION_FAILED",
        problem=ProblemDetails(
            title="Authentication failed",
            status=401,
            code="ACCOUNT_AUTHENTICATION_FAILED",
            detail=detail,
        ),
    )


class AccountService:
    """Account registry and session store for the manage-accounts capability."""

    def __init__(self, config: ManageAccountsConfig | None = None) -> None:
        """Open the account database and ensure its schema exists.

        Args:
            config: Service configuration carrying the database path.
        """
        self._config = config or ManageAccountsConfig()
        target = Path(self._config.database_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(target), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._init_db()

    def _init_db(self) -> None:
        """Create the account tables when they do not exist yet.

        The DDL matches the shared workspace database schema exactly;
        concurrent creators converge because every statement is
        ``IF NOT EXISTS``.
        """
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
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
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_digest TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    csrf_digest TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    revoked_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                        ON DELETE CASCADE
                )
                """
            )

    def close(self) -> None:
        """Close the underlying database connection."""
        with contextlib.suppress(sqlite3.Error):
            self._conn.close()

    async def manage_accounts(
        self, request: ManageAccountsRequest
    ) -> ManageAccountsSuccess | WorkspaceFailure:
        """Serve one operation-discriminated account request.

        Args:
            request: REGISTER, LOGIN, ME, or LOGOUT request.

        Returns:
            Account operation success, or a structured workspace failure.
        """
        if request.operation == "REGISTER":
            return self._register(request)
        if request.operation == "LOGIN":
            return self._login(request)
        if request.operation == "ME":
            return self._resolve_session(request)
        return self._logout(request)

    def _register(
        self, request: ManageAccountsRequest
    ) -> ManageAccountsSuccess | WorkspaceFailure:
        """Register one user and open their first session.

        Returns:
            Registration success with session tokens, or a typed failure.
        """
        username = (request.username or "").strip()
        password = request.password or ""
        if not _USERNAME_PATTERN.match(username):
            detail = (
                "Username must be 3-64 alphanumeric, underscore, hyphen, "
                "or dot characters"
            )
            return _registration_failure(request, detail)
        if len(password) < _MIN_PASSWORD_LEN:
            detail = "Password must be at least 6 characters"
            return _registration_failure(request, detail)
        profile = (
            request.runtime_profile
            if request.runtime_profile in _RUNTIME_PROFILES
            else "research"
        )
        now = _utc_now_iso()
        expires_at = _expiry_iso()
        user_id = f"usr_{secrets.token_hex(8)}"
        try:
            with self._conn:
                existing = self._conn.execute(
                    "SELECT 1 FROM users WHERE LOWER(username) = LOWER(?)",
                    (username,),
                ).fetchone()
                if existing is not None:
                    return _registration_failure(request, "Username is already taken")
                self._conn.execute(
                    """
                    INSERT INTO users (
                        user_id, username, password_hash, roles_json,
                        permissions_json, environment, active, verified,
                        created_at, runtime_profile
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        username,
                        hash_password(password),
                        '["user"]',
                        "[]",
                        "development",
                        1,
                        1,
                        now,
                        profile,
                    ),
                )
                session_token, csrf_token = self._insert_session(user_id)
        except sqlite3.IntegrityError:
            return _registration_failure(request, "Username is already taken")
        return ManageAccountsSuccess(
            request_id=request.request_id,
            user=AccountRecord(
                user_id=user_id,
                username=username,
                expires_at=expires_at,
                runtime_profile=profile,
            ),
            session_token=session_token,
            csrf_token=csrf_token,
        )

    def _login(
        self, request: ManageAccountsRequest
    ) -> ManageAccountsSuccess | WorkspaceFailure:
        """Authenticate one user and open a session.

        Returns:
            Login success with session tokens, or a typed failure.
        """
        username = (request.username or "").strip()
        row = self._conn.execute(
            """
            SELECT user_id, username, password_hash, active, verified,
                   runtime_profile
            FROM users WHERE LOWER(username) = LOWER(?)
            """,
            (username,),
        ).fetchone()
        if row is None:
            return _authentication_failure(request, "Invalid username or password")
        if not bool(row["active"]) or not bool(row["verified"]):
            return _authentication_failure(request, "Account is inactive or unverified")
        if not verify_password(request.password or "", str(row["password_hash"])):
            return _authentication_failure(request, "Invalid username or password")
        expires_at = _expiry_iso()
        with self._conn:
            session_token, csrf_token = self._insert_session(str(row["user_id"]))
            self._conn.execute(
                "UPDATE users SET last_login_at = ? WHERE user_id = ?",
                (_utc_now_iso(), row["user_id"]),
            )
        return ManageAccountsSuccess(
            request_id=request.request_id,
            user=AccountRecord(
                user_id=str(row["user_id"]),
                username=str(row["username"]),
                expires_at=expires_at,
                runtime_profile=str(row["runtime_profile"]),
            ),
            session_token=session_token,
            csrf_token=csrf_token,
        )

    def _resolve_session(
        self, request: ManageAccountsRequest
    ) -> ManageAccountsSuccess | WorkspaceFailure:
        """Validate one session token and return its identity claims.

        Returns:
            Session identity success, or a typed failure.
        """
        record = self._session_row(request.session_token or "")
        if record is None:
            return _authentication_failure(request, "Session is not valid")
        return ManageAccountsSuccess(
            request_id=request.request_id,
            user=AccountRecord(
                user_id=str(record["user_id"]),
                username=str(record["username"]),
                expires_at=_normalize_iso(record["expires_at"]),
                runtime_profile=str(record["runtime_profile"]),
            ),
        )

    def _logout(
        self, request: ManageAccountsRequest
    ) -> ManageAccountsSuccess | WorkspaceFailure:
        """Revoke one active session; unknown tokens logout cleanly.

        Returns:
            Logout success; revocation is idempotent.
        """
        token = request.session_token or ""
        if token:
            with self._conn:
                self._conn.execute(
                    """
                    UPDATE user_sessions
                    SET revoked_at = ?
                    WHERE session_digest = ? AND revoked_at IS NULL
                    """,
                    (_utc_now_iso(), _digest(token)),
                )
        return ManageAccountsSuccess(
            request_id=request.request_id,
            revoked=True,
        )

    def _insert_session(self, user_id: str) -> tuple[str, str]:
        """Issue and persist one session with its CSRF peer token.

        Returns:
            Tuple of (session_token, csrf_token); only digests persist.
        """
        session_token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        self._conn.execute(
            """
            INSERT INTO user_sessions (
                session_digest, user_id, csrf_digest, created_at, expires_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                _digest(session_token),
                user_id,
                _digest(csrf_token),
                _utc_now_iso(),
                _expiry_iso(),
            ),
        )
        return session_token, csrf_token

    def _session_row(self, session_token: str) -> sqlite3.Row | None:
        """Return the active identity row for one session token.

        Returns:
            Joined identity row, or None when the token is unknown,
            revoked, expired, or the account is inactive.
        """
        if not session_token:
            return None
        row = self._conn.execute(
            """
            SELECT
                u.user_id,
                u.username,
                u.runtime_profile,
                s.expires_at,
                s.revoked_at,
                u.active
            FROM user_sessions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.session_digest = ?
            """,
            (_digest(session_token),),
        ).fetchone()
        if row is None:
            return None
        if row["revoked_at"] is not None:
            return None
        if not bool(row["active"]):
            return None
        if str(row["expires_at"]) <= _utc_now_iso():
            return None
        return cast("sqlite3.Row", row)


DEMO_SECRET = "secret123"  # noqa: S105  # pragma: allowlist secret


def _run_usage_example() -> None:  # pragma: no cover - usage harness
    """Demonstrate the account lifecycle against a temporary database."""
    import asyncio
    import tempfile

    from app.contracts.workspace.models import ManageAccountsRequest

    with tempfile.TemporaryDirectory() as tmp:
        from app.services.workspace.manage_accounts.config import (
            ManageAccountsConfig,
        )

        service = AccountService(
            ManageAccountsConfig(database_path=Path(tmp) / "accounts.db")
        )

        async def scenario() -> None:
            request = ManageAccountsRequest(
                request_id=str(uuid7()),
                capability_snapshot_id=str(uuid7()),
                operation="REGISTER",
                username="trader",
                password=DEMO_SECRET,
            )
            registered = await service.manage_accounts(request)
            login = await service.manage_accounts(
                ManageAccountsRequest(
                    request_id=str(uuid7()),
                    capability_snapshot_id=str(uuid7()),
                    operation="LOGIN",
                    username="trader",
                    password=DEMO_SECRET,
                )
            )
            if isinstance(registered, WorkspaceFailure) or isinstance(
                login, WorkspaceFailure
            ):
                print("registration/login failed")
            else:
                user1 = registered.user.username if registered.user else None
                user2 = login.user.username if login.user else None
                print(f"registered={user1} login={user2}")
            service.close()

        asyncio.run(scenario())


if __name__ == "__main__":  # pragma: no cover
    _run_usage_example()
