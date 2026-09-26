"""Session authority combining process signatures and durable revocation.

SessionManager owns a fresh process key and bounded per-peer retry accounting.
AuthStore owns database reads/writes; plaintext bearer credentials are returned
to clients but only their hashes are persisted. Restarting changes the signing
key and invalidates old tokens. Construction can provision an absent operator,
so callers must initialize the schema and explicitly schedule this I/O.
"""

import hmac
import secrets
import time
from collections import OrderedDict
from dataclasses import dataclass

from app.host.config import HostSettings
from app.host.logging import get_logger
from app.host.security import (
    hash_password,
    is_loopback,
    sign,
    token_hash,
    verify_password,
)
from app.persistence.host import AuthStore

logger = get_logger(__name__)
RETRY_WINDOW = 60
MAX_PEERS = 1024
MAX_ATTEMPTS = 5
MAX_TOKEN_LENGTH = 256


class SessionError(ValueError):
    """Authentication failed without disclosing the reason to the caller."""


@dataclass(frozen=True)
class Session:
    """Authenticated username paired with an internal hashed token key.

    key is used for per-session readiness tracking and is not a bearer credential.
    The frozen record is returned only after signature and durable validity checks.
    """

    username: str
    key: str


class SessionManager:
    """Own runtime signing authority, finite retries and persistent session state."""

    def __init__(self, settings: HostSettings) -> None:
        """Create process signing state and validate or provision the operator.

        Reads persistent credentials and inserts the operator only when absent. Password
        derivation and database access are synchronous; bootstrap runs construction in
        a worker thread. SQLite failures propagate; no schema migration is attempted.

        Args:
            settings: Validated runtime settings pointing to a prepared auth database.

        Raises:
            SessionError: Configured credentials conflict with storage or remote binding
                has an unprotected existing operator.
        """
        self.settings = settings
        self.store = AuthStore(settings.database_path)
        self._key = secrets.token_bytes(32)
        self._attempts: OrderedDict[str, tuple[float, int]] = OrderedDict()
        configured = settings.password.get_secret_value() if settings.password else None
        exists, stored = self.store.credential("operator")
        if not exists:
            self.store.provision(
                "operator", hash_password(configured) if configured else None
            )
        elif configured is not None and (
            stored is None or not verify_password(configured, stored)
        ):
            raise SessionError("Configured credentials differ from stored operator")
        if not is_loopback(settings.host) and stored is None and exists:
            raise SessionError("Remote host requires a protected operator")
        logger.info("B10 Session authority initialized")

    def login(self, username: str, password: str | None, *, peer: str) -> str:
        """Authenticate credentials and persist a signed token hash.

        Every attempt counts within the 60-second window; success clears that peer.
        Passwordless login requires both bind and peer addresses to be loopback. The
        session expiry uses Unix seconds and the configured lifetime; storage errors
        propagate without returning a token.

        Args:
            username: Stored identity to authenticate.
            password: Candidate plaintext password, or None for eligible local
                auto-login.
            peer: Literal transport peer address used for retry accounting and loopback
                checks.

        Returns:
            Opaque bearer token; callers must not put it in logs or URLs.

        Raises:
            SessionError: Credentials fail or the peer has exhausted the retry window.
        """
        now = time.time()
        since, count = self._attempts.get(peer, (now, 0))
        count = 0 if now - since >= RETRY_WINDOW else count
        self._attempts[peer] = (now if count == 0 else since, count + 1)
        self._attempts.move_to_end(peer)
        if len(self._attempts) > MAX_PEERS:
            self._attempts.popitem(last=False)
        if count >= MAX_ATTEMPTS:
            logger.warning("B10 Authentication retry limit reached")
            raise SessionError("Retry limit")
        exists, stored = self.store.credential(username)
        local = is_loopback(self.settings.host) and is_loopback(peer)
        valid = exists and (
            (stored is None and local)
            or (stored is not None and verify_password(password or "", stored))
        )
        if not valid:
            logger.warning("B10 Authentication rejected")
            raise SessionError("Invalid credentials or retry limit")
        self._attempts.pop(peer, None)
        identifier = secrets.token_urlsafe(32)
        token = identifier + "." + sign(identifier, self._key)
        self.store.issue(
            token_hash(token), username, now, now + self.settings.session_seconds
        )
        logger.info("B10 Client authenticated")
        return token

    def verify(self, token: str) -> Session | None:
        """Check token shape, process signature, expiry, and revocation.

        A valid signature alone grants no authority: storage must also contain a live,
        unrevoked record. Database errors propagate rather than authorizing the client.

        Args:
            token: Full bearer credential supplied by a client.

        Returns:
            Session containing username and hashed token key, or None when verification
            fails.
        """
        if len(token) > MAX_TOKEN_LENGTH or token.count(".") != 1:
            return None
        identifier, signature = token.split(".")
        if not hmac.compare_digest(sign(identifier, self._key), signature):
            return None
        hashed = token_hash(token)
        username = self.store.valid(hashed, time.time())
        return None if username is None else Session(username, hashed)

    def revoke(self, token: str) -> None:
        """Persist revocation for the supplied bearer credential.

        Does not require a valid signature. Missing token hashes are a no-op; database
        errors propagate. The session row is retained.

        Args:
            token: Full credential to hash before updating storage.
        """
        self.store.revoke(token_hash(token))
