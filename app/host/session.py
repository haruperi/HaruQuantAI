"""Session authority, credential verification, bearer tokens, and durable revocation.

Description:
    Provides the authoritative session management and operator authentication
    subsystem for the HaruQuantAI platform. Implements salted PBKDF2 password
    hashing and verification, HMAC-SHA256 ephemeral bearer token issuance and
    cryptographic verification, in-memory sliding-window per-peer retry throttling,
    and durable transactional SQLite session tracking and revocation in the
    `host_session` table. Interacts with the host database to guarantee complete
    session lifecycle auditing, token status validation, and immediate revocation.

Purpose:
    FEAT-HOST-SESSION: Operator Authentication, Ephemeral Tokens, and Revocation.
    Provides salted PBKDF2 credential verification, HMAC-signed bearer token issuance,
    sliding-window rate limiting, and durable SQLite token revocation.

Capabilities:
    - FR-HOST-SESSION-CREDENTIAL-VERIFICATION: Salted PBKDF2 Password Hashing
      Associated: `[SessionAuthority.verify_password()]`,
        `[SessionAuthority.hash_password()]`
      Logging: Emits INFO upon successful credential verification; emits WARNING
      on failed verification attempts with peer context.
    - FR-HOST-SESSION-TOKEN-ISSUANCE: Ephemeral HMAC Bearer Token Generation
      Associated: `[SessionAuthority.create_session()]`,
        `[SessionAuthority.issue_token()]`
      Logging: Emits INFO upon session creation and token issuance declaring session
      identifier, username, peer identifier, and expiration timestamp.
    - FR-HOST-SESSION-RATE-LIMITING: Sliding-Window Per-Peer Retry Throttling
      Associated: `[SessionAuthority.check_rate_limit()]`,
        `[SessionAuthority.record_attempt()]`
      Logging: Emits DEBUG on recorded authentication attempts; emits WARNING when
      a peer exceeds the allowed sliding-window attempt quota.
    - FR-HOST-SESSION-TOKEN-VERIFICATION: Signature & Persistence Validation
      Associated: `[SessionAuthority.verify_token()]`
      Logging: Emits DEBUG upon successful token signature and persistence
      validation; emits WARNING when encountering invalid signatures, expired
      tokens, or revoked tokens.
    - FR-HOST-SESSION-DURABLE-REVOCATION: Immediate Database Token Revocation
      Associated: `[SessionAuthority.revoke_session()]`,
        `[SessionAuthority.revoke_token()]`
      Logging: Emits INFO upon immediate database revocation of an active session.

Python API Usage:
    ```python
    from app.host.session import SessionAuthority

    authority = SessionAuthority()
    authority.initialize()

    # Authenticate and issue ephemeral token
    token_bundle = authority.create_session(username="operator", peer_id="127.0.0.1")
    raw_token = token_bundle.token

    # Verify bearer token
    session_record = authority.verify_token(raw_token)
    assert session_record.status == "ACTIVE"

    # Durable revocation
    authority.revoke_session(session_record.session_id)
    ```

CLI Usage:
    Session authority is initialized during process startup by the host CLI:
    ```bash
    uv run python -m app.cli
    ```
"""

from __future__ import annotations

import base64
import collections
import hashlib
import hmac
import json
import secrets
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.host.logging import get_logger
from app.host.persistance import BUSY_TIMEOUT_SECONDS, DEFAULT_DATABASE_PATH

if TYPE_CHECKING:
    from collections.abc import Generator

__all__ = [
    "AuthenticationError",
    "InvalidTokenError",
    "IssuedToken",
    "RateLimitExceededError",
    "SessionAuthority",
    "SessionError",
    "SessionRecord",
    "TokenExpiredError",
    "TokenRevokedError",
]

logger = get_logger(__name__)

DEFAULT_PBKDF2_ITERATIONS: int = 100_000
DEFAULT_SESSION_TTL_SECONDS: int = 86_400  # 24 hours
DEFAULT_RATE_LIMIT_ATTEMPTS: int = 5
DEFAULT_RATE_LIMIT_WINDOW_SECONDS: float = 60.0

_BASE64_PAD_MULTIPLE: int = 4
_BEARER_TOKEN_PARTS: int = 3


