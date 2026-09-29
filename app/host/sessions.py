"""Session Authority, Credential Hashing, Rate-Limiting, and Token Revocation.

Description:
    This module provides cryptographic operator authentication, bearer token
    issuance, rate-limiting, and revocation management for the HaruQuantAI host.
    It exists to prevent unauthorized remote execution, protect against brute-force
    credential attacks, isolate ephemeral signing keys in process memory, and
    maintain durable session states across SQLite storage. Externally, it
    participates in three key workflows: (1) `BootstrapCoordinator` provisions
    default credentials and verifies operator configuration during host
    initialization (`_database`); (2) The ASGI transport layer (`app.host.transport`)
    invokes `SessionManager.verify()` within `request_guard()` and `socket_endpoint`
    to protect HTTP routes and WebSocket channels; and (3) Authentication routes
    (`/api/v1/auth/login`, `/logout`) call `login()` to generate HMAC-signed bearer
    tokens and `revoke()` to durably invalidate active sessions. Internally,
    PBKDF2-HMAC-SHA256 helpers (`hash_password`, `verify_credentials`) manage salted
    credentials; `sign()` and `token_hash()` generate tamper-evident bearer tokens
    without storing raw credentials; and `SessionManager` enforces a 60-second
    sliding-window retry limit per network peer.

Purpose:
    FEAT-HOST-SESSION: Operator Authentication, Ephemeral Tokens, and Revocation.
    Provides salted PBKDF2 credential verification, HMAC-signed bearer token
    issuance, sliding-window rate limiting, and durable SQLite token revocation.

Key Capabilities:
    - FR-HOST-SESSION-CREDENTIAL-VERIFICATION: Salted PBKDF2 Password Hashing
      Associated: `hash_password()`, `verify_password()`, `verify_credentials()`
      Logging: Emits warning log on invalid credential presentation during
      authentication attempts.
    - FR-HOST-SESSION-TOKEN-ISSUANCE: Ephemeral HMAC Bearer Token Generation
      Associated: `SessionManager.login()`, `sign()`, `token_hash()`
      Logging: Emits info log when client authenticates and bearer token is
      successfully issued.
    - FR-HOST-SESSION-RATE-LIMITING: Sliding-Window Per-Peer Retry Throttling
      Associated: `SessionManager.login()`
      Logging: Emits warning log when a peer exceeds max authentication
      attempts (5 within 60s).
    - FR-HOST-SESSION-TOKEN-VERIFICATION: Signature & Persistence Validation
      Associated: `SessionManager.verify()`
      Logging: Emits debug log on session verification and failed token
      resolution.
    - FR-HOST-SESSION-DURABLE-REVOCATION: Immediate Database Token Revocation
      Associated: `SessionManager.revoke()`
      Logging: Emits info log when session token is durably revoked in the
      auth store.

Python API Usage:
    ```python
    from app.host.sessions import SessionManager
    from app.host.settings import HostSettings

    # 1. Initialize session authority with host settings
    settings = HostSettings()
    manager = SessionManager(settings)

    # 2. Authenticate credentials from a network peer
    token = manager.login("haruquantai", "password123", peer="127.0.0.1")

    # 3. Verify bearer token on incoming requests
    session = manager.verify(token)
    if session is not None:
        user = session.username

    # 4. Invalidate session token on logout
    manager.revoke(token)
    ```

CLI Usage:
    Session credentials and schema initialization are configured via CLI
    flags:
    ```bash
    # Supply operator password at server launch
    uv run python -m app.main --password "secret"

    # Pre-migrate authentication schema in isolated database
    uv run python -m app.main --migrate-auth-schema --data-dir ./data
    ```
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import secrets
import time
from collections import OrderedDict
from dataclasses import dataclass

from app.host.logging import get_logger
from app.host.settings import HostSettings
from app.persistence.host import AuthStore

logger = get_logger(__name__)
RETRY_WINDOW = 60
MAX_PEERS = 1024
MAX_ATTEMPTS = 5
MAX_TOKEN_LENGTH = 256


def is_loopback(host: str) -> bool:
    """Recognize a literal IPv4 or IPv6 loopback address.

    Args:
        host: Peer or bind address; DNS names and forwarding headers are not resolved.

    Returns:
        True for loopback literals; False for invalid addresses or hostnames.
    """
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def hash_password(password: str) -> str:
    """Create a password verifier with a fresh 32-byte random salt.

    Uses 600,000 PBKDF2-HMAC-SHA256 iterations. This CPU-bound operation does
    not store or log the password; callers own persistence and scheduling.

    Args:
        password: Plaintext password, encoded as UTF-8 without normalization.

    Returns:
        Hex salt and hex digest separated by a colon.
    """
    salt = secrets.token_bytes(32)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600000)
    return salt.hex() + ":" + digest.hex()


def hash_credentials(
    password: str, salt: str | None = None, iterations: int = 100000
) -> tuple[str, str]:
    """Create a password verifier and salt for user.access persistence.

    Uses PBKDF2-HMAC-SHA256 with 100,000 iterations by default.

    Args:
        password: Plaintext password.
        salt: Optional hexadecimal salt; generated randomly if None.
        iterations: Number of PBKDF2 iterations.

    Returns:
        Tuple of (hex_digest, hex_salt).
    """
    effective_salt = salt if salt is not None else secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(effective_salt), iterations
    )
    return digest.hex(), effective_salt


def verify_credentials(
    password: str,
    stored_hash: str,
    stored_salt: str,
) -> bool:
    """Verify candidate password against stored user.access hash and salt.

    Supports both 100,000 and 600,000 iteration counts for compatibility.

    Args:
        password: Candidate plaintext password.
        stored_hash: Hexadecimal hash stored in user.access.
        stored_salt: Hexadecimal salt stored in user.access.

    Returns:
        True if matching, False for mismatch or malformed inputs.
    """
    try:
        salt_bytes = bytes.fromhex(stored_salt)
        for iters in (100000, 600000):
            digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt_bytes, iters)
            if hmac.compare_digest(digest.hex(), stored_hash):
                return True
        return False
    except ValueError, TypeError:
        return False


def verify_password(password: str, stored: str) -> bool:
    """Recompute and compare a stored PBKDF2 password verifier.

    Digest comparison uses compare_digest. The expensive derivation is synchronous;
    callers must apply their own request limits.

    Args:
        password: Candidate plaintext password.
        stored: Colon-separated hex salt and digest from hash_password.

    Returns:
        Whether the digest matches; malformed verifier encodings return False.
    """
    try:
        salt, expected = stored.split(":")
        return verify_credentials(password, expected, salt)
    except ValueError:
        return False


def token_hash(token: str) -> str:
    """Produce the database lookup key for a bearer token.

    Args:
        token: Complete bearer credential, including its signature.

    Returns:
        SHA-256 hexadecimal digest; token validity is not checked here.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def sign(message: str, key: bytes) -> str:
    """Compute a message authentication code with an injected secret.

    Args:
        message: Opaque token identifier encoded as UTF-8.
        key: Process-owned signing bytes; never persisted by this helper.

    Returns:
        Hexadecimal HMAC-SHA256 signature.
    """
    return hmac.new(key, message.encode(), "sha256").hexdigest()


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
        exists, stored = self.store.credential("haruquantai")
        if not exists:
            self.store.provision(
                "haruquantai", hash_password(configured) if configured else None
            )
        elif configured is not None and (
            stored is None or not verify_password(configured, stored)
        ):
            raise SessionError("Configured credentials differ from stored operator")
        if not is_loopback(settings.host) and stored is None and exists:
            raise SessionError("Remote host requires a protected operator")
        logger.info("Session authority initialized")

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
            logger.warning("Authentication retry limit reached")
            raise SessionError("Retry limit")
        exists, stored = self.store.credential(username)
        local = is_loopback(self.settings.host) and is_loopback(peer)
        valid = exists and (
            (stored is None and local)
            or (stored is not None and verify_password(password or "", stored))
        )
        if not valid:
            logger.warning("Authentication rejected")
            raise SessionError("Invalid credentials or retry limit")
        self._attempts.pop(peer, None)
        identifier = secrets.token_urlsafe(32)
        token = identifier + "." + sign(identifier, self._key)
        self.store.issue(
            token_hash(token), username, now, now + self.settings.session_seconds
        )
        logger.info("Client authenticated")
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
        if username is None:
            logger.debug("Session token verification failed")
            return None
        logger.debug("Session verified: username=%s", username)
        return Session(username, hashed)

    def revoke(self, token: str) -> None:
        """Persist revocation for the supplied bearer credential.

        Does not require a valid signature. Missing token hashes are a no-op; database
        errors propagate. The session row is retained.

        Args:
            token: Full credential to hash before updating storage.
        """
        self.store.revoke(token_hash(token))
        logger.info("Session revoked")
