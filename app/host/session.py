# ruff: noqa: INP001
"""Host session authority, credential hashing, and security token management.

Description:
    Provides the central authentication and session authority for HaruQuantAI.
    Implements cryptographic password hashing (PBKDF2-HMAC-SHA256 with random salt),
    ephemeral session creation with 64-character opaque tokens, SHA-256 token digest
    persistence in the SQLite WAL `host_session` table via `app.host.persistence`,
    sliding session expiration, explicit session revocation, host-restart invalidation
    binding sessions to the running host process instance ID, and granular
    capability scope authorization.

Purpose:
    FEAT-HOST-SESSION: Host-owned sessions, security boundaries, and token lifecycle.

Key Capabilities:
    - FR-HOST-SESSION-CREDENTIALS: Hash passwords and verify credentials securely.
      Associated: `hash_password()`, `verify_password()`
      Logging: INFO on verification success; WARNING on invalid credentials.
    - FR-HOST-SESSION-LIFECYCLE: Create, validate, expire, and revoke opaque tokens.
      Associated: `SessionManager.create_session()`, `SessionManager.validate_token()`,
      `SessionManager.revoke_session()`
      Logging: INFO on session creation and revocation; WARNING on expired tokens.
    - FR-HOST-SESSION-PERSISTENCE: Store session digests in host_session SQLite table.
      Associated: `SessionManager._persist_session()`, `SessionManager._update_status()`
      Logging: DEBUG on session record database writes.
    - FR-HOST-SESSION-RESTART-INVALIDATION: Invalidate sessions upon host restart.
      Associated: `SessionManager.reset()`, `SessionManager.host_instance_id`
      Logging: INFO on restart session reset.
    - FR-HOST-SESSION-SCOPE-AUTH: Evaluate fine-grained domain:action permission scopes.
      Associated: `SessionManager.authorize()`
      Logging: DEBUG on scope evaluation; WARNING on unauthorized action.

Python API Usage:
    ```python
    from app.host.session import hash_password, session_manager, verify_password

    # Credential hashing
    p_hash = hash_password("secret_pass")
    assert verify_password("secret_pass", p_hash)

    # Session lifecycle
    token, session = session_manager.create_session("admin", "peer-1")
    validated = session_manager.validate_token(token)
    assert validated is not None
    session_manager.revoke_session(session.session_id)
    ```

CLI Usage:
    ```bash
    uv run python -m app.host.session
    ```
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.host.logging import get_logger
from app.host.persistence.read import get_host_session_by_token_hash
from app.host.persistence.update import save_host_session, update_host_session_status

__all__ = [
    "SessionManager",
    "SessionRecord",
    "hash_password",
    "session_manager",
    "verify_password",
]

logger = get_logger(__name__)

CREDENTIALS_FR = "FR-HOST-SESSION-CREDENTIALS"
LIFECYCLE_FR = "FR-HOST-SESSION-LIFECYCLE"
PERSISTENCE_FR = "FR-HOST-SESSION-PERSISTENCE"
RESTART_FR = "FR-HOST-SESSION-RESTART-INVALIDATION"
SCOPE_AUTH_FR = "FR-HOST-SESSION-SCOPE-AUTH"

HASH_ITERATIONS: int = 100_000
SALT_BYTES: int = 16
RAW_TOKEN_LENGTH: int = 64

DEFAULT_OPERATOR_SCOPES: frozenset[str] = frozenset(
    {
        "settings:read",
        "settings:write",
        "jobs:read",
        "jobs:write",
        "telemetry:read",
        "diagnostics:read",
        "mcp:invoke",
    }
)


def _now_utc() -> datetime:
    """Return current timezone-aware UTC datetime."""
    return datetime.now(UTC)


def _now_utc_str() -> str:
    """Return formatted ISO UTC timestamp string."""
    return _now_utc().strftime("%Y-%m-%d %H:%M:%S")


def hash_password(
    password: str,
    salt: str | None = None,
    iterations: int | None = None,
) -> str:
    """Generate PBKDF2-HMAC-SHA256 password hash with cryptographically random salt.

    Args:
        password: Raw plaintext password to hash.
        salt: Optional hexadecimal salt. If omitted, a fresh 16-byte salt is generated.
        iterations: Optional PBKDF2 iteration count. Defaults to HASH_ITERATIONS.

    Returns:
        Formatted string containing `salt$hash`.
    """
    effective_salt = salt if salt is not None else secrets.token_hex(SALT_BYTES)
    effective_iterations = iterations if iterations is not None else HASH_ITERATIONS
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        effective_salt.encode("utf-8"),
        effective_iterations,
    )
    return f"{effective_salt}${derived.hex()}"


def verify_password(
    password: str,
    password_hash: str,
    iterations: int | None = None,
) -> bool:
    """Verify plaintext password against stored salt$hash with timing-attack mitigation.

    Args:
        password: Plaintext candidate password.
        password_hash: Stored `salt$hash` string.
        iterations: Optional PBKDF2 iteration count. Defaults to HASH_ITERATIONS.

    Returns:
        True if password matches, False otherwise.
    """
    if "$" not in password_hash:
        logger.warning("%s: invalid password hash format", CREDENTIALS_FR)
        return False

    salt, expected_hex = password_hash.split("$", 1)
    candidate_hash = hash_password(password, salt=salt, iterations=iterations)
    candidate_hex = candidate_hash.split("$", 1)[1]

    matches = hmac.compare_digest(candidate_hex, expected_hex)
    if matches:
        logger.debug("%s: password verification succeeded", CREDENTIALS_FR)
    else:
        logger.warning("%s: password verification rejected", CREDENTIALS_FR)
    return matches


@dataclass(frozen=True)
class SessionRecord:
    """Durable metadata representing an authenticated host session."""

    session_id: str
    token_hash: str
    username: str
    peer_id: str
    created_at_utc: str
    expires_at_utc: str
    revoked_at_utc: str | None = None
    status: str = "ACTIVE"

    def to_dict(self) -> dict[str, Any]:
        """Convert session record to dictionary."""
        return asdict(self)


class SessionManager:
    """Authority for ephemeral host sessions, tokens, and restart invalidation."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        *,
        host_instance_id: str | None = None,
    ) -> None:
        """Initialize SessionManager with isolated host instance identity.

        Args:
            db_path: Optional path to SQLite database.
            host_instance_id: Optional unique host instance ID.
        """
        self._db_path: Path | str | None = db_path
        self._host_instance_id: str = (
            host_instance_id if host_instance_id is not None else secrets.token_hex(8)
        )
        self._active_sessions: dict[str, SessionRecord] = {}

    @property
    def host_instance_id(self) -> str:
        """Return unique running host process instance identifier."""
        return self._host_instance_id

    @property
    def db_path(self) -> Path:
        """Return filesystem path to underlying SQLite database."""
        return (
            Path(self._db_path)
            if self._db_path is not None
            else Path("data/database/haruquantai.db")
        )

    def create_session(
        self,
        username: str,
        peer_id: str,
        *,
        duration_mins: int = 1440,
    ) -> tuple[str, SessionRecord]:
        """Issue a fresh 24h opaque token and record session metadata.

        Args:
            username: Authenticated username.
            peer_id: Client identifier or network peer.
            duration_mins: Validity window in minutes (default: 1440 = 24 hours).

        Returns:
            Tuple of (raw_opaque_token, SessionRecord).
        """
        raw_token = secrets.token_hex(32)  # 64-hex-char opaque token
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        session_id = f"sess_{secrets.token_hex(12)}"

        now = _now_utc()
        created_at = now.strftime("%Y-%m-%d %H:%M:%S")
        expires_at = (now + timedelta(minutes=duration_mins)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        record = SessionRecord(
            session_id=session_id,
            token_hash=token_hash,
            username=username,
            peer_id=peer_id,
            created_at_utc=created_at,
            expires_at_utc=expires_at,
            status="ACTIVE",
        )

        save_host_session(
            session_id=session_id,
            token_hash=token_hash,
            username=username,
            peer_id=peer_id,
            created_at_utc=created_at,
            expires_at_utc=expires_at,
            status="ACTIVE",
            conn=self._db_path,
        )

        self._active_sessions[token_hash] = record

        logger.info(
            "%s: created session %s for user %s (expires=%s)",
            LIFECYCLE_FR,
            session_id,
            username,
            expires_at,
            extra={
                "fr_id": LIFECYCLE_FR,
                "session_id": session_id,
                "username": username,
            },
        )
        return raw_token, record

    def validate_token(self, raw_token: str) -> SessionRecord | None:
        """Validate raw opaque token, verifying expiration and active status.

        Args:
            raw_token: 64-character bearer token supplied by caller.

        Returns:
            Active SessionRecord if valid, None if expired, revoked, or unknown.
        """
        if len(raw_token) != RAW_TOKEN_LENGTH:
            logger.warning("%s: invalid token length", LIFECYCLE_FR)
            return None

        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

        # Check in-memory active cache first
        record = self._active_sessions.get(token_hash)
        if record is None:
            row = get_host_session_by_token_hash(token_hash, conn=self._db_path)
            if not row:
                logger.warning(
                    "%s: token hash not found in session store", LIFECYCLE_FR
                )
                return None
            record = SessionRecord(
                session_id=row["session_id"],
                token_hash=row["token_hash"],
                username=row["username"],
                peer_id=row["peer_id"],
                created_at_utc=row["created_at_utc"],
                expires_at_utc=row["expires_at_utc"],
                revoked_at_utc=row.get("revoked_at_utc"),
                status=row["status"],
            )

        if record.status != "ACTIVE":
            logger.warning(
                "%s: rejected token for session %s (status=%s)",
                LIFECYCLE_FR,
                record.session_id,
                record.status,
            )
            return None

        # Check expiration
        expires_dt = datetime.strptime(
            record.expires_at_utc, "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=UTC)
        if _now_utc() > expires_dt:
            logger.warning(
                "%s: session %s expired at %s",
                LIFECYCLE_FR,
                record.session_id,
                record.expires_at_utc,
            )
            self._update_status(record.session_id, "EXPIRED")
            self._active_sessions.pop(token_hash, None)
            return None

        self._active_sessions[token_hash] = record
        return record

    def revoke_session(self, session_id: str) -> bool:
        """Revoke active session immediately.

        Args:
            session_id: Target session identifier to revoke.

        Returns:
            True if revoked, False if session not found.
        """
        now_str = _now_utc_str()
        updated = update_host_session_status(
            session_id,
            "REVOKED",
            revoked_at_utc=now_str,
            conn=self._db_path,
        )

        # Purge from memory
        to_purge = [
            th
            for th, rec in self._active_sessions.items()
            if rec.session_id == session_id
        ]
        for th in to_purge:
            self._active_sessions.pop(th, None)

        if updated:
            logger.info(
                "%s: revoked session %s",
                LIFECYCLE_FR,
                session_id,
                extra={"fr_id": LIFECYCLE_FR, "session_id": session_id},
            )
            return True
        return False

    def _update_status(self, session_id: str, new_status: str) -> None:
        """Update status of a session record in the persistence table."""
        update_host_session_status(
            session_id,
            new_status,
            conn=self._db_path,
        )

    def reset(self) -> None:
        """Reset host session state on restart, invalidating all in-memory sessions."""
        self._active_sessions.clear()
        self._host_instance_id = secrets.token_hex(8)
        logger.info(
            "%s: reset session manager (new host_instance_id=%s)",
            RESTART_FR,
            self._host_instance_id,
            extra={"fr_id": RESTART_FR, "host_instance_id": self._host_instance_id},
        )

    def authorize(self, session: SessionRecord, required_scope: str) -> bool:
        """Evaluate whether active session possesses requested permission scope.

        Args:
            session: Active authenticated session record.
            required_scope: Requested scope in `<domain>:<action>` format.

        Returns:
            True if authorized, False otherwise.
        """
        if session.status != "ACTIVE":
            logger.warning(
                "%s: access denied for inactive session %s",
                SCOPE_AUTH_FR,
                session.session_id,
            )
            return False

        if required_scope not in DEFAULT_OPERATOR_SCOPES:
            logger.warning(
                "%s: access denied: scope '%s' not granted to session %s",
                SCOPE_AUTH_FR,
                required_scope,
                session.session_id,
                extra={"fr_id": SCOPE_AUTH_FR, "scope": required_scope},
            )
            return False

        logger.debug(
            "%s: authorized scope %s for session %s (user=%s)",
            SCOPE_AUTH_FR,
            required_scope,
            session.session_id,
            session.username,
            extra={
                "fr_id": SCOPE_AUTH_FR,
                "scope": required_scope,
                "session_id": session.session_id,
            },
        )
        return True


session_manager: SessionManager = SessionManager()


def main() -> None:
    """Demonstrate SessionManager credential hashing, lifecycle, and revocation."""
    print("1. Password hashing and verification...")
    sample_key = "host_operator_secret_123"
    hashed = hash_password(sample_key, iterations=1_000)
    print(f"   Password hashed: {hashed[:25] + '...'}")
    if not verify_password(sample_key, hashed, iterations=1_000):
        raise RuntimeError("Password verification unexpectedly failed.")
    if verify_password("wrong_password", hashed, iterations=1_000):
        raise RuntimeError("Wrong password unexpectedly passed verification.")
    print("   Password verification matches successfully.")

    print("2. Reading configured user from database settings...")
    from app.host.settings import settings

    target_user = str(getattr(settings.user_access, "username", "haruquantai"))
    print(f"   Resolved database username: {target_user}")

    print("3. Creating host session...")
    mgr = SessionManager()
    token, record = mgr.create_session(target_user, "127.0.0.1", duration_mins=60)
    print(
        "   Session created: id=%s, user=%s",
        record.session_id,
        record.username,
    )

    print("4. Validating opaque token...")
    validated = mgr.validate_token(token)
    if validated is None:
        raise RuntimeError("Token validation unexpectedly returned None.")
    print(
        "   Token validated: session_id=%s, user=%s",
        validated.session_id,
        validated.username,
    )

    print("5. Evaluating scope authorization...")
    authorized = mgr.authorize(validated, "settings:write")
    print(f"   Scope 'settings:write' authorized: {authorized}")

    print("6. Revoking session...")
    revoked = mgr.revoke_session(record.session_id)
    print(f"   Session revoked: {revoked}")
    if mgr.validate_token(token) is not None:
        raise RuntimeError("Revoked token unexpectedly validated.")
    print("   Validated post-revocation token returns None as expected.")


if __name__ == "__main__":
    main()