class SessionError(Exception):
    """Base exception for all session authority and authentication errors."""


class AuthenticationError(SessionError):
    """Raised when credential verification fails."""


class RateLimitExceededError(SessionError):
    """Raised when a peer exceeds sliding-window retry throttling limits."""


class InvalidTokenError(SessionError):
    """Raised when a bearer token is malformed, tampered with, or unrecognized."""


class TokenExpiredError(SessionError):
    """Raised when a bearer token has surpassed its valid operational lifespan."""


class TokenRevokedError(SessionError):
    """Raised when a bearer token or session has been explicitly revoked."""


@dataclass(frozen=True, slots=True)
class SessionRecord:
    """Immutable representation of a persisted host session record.

    Attributes:
        session_id: Unique session identifier string.
        token_hash: SHA-256 digest hex string of the issued bearer token.
        username: Operator username bound to the session.
        peer_id: Network address or client identifier of the caller.
        created_at_utc: ISO 8601 UTC timestamp of session creation.
        expires_at_utc: ISO 8601 UTC timestamp of session expiration.
        revoked_at_utc: ISO 8601 UTC timestamp when revoked, or None if active.
        status: Current session state ('ACTIVE', 'REVOKED', or 'EXPIRED').
    """

    session_id: str
    token_hash: str
    username: str
    peer_id: str
    created_at_utc: str
    expires_at_utc: str
    revoked_at_utc: str | None
    status: str


@dataclass(frozen=True, slots=True)
class IssuedToken:
    """Pair of generated bearer token and its corresponding database record.

    Attributes:
        token: Base64url-encoded signed HMAC bearer token provided to client.
        record: Persisted SessionRecord stored in the host database.
    """

    token: str
    record: SessionRecord


def _now_utc_iso() -> str:
    """Return the current UTC timestamp formatted as ISO 8601 string."""
    return datetime.now(UTC).isoformat()


def _b64url_encode(data: bytes) -> str:
    """Encode bytes into URL-safe unpadded base64 string."""
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(encoded: str) -> bytes:
    """Decode unpadded URL-safe base64 string into raw bytes."""
    padding = _BASE64_PAD_MULTIPLE - (len(encoded) % _BASE64_PAD_MULTIPLE)
    if padding != _BASE64_PAD_MULTIPLE:
        encoded += "=" * padding
    return base64.urlsafe_b64decode(encoded.encode("ascii"))


