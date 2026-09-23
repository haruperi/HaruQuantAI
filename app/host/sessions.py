"""Bearer-token sessions for the host.

Tokens are issued by ``POST /api/v1/auth/login`` and enforced by the
webserver's auth middleware on every non-exempt ``/api`` route. They live in
memory only: a host restart invalidates all sessions and requires re-login
(fail closed, no credential persistence on disk).

Two operating modes:

- **Locked** (``HARUQUANTAI_HOST_PASSWORD`` set): the password is required
  and compared in constant time to avoid timing oracles.
- **Research** (unset): tokens are issued without a password; this is a
  documented convenience mode for local research, not an authorization
  bypass — enforcement stays on so every request still presents a token.
"""

from __future__ import annotations

import hmac
import secrets
import threading
import time
from dataclasses import dataclass

SESSION_TTL_SECONDS = 12 * 60 * 60
TOKEN_BYTES = 32


@dataclass(frozen=True)
class SessionInfo:
    """A verified session's identity and validity window.

    Attributes:
        username: The identity supplied at login.
        issued_at: Monotonic timestamp of issuance.
        expires_at: Monotonic timestamp after which verification fails.
    """

    username: str
    issued_at: float
    expires_at: float


class SessionError(Exception):
    """Raised when login fails (bad credentials or empty username)."""


class SessionManager:
    """In-memory bearer-token store with TTL expiry.

    Thread-safe: issuance, verification, and revocation serialize on a lock
    so multi-threaded servers and test threads share one consistent view.
    Expired sessions are dropped lazily on every mutation and lookup.
    """

    def __init__(
        self, password: str | None, *, ttl_seconds: int = SESSION_TTL_SECONDS
    ) -> None:
        """Create a manager.

        Args:
            password: Required login password (locked mode), or ``None``
                for research mode (no password asked).
            ttl_seconds: Session lifetime in seconds (default 12 hours).
        """
        self._password = password
        self._ttl_seconds = ttl_seconds
        self._sessions: dict[str, SessionInfo] = {}
        self._lock = threading.Lock()

    def login(self, username: str, password: str | None) -> str:
        """Issue a session token for ``username`` after credential checks.

        Args:
            username: Non-empty caller identity.
            password: Supplied password; ignored in research mode.

        Returns:
            A fresh opaque bearer token.

        Raises:
            SessionError: If the username is empty or the supplied password
                does not match the configured one.
        """
        if not username.strip():
            raise SessionError("Username must not be empty")
        if self._password is not None:
            supplied = password if password is not None else ""
            if not hmac.compare_digest(supplied.encode(), self._password.encode()):
                raise SessionError("Invalid credentials")

        token = secrets.token_urlsafe(TOKEN_BYTES)
        now = time.monotonic()
        with self._lock:
            self._drop_expired(now)
            self._sessions[token] = SessionInfo(
                username=username,
                issued_at=now,
                expires_at=now + self._ttl_seconds,
            )
        return token

    def verify(self, token: str) -> SessionInfo | None:
        """Return the live session for ``token``, or ``None`` when invalid.

        Unknown, expired, and revoked tokens are indistinguishable by
        design: callers learn only that the token does not authenticate.
        """
        now = time.monotonic()
        with self._lock:
            self._drop_expired(now)
            return self._sessions.get(token)

    def revoke(self, token: str) -> None:
        """Drop a session token if present."""
        with self._lock:
            self._sessions.pop(token, None)

    def _drop_expired(self, now: float) -> None:
        expired = [
            token for token, info in self._sessions.items() if info.expires_at <= now
        ]
        for token in expired:
            del self._sessions[token]