class SessionAuthority:
    """Authoritative host operator authentication and session management service.

    Manages credential verification using salted PBKDF2 hashes, signs and validates
    ephemeral HMAC bearer tokens, throttles retries via sliding-window rate limiting,
    and durably records and revokes sessions in the host SQLite database.
    """

    def __init__(
        self,
        db_path: Path | str | None = None,
        *,
        secret_key: bytes | None = None,
        rate_limit_attempts: int = DEFAULT_RATE_LIMIT_ATTEMPTS,
        rate_limit_window_seconds: float = DEFAULT_RATE_LIMIT_WINDOW_SECONDS,
        busy_timeout: float = BUSY_TIMEOUT_SECONDS,
    ) -> None:
        """Initialize SessionAuthority with database path and cryptographic parameters.

        Args:
            db_path: Path to authoritative SQLite database file. Defaults to
                repository database path.
            secret_key: Secret key bytes used for HMAC token signing. If None,
                generates a secure 32-byte ephemeral key for the host lifecycle.
            rate_limit_attempts: Maximum allowed authentication attempts per window.
            rate_limit_window_seconds: Sliding-window evaluation duration in seconds.
            busy_timeout: Timeout in seconds for SQLite lock waits.
        """
        self._db_path: Path = (
            Path(db_path).resolve() if db_path is not None else DEFAULT_DATABASE_PATH
        )
        self._secret_key: bytes = secret_key or secrets.token_bytes(32)
        self._rate_limit_attempts: int = max(1, rate_limit_attempts)
        self._rate_limit_window_seconds: float = max(1.0, rate_limit_window_seconds)
        self._busy_timeout: float = busy_timeout

        self._lock = threading.Lock()
        self._peer_attempts: dict[str, collections.deque[float]] = {}

    @property
    def db_path(self) -> Path:
        """Return the resolved host database file path."""
        return self._db_path

    @contextmanager
    def _connect(self, *, query_only: bool = False) -> Generator[sqlite3.Connection]:
        """Context manager yielding an authoritative SQLite database connection.

        Args:
            query_only: If True, opens connection in read-only query mode.

        Yields:
            Configured sqlite3.Connection instance with row factory and timeouts.
        """
        if not query_only:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)

        uri = (
            f"file:{self._db_path.as_posix()}?mode=ro"
            if query_only
            else f"file:{self._db_path.as_posix()}"
        )
        conn = sqlite3.connect(
            uri,
            timeout=self._busy_timeout,
            uri=True,
            autocommit=True,
        )
        conn.row_factory = sqlite3.Row
        try:
            conn.execute(f"PRAGMA busy_timeout = {int(self._busy_timeout * 1000)}")
            conn.execute("PRAGMA foreign_keys = ON")
            if query_only:
                conn.execute("PRAGMA query_only = ON")
            yield conn
        finally:
            conn.close()

    def initialize(self) -> None:
        """Create host_session table and secondary indices if they do not exist.

        Ensures that the host persistence store contains the authoritative session
        table with required column schemas and indexing.
        """
        with self._connect(query_only=False) as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS host_session (
                    session_id TEXT PRIMARY KEY,
                    token_hash TEXT NOT NULL UNIQUE,
                    username TEXT NOT NULL,
                    peer_id TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL,
                    expires_at_utc TEXT NOT NULL,
                    revoked_at_utc TEXT,
                    status TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_host_session_token_hash "
                "ON host_session(token_hash)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_host_session_peer_id "
                "ON host_session(peer_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_host_session_status "
                "ON host_session(status)"
            )
            conn.execute("COMMIT")

        logger.info(
            "Initialized host_session persistence table",
            extra={"db_path": str(self._db_path)},
        )

    def hash_password(
        self,
        plain_credential: str,
        *,
        salt_hex: str | None = None,
        iterations: int = DEFAULT_PBKDF2_ITERATIONS,
    ) -> tuple[str, str]:
        """Compute salted PBKDF2-HMAC-SHA256 digest of credential string.

        Args:
            plain_credential: Plaintext credential string to hash.
            salt_hex: Optional hex-encoded salt string. If None, generates a 16-byte
                cryptographic random salt.
            iterations: Number of PBKDF2 hash iterations.

        Returns:
            Tuple of (hash_hex, salt_hex) representation.
        """
        salt_bytes = (
            bytes.fromhex(salt_hex) if salt_hex is not None else secrets.token_bytes(16)
        )
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            plain_credential.encode("utf-8"),
            salt_bytes,
            iterations,
        )
        return digest.hex(), salt_bytes.hex()

    def verify_password(
        self,
        plain_credential: str,
        *,
        expected_hash_hex: str,
        salt_hex: str,
        iterations: int = DEFAULT_PBKDF2_ITERATIONS,
        peer_id: str = "local",
    ) -> bool:
        """Verify credential against expected hash using constant-time comparison.

        Args:
            plain_credential: Provided plaintext credential to verify.
            expected_hash_hex: Expected PBKDF2-HMAC-SHA256 hex digest string.
            salt_hex: Hex-encoded cryptographic salt string.
            iterations: Number of PBKDF2 iterations used during hashing.
            peer_id: Identifier of the peer attempting authentication.

        Returns:
            True if credentials match, False otherwise.
        """
        if not self.check_rate_limit(peer_id):
            logger.warning(
                "Authentication attempt rejected by rate limiter for peer %s",
                peer_id,
                extra={
                    "peer_id": peer_id,
                    "requirement": "FR-HOST-SESSION-RATE-LIMITING",
                },
            )
            return False

        try:
            salt_bytes = bytes.fromhex(salt_hex)
            computed_digest = hashlib.pbkdf2_hmac(
                "sha256",
                plain_credential.encode("utf-8"),
                salt_bytes,
                iterations,
            ).hex()
            is_valid = hmac.compare_digest(computed_digest, expected_hash_hex)
        except ValueError, TypeError:
            is_valid = False

        self.record_attempt(peer_id, success=is_valid)

        if is_valid:
            logger.info(
                "Credential verification succeeded for peer %s",
                peer_id,
                extra={
                    "peer_id": peer_id,
                    "requirement": "FR-HOST-SESSION-CREDENTIAL-VERIFICATION",
                },
            )
        else:
            logger.warning(
                "Credential verification failed for peer %s",
                peer_id,
                extra={
                    "peer_id": peer_id,
                    "requirement": "FR-HOST-SESSION-CREDENTIAL-VERIFICATION",
                },
            )

        return is_valid

    def check_rate_limit(self, peer_id: str) -> bool:
        """Evaluate whether peer has exceeded sliding-window attempt threshold.

        Args:
            peer_id: Network address or client identifier.

        Returns:
            True if peer is within rate limits, False if throttled.
        """
        now = time.monotonic()
        cutoff = now - self._rate_limit_window_seconds

        with self._lock:
            queue = self._peer_attempts.get(peer_id)
            if not queue:
                return True
            while queue and queue[0] < cutoff:
                queue.popleft()
            return len(queue) < self._rate_limit_attempts

    def record_attempt(self, peer_id: str, *, success: bool) -> None:
        """Record an authentication attempt timestamp for peer throttling.

        Args:
            peer_id: Network address or client identifier.
            success: Whether the authentication attempt was successful.
        """
        now = time.monotonic()
        cutoff = now - self._rate_limit_window_seconds

        with self._lock:
            queue = self._peer_attempts.setdefault(peer_id, collections.deque())
            while queue and queue[0] < cutoff:
                queue.popleft()

            if not success:
                queue.append(now)
                attempts_count = len(queue)
                if attempts_count >= self._rate_limit_attempts:
                    logger.warning(
                        "Peer %s exceeded sliding-window rate limit (%d/%d attempts)",
                        peer_id,
                        attempts_count,
                        self._rate_limit_attempts,
                        extra={
                            "peer_id": peer_id,
                            "attempts": attempts_count,
                            "window_seconds": self._rate_limit_window_seconds,
                            "requirement": "FR-HOST-SESSION-RATE-LIMITING",
                        },
                    )
                else:
                    logger.debug(
                        "Recorded failed attempt for peer %s (%d/%d attempts)",
                        peer_id,
                        attempts_count,
                        self._rate_limit_attempts,
                        extra={
                            "peer_id": peer_id,
                            "attempts": attempts_count,
                            "requirement": "FR-HOST-SESSION-RATE-LIMITING",
                        },
                    )
            else:
                # Reset failed attempts queue upon successful authentication
                queue.clear()
                logger.debug(
                    "Cleared rate limit history for authenticated peer %s",
                    peer_id,
                    extra={
                        "peer_id": peer_id,
                        "requirement": "FR-HOST-SESSION-RATE-LIMITING",
                    },
                )

    def _sign_payload(self, payload_bytes: bytes) -> str:
        """Generate HMAC-SHA256 signature string for token payload.

        Args:
            payload_bytes: Raw bytes to sign.

        Returns:
            Base64url-encoded HMAC signature string.
        """
        digest = hmac.new(self._secret_key, payload_bytes, hashlib.sha256).digest()
        return _b64url_encode(digest)

    def create_session(
        self,
        username: str,
        *,
        peer_id: str = "local",
        ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
    ) -> IssuedToken:
        """Create a new authenticated operator session and persist in host database.

        Args:
            username: Operator username bound to the session.
            peer_id: Network or client peer identifier.
            ttl_seconds: Lifespan of the issued bearer token in seconds.

        Returns:
            IssuedToken containing raw bearer token and persisted SessionRecord.

        Raises:
            RateLimitExceededError: If the peer has exceeded rate limiting quotas.
        """
        if not self.check_rate_limit(peer_id):
            raise RateLimitExceededError(
                f"Rate limit exceeded for peer '{peer_id}'. Try again later."
            )

        session_id = secrets.token_hex(16)
        created_dt = datetime.now(UTC)
        expires_dt = created_dt + timedelta(seconds=ttl_seconds)

        created_at_utc = created_dt.isoformat()
        expires_at_utc = expires_dt.isoformat()

        payload_dict: dict[str, Any] = {
            "session_id": session_id,
            "username": username,
            "peer_id": peer_id,
            "created_at_utc": created_at_utc,
            "expires_at_utc": expires_at_utc,
        }
        payload_bytes = json.dumps(
            payload_dict, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        payload_part = _b64url_encode(payload_bytes)
        signature_part = self._sign_payload(payload_bytes)

        raw_token = f"{session_id}.{payload_part}.{signature_part}"
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

        record = SessionRecord(
            session_id=session_id,
            token_hash=token_hash,
            username=username,
            peer_id=peer_id,
            created_at_utc=created_at_utc,
            expires_at_utc=expires_at_utc,
            revoked_at_utc=None,
            status="ACTIVE",
        )

        with self._connect(query_only=False) as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                INSERT INTO host_session (
                    session_id, token_hash, username, peer_id,
                    created_at_utc, expires_at_utc, revoked_at_utc, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.session_id,
                    record.token_hash,
                    record.username,
                    record.peer_id,
                    record.created_at_utc,
                    record.expires_at_utc,
                    record.revoked_at_utc,
                    record.status,
                ),
            )
            conn.execute("COMMIT")

        logger.info(
            "Issued session token %s for user %s (peer: %s, expires: %s)",
            session_id,
            username,
            peer_id,
            expires_at_utc,
            extra={
                "session_id": session_id,
                "username": username,
                "peer_id": peer_id,
                "expires_at_utc": expires_at_utc,
                "requirement": "FR-HOST-SESSION-TOKEN-ISSUANCE",
            },
        )

        return IssuedToken(token=raw_token, record=record)

    def issue_token(
        self,
        username: str,
        *,
        peer_id: str = "local",
        ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
    ) -> IssuedToken:
        """Alias for create_session providing token issuance capability."""
        return self.create_session(
            username=username, peer_id=peer_id, ttl_seconds=ttl_seconds
        )

    def verify_token(self, raw_token: str) -> SessionRecord:
        """Validate HMAC bearer token signature, expiration, and database status.

        Args:
            raw_token: Bearer token string provided by client.

        Returns:
            Verified SessionRecord from the host database.

        Raises:
            InvalidTokenError: If token structure, payload, or HMAC is invalid.
            TokenExpiredError: If token has surpassed its expiration timestamp.
            TokenRevokedError: If token has been revoked in the host database.
        """
        parts = raw_token.split(".")
        if len(parts) != _BEARER_TOKEN_PARTS:
            logger.warning(
                "Bearer token rejected due to invalid structure",
                extra={"requirement": "FR-HOST-SESSION-TOKEN-VERIFICATION"},
            )
            raise InvalidTokenError("Malformed bearer token structure")

        session_id, payload_part, signature_part = parts

        try:
            payload_bytes = _b64url_decode(payload_part)
            _ = json.loads(payload_bytes.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            logger.warning(
                "Bearer token rejected due to unparseable payload",
                extra={"requirement": "FR-HOST-SESSION-TOKEN-VERIFICATION"},
            )
            raise InvalidTokenError("Invalid bearer token payload") from exc

        expected_sig = self._sign_payload(payload_bytes)
        if not hmac.compare_digest(expected_sig, signature_part):
            logger.warning(
                "Bearer token rejected due to cryptographic signature mismatch",
                extra={
                    "session_id": session_id,
                    "requirement": "FR-HOST-SESSION-TOKEN-VERIFICATION",
                },
            )
            raise InvalidTokenError("Invalid bearer token signature")

        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

        with self._connect(query_only=True) as conn:
            row = conn.execute(
                """
                SELECT session_id, token_hash, username, peer_id,
                       created_at_utc, expires_at_utc, revoked_at_utc, status
                FROM host_session
                WHERE session_id = ? AND token_hash = ?
                """,
                (session_id, token_hash),
            ).fetchone()

        if row is None:
            logger.warning(
                "Bearer token %s not found in host_session persistence",
                session_id,
                extra={
                    "session_id": session_id,
                    "requirement": "FR-HOST-SESSION-TOKEN-VERIFICATION",
                },
            )
            raise InvalidTokenError("Session not found in persistence store")

        record = SessionRecord(
            session_id=row["session_id"],
            token_hash=row["token_hash"],
            username=row["username"],
            peer_id=row["peer_id"],
            created_at_utc=row["created_at_utc"],
            expires_at_utc=row["expires_at_utc"],
            revoked_at_utc=row["revoked_at_utc"],
            status=row["status"],
        )

        if record.status == "REVOKED" or record.revoked_at_utc is not None:
            logger.warning(
                "Bearer token %s rejected because session is revoked",
                session_id,
                extra={
                    "session_id": session_id,
                    "revoked_at_utc": record.revoked_at_utc,
                    "requirement": "FR-HOST-SESSION-TOKEN-VERIFICATION",
                },
            )
            raise TokenRevokedError(f"Session '{session_id}' has been revoked")

        # Expiration check
        try:
            expires_dt = datetime.fromisoformat(record.expires_at_utc)
            if datetime.now(UTC) > expires_dt:
                self._mark_session_expired(record.session_id)
                logger.warning(
                    "Bearer token %s rejected because session has expired",
                    session_id,
                    extra={
                        "session_id": session_id,
                        "expires_at_utc": record.expires_at_utc,
                        "requirement": "FR-HOST-SESSION-TOKEN-VERIFICATION",
                    },
                )
                raise TokenExpiredError(f"Session '{session_id}' has expired")
        except ValueError as exc:
            raise InvalidTokenError("Invalid expiration format in token") from exc

        logger.debug(
            "Bearer token %s successfully verified for user %s",
            session_id,
            record.username,
            extra={
                "session_id": session_id,
                "username": record.username,
                "requirement": "FR-HOST-SESSION-TOKEN-VERIFICATION",
            },
        )
        return record

    def _mark_session_expired(self, session_id: str) -> None:
        """Mark an expired session status in the host database transactionally."""
        with self._connect(query_only=False) as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "UPDATE host_session SET status = 'EXPIRED' "
                "WHERE session_id = ? AND status = 'ACTIVE'",
                (session_id,),
            )
            conn.execute("COMMIT")

    def revoke_session(self, session_id: str) -> bool:
        """Durably revoke a session in host database by session identifier.

        Args:
            session_id: Unique session identifier string.

        Returns:
            True if active session was revoked, False if already revoked or absent.
        """
        now_utc = _now_utc_iso()
        with self._connect(query_only=False) as conn:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.execute(
                """
                UPDATE host_session
                SET status = 'REVOKED', revoked_at_utc = ?
                WHERE session_id = ? AND status != 'REVOKED'
                """,
                (now_utc, session_id),
            )
            modified = cursor.rowcount > 0
            conn.execute("COMMIT")

        if modified:
            logger.info(
                "Durably revoked session %s in host_session table",
                session_id,
                extra={
                    "session_id": session_id,
                    "revoked_at_utc": now_utc,
                    "requirement": "FR-HOST-SESSION-DURABLE-REVOCATION",
                },
            )
        else:
            logger.debug(
                "Session %s revocation requested but was not active",
                session_id,
                extra={
                    "session_id": session_id,
                    "requirement": "FR-HOST-SESSION-DURABLE-REVOCATION",
                },
            )

        return modified

    def revoke_token(self, raw_token: str) -> bool:
        """Durably revoke a session by its raw bearer token string.

        Args:
            raw_token: Bearer token string to revoke.

        Returns:
            True if active session was revoked, False if already revoked or absent.
        """
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        now_utc = _now_utc_iso()

        with self._connect(query_only=False) as conn:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.execute(
                """
                UPDATE host_session
                SET status = 'REVOKED', revoked_at_utc = ?
                WHERE token_hash = ? AND status != 'REVOKED'
                """,
                (now_utc, token_hash),
            )
            modified = cursor.rowcount > 0
            conn.execute("COMMIT")

        if modified:
            logger.info(
                "Durably revoked session by token hash in host_session table",
                extra={
                    "token_hash": token_hash[:16] + "...",
                    "revoked_at_utc": now_utc,
                    "requirement": "FR-HOST-SESSION-DURABLE-REVOCATION",
                },
            )

        return modified
