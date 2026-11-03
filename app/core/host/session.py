"""Host session authority, credential verification, and OS vault storage.

Description:
    Manages persistent UI/CLI session lifecycles, PBKDF2 password hashing,
    token validation, capability grants, and OS-level secret vault storage
    via Windows Credential Manager (Advapi32). Enforces constant-time
    credential checks, sliding session expiration, and atomic credential
    staging and rollback for broker/exchange connection configurations.

Purpose:
    FEAT-HOST-SESSION: Unified host session authentication, authorization,
    and credential vault storage.

Key Capabilities:
    - FR-HOST-SESSION-LIFECYCLE: Session tokens (create_session -> INFO).
    - FR-HOST-SESSION-CREDENTIALS: PBKDF2 hashing (hash_password -> DEBUG).
    - FR-HOST-SESSION-AUTHORIZATION: Capability scopes (authorize -> DEBUG).
    - FR-HOST-SESSION-REVOCATION: Idempotent session logout (revoke_session -> INFO).
    - FR-HOST-VAULT-STORAGE: Windows Credential Vault (store -> INFO).
    - FR-HOST-VAULT-PREPARE-CREDENTIALS: Secret staging (prepare_credentials -> INFO).
    - FR-HOST-VAULT-ENDPOINT-VALIDATION: Endpoint URL validation (_endpoint -> DEBUG).

Python API Usage:
    ```python
    from app.core.host.session import SessionManager, WindowsCredentialVault

    sessions = SessionManager()
    vault = WindowsCredentialVault()
    ```

CLI Usage:
    ```bash
    uv run python -m app.cli login --username admin
    uv run python -m app.cli logout
    ```
"""

from __future__ import annotations

import ctypes
import hashlib
import hmac
import os
import re
import secrets
import uuid
from collections.abc import Callable, Iterable, Mapping
from ctypes import wintypes
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, Protocol
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field

from app.core.host.logging import get_logger
from app.core.host.persistence import HostPersistence

logger = get_logger(__name__)

_ITERATIONS = 600_000
_LEGACY_ITERATIONS = 100_000
_LEGACY_SALT_LENGTH = 32
_MAX_ITERATIONS = 2_000_000
_KEY_BYTES = 32
_HEX_LENGTH = 64
_TOKEN = re.compile(r"[0-9a-f]{64}\Z")
_SCOPE = re.compile(r"(?:[a-zA-Z0-9_.-]+|\*):(?:[a-zA-Z0-9_.-]+|\*)\Z")
_HOST_INSTANCE_ID = secrets.token_hex(16)
_MAX_CREDENTIAL_BYTES = 2400
_ERROR_NOT_FOUND = 1168


class SessionPersistenceError(RuntimeError):
    """The persistence gateway rejected an operation; access must fail closed."""


@dataclass(frozen=True, slots=True)
class Session:
    """Validated session identity, without the bearer token or its digest."""

    session_id: str
    username: str
    peer_id: str
    created_at_utc: datetime
    expires_at_utc: datetime


def _data(response: Mapping[str, Any]) -> dict[str, Any]:
    if not response["success"]:
        logger.error("Session persistence operation failed")
        raise SessionPersistenceError("Session persistence operation failed")
    data: dict[str, Any] = response["data"]
    return data


def _now() -> datetime:
    return datetime.now(UTC)


def _identity(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("A non-empty identity is required")


class SessionManager:
    """Manage sessions through the existing host_session schema.

    create_session is a trusted API: call it only after credential verification.
    peer_id identifies the client channel: CLI uses "cli"; UI callers should use
    "ui:<stable-browser-id>" to retain browser binding and identify the channel.
    Possession of a peer_id alone never authenticates a request.
    host_instance_id identifies this running process for diagnostics only; it
    deliberately does not invalidate persisted browser sessions on restart.
    Invalid credentials/tokens return False/None; storage failures raise.
    """

    def __init__(
        self,
        persistence: HostPersistence | None = None,
        *,
        scope_resolver: Callable[[str], Iterable[str]] | None = None,
        clock: Callable[[], datetime] = _now,
    ) -> None:
        self.persistence = persistence if persistence is not None else HostPersistence()
        self.host_instance_id = _HOST_INSTANCE_ID
        self._scope_resolver = scope_resolver
        self._clock = clock
        logger.debug(
            "Session manager initialized; host_instance_id=%s", self.host_instance_id
        )

    @staticmethod
    def hash_password(password: str) -> str:
        """Encode PBKDF2-HMAC-SHA256 with a fresh 256-bit random salt."""
        _identity(password)
        salt = secrets.token_bytes(32)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
        logger.debug("Password hash generated; algorithm=pbkdf2_sha256")
        return f"pbkdf2_sha256${_ITERATIONS}${salt.hex()}${digest.hex()}"

    @staticmethod
    def verify_password(password: object, password_hash: object) -> bool:
        """Verify current and legacy salt$hash encodings in constant time.

        Legacy records use a 16-byte hex salt encoded as UTF-8 KDF input and
        100,000 iterations. New records decode their hex salt to raw bytes.
        Only hash_password emits new hashes, always using the current format.
        """
        if not isinstance(password, str) or not isinstance(password_hash, str):
            return False
        try:
            if password_hash.count("$") == 1:
                return SessionManager._verify_legacy_password(password, password_hash)
            algorithm, raw_iterations, raw_salt, raw_digest = password_hash.split("$")
            iterations = int(raw_iterations)
            if (
                algorithm != "pbkdf2_sha256"
                or not 1 <= iterations <= _MAX_ITERATIONS
                or len(raw_salt) != _HEX_LENGTH
                or len(raw_digest) != _HEX_LENGTH
            ):
                return False
            salt, expected = bytes.fromhex(raw_salt), bytes.fromhex(raw_digest)
            if len(salt) != _KEY_BYTES or len(expected) != _KEY_BYTES:
                return False
            actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
            return hmac.compare_digest(actual, expected)
        except ValueError, OverflowError:
            return False

    @staticmethod
    def _verify_legacy_password(password: str, password_hash: str) -> bool:
        raw_salt, raw_digest = password_hash.split("$")
        if (
            len(raw_salt) != _LEGACY_SALT_LENGTH
            or len(raw_digest) != _HEX_LENGTH
            or not all(
                char in "0123456789abcdefABCDEF" for char in raw_salt + raw_digest
            )
        ):
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), raw_salt.encode(), _LEGACY_ITERATIONS
        )
        return hmac.compare_digest(actual, bytes.fromhex(raw_digest))

    @staticmethod
    def verify_credentials(
        username: str, password: str, *, expected_username: str, password_hash: str
    ) -> bool:
        """Check a configured identity and password without short-circuiting KDF."""
        password_valid = SessionManager.verify_password(password, password_hash)
        valid = (
            isinstance(username, str)
            and isinstance(expected_username, str)
            and hmac.compare_digest(username.encode(), expected_username.encode())
            and password_valid
        )
        if valid:
            logger.info("Credential verification succeeded")
        else:
            logger.warning("Credential verification failed")
        return valid

    def _timestamp(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Session clock must return an aware UTC timestamp")
        return value.astimezone(UTC)

    def create_session(self, username: str, peer_id: str) -> str:
        """Persist a digest and return the sole copy of a new 64-character token."""
        _identity(username)
        _identity(peer_id)
        token = secrets.token_hex(32)
        session_id = secrets.token_hex(16)
        now = self._timestamp()
        _data(
            self.persistence.create_records(
                "host_session",
                {
                    "session_id": session_id,
                    "token_hash": hashlib.sha256(token.encode()).hexdigest(),
                    "username": username,
                    "peer_id": peer_id,
                    "created_at_utc": now.isoformat(),
                    "expires_at_utc": (now + timedelta(hours=24)).isoformat(),
                    "revoked_at_utc": None,
                    "status": "active",
                },
            )
        )
        logger.info("Session created; session_id=%s", session_id)
        return token

    def validate_session(self, token: str, peer_id: str) -> Session | None:  # noqa: PLR0911
        """Validate and slide expiry atomically with respect to logout.

        Expired rows are marked expired on access. Malformed persisted timestamps
        fail closed. A different browser cannot refresh or revoke this session.
        """
        if not isinstance(token, str) or not _TOKEN.fullmatch(token):
            logger.warning("Session validation denied; reason=malformed_token")
            return None
        if not isinstance(peer_id, str) or not peer_id:
            logger.warning("Session validation denied; reason=missing_peer")
            return None
        digest = hashlib.sha256(token.encode()).hexdigest()
        with self.persistence.transaction() as tx:
            rows = _data(
                tx.read_records("host_session", filters={"token_hash": digest})
            )["records"]
            if not rows:
                logger.warning("Session validation denied; reason=unknown_token")
                return None
            row = rows[0]
            if (
                row["status"] != "active"
                or row["revoked_at_utc"] is not None
                or not hmac.compare_digest(row["peer_id"].encode(), peer_id.encode())
            ):
                logger.warning(
                    "Session validation denied; reason=inactive_or_peer_mismatch"
                )
                return None
            try:
                created = datetime.fromisoformat(row["created_at_utc"])
                expires = datetime.fromisoformat(row["expires_at_utc"])
                if created.utcoffset() is None or expires.utcoffset() is None:
                    logger.error(
                        "Session validation denied; reason=naive_stored_timestamp"
                    )
                    return None
            except ValueError, TypeError:
                # Tracebacks may contain sensitive persisted values.
                logger.error(  # noqa: TRY400
                    "Session validation denied; reason=invalid_stored_timestamp"
                )
                return None
            now = self._timestamp()
            if expires <= now:
                logger.info(
                    "Session expiration detected; session_id=%s", row["session_id"]
                )
                _data(
                    tx.update_record(
                        "host_session",
                        {"status": "expired"},
                        filters={"session_id": row["session_id"]},
                    )
                )
                return None
            expires = max(expires, now + timedelta(hours=24))
            _data(
                tx.update_record(
                    "host_session",
                    {"expires_at_utc": expires.isoformat()},
                    filters={"session_id": row["session_id"]},
                )
            )
            session = Session(
                row["session_id"], row["username"], row["peer_id"], created, expires
            )
        logger.debug(
            "Session validated and expiry refreshed; session_id=%s", session.session_id
        )
        return session

    def resolve_peer(self, token: str) -> str | None:
        """Resolve the peer identifier bound to a token if valid and active."""
        if not isinstance(token, str) or not _TOKEN.fullmatch(token):
            return None
        digest = hashlib.sha256(token.encode()).hexdigest()
        try:
            records = _data(
                self.persistence.read_records(
                    "host_session", filters={"token_hash": digest}
                )
            ).get("records", [])
            if (
                records
                and records[0].get("status") == "active"
                and records[0].get("revoked_at_utc") is None
            ):
                peer = records[0].get("peer_id")
                return str(peer) if isinstance(peer, str) and peer else None
        except SessionPersistenceError, KeyError, ValueError:
            return None
        return None

    def revoke_session(self, token: str, peer_id: str) -> bool:
        """Log out a browser permanently; repeated logout is idempotent."""
        if not isinstance(token, str) or not _TOKEN.fullmatch(token):
            logger.warning("Session revocation denied; reason=malformed_token")
            return False
        if not isinstance(peer_id, str) or not peer_id:
            logger.warning("Session revocation denied; reason=missing_peer")
            return False
        filters = {
            "token_hash": hashlib.sha256(token.encode()).hexdigest(),
            "peer_id": peer_id,
        }
        with self.persistence.transaction() as tx:
            rows = _data(tx.read_records("host_session", filters=filters))["records"]
            if not rows:
                logger.warning(
                    "Session revocation denied; reason=unknown_token_or_peer"
                )
                return False
            revoked = rows[0]["revoked_at_utc"] is None
            if revoked:
                _data(
                    tx.update_record(
                        "host_session",
                        {
                            "status": "revoked",
                            "revoked_at_utc": self._timestamp().isoformat(),
                        },
                        filters=filters,
                    )
                )
        if revoked:
            logger.info("Session revoked; session_id=%s", rows[0]["session_id"])
        else:
            logger.debug(
                "Session already revoked; session_id=%s", rows[0]["session_id"]
            )
        return True

    @staticmethod
    def has_scope(grants: Iterable[str], required_scope: str) -> bool:
        """Match exact domain:action or explicit component wildcards; deny default."""
        if (
            not isinstance(required_scope, str)
            or not _SCOPE.fullmatch(required_scope)
            or "*" in required_scope
            or isinstance(grants, str)
        ):
            return False
        domain, action = required_scope.split(":")
        allowed = {required_scope, f"{domain}:*", f"*:{action}", "*:*"}
        return any(isinstance(grant, str) and grant in allowed for grant in grants)

    def authorize(self, token: str, peer_id: str, required_scope: str) -> bool:
        """Validate the session and check current trusted grants for its identity."""
        session = self.validate_session(token, peer_id)
        if session is None or self._scope_resolver is None:
            logger.warning(
                "Authorization denied; reason=invalid_session_or_missing_resolver"
            )
            return False
        allowed = self.has_scope(self._scope_resolver(session.username), required_scope)
        if allowed:
            logger.debug("Authorization granted; session_id=%s", session.session_id)
        else:
            logger.warning(
                "Authorization denied; reason=insufficient_scope; session_id=%s",
                session.session_id,
            )
        return allowed


class _Credential(ctypes.Structure):
    _fields_ = [  # type: ignore[mutable-override]
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


class WindowsCredentialVault:
    """Store secrets in the current Windows user's OS-protected credential store."""

    def __init__(self) -> None:
        self._api = (
            ctypes.WinDLL("Advapi32.dll", use_last_error=True)
            if os.name == "nt"
            else None
        )
        if self._api:
            self._api.CredWriteW.argtypes = [
                ctypes.POINTER(_Credential),
                wintypes.DWORD,
            ]
            self._api.CredWriteW.restype = wintypes.BOOL
            self._api.CredReadW.argtypes = [
                wintypes.LPCWSTR,
                wintypes.DWORD,
                wintypes.DWORD,
                ctypes.POINTER(ctypes.POINTER(_Credential)),
            ]
            self._api.CredReadW.restype = wintypes.BOOL
            self._api.CredDeleteW.argtypes = [
                wintypes.LPCWSTR,
                wintypes.DWORD,
                wintypes.DWORD,
            ]
            self._api.CredDeleteW.restype = wintypes.BOOL
            self._api.CredFree.argtypes = [ctypes.c_void_p]

    def store(self, secret: str) -> str:
        """Write a new owned credential; never overwrite another reference."""
        if not self._api:
            raise OSError("The OS credential vault is unavailable")
        if (
            not isinstance(secret, str)
            or not secret
            or len(secret.encode()) > _MAX_CREDENTIAL_BYTES
        ):
            raise ValueError("Supply a nonempty credential up to 2400 bytes")
        reference = "HaruQuantAI/" + uuid.uuid4().hex
        raw = secret.encode("utf-8")
        buffer = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
        credential = _Credential(
            Type=1,
            TargetName=reference,
            CredentialBlobSize=len(raw),
            CredentialBlob=buffer,
            Persist=2,
            UserName="HaruQuantAI",
        )
        if not self._api.CredWriteW(ctypes.byref(credential), 0):
            raise OSError("Unable to store the OS credential")
        logger.debug("FR-HOST-VAULT-STORAGE: stored credential ref=%s", reference)
        return reference

    def resolve(self, reference: str) -> str:
        """Read only references owned by this application's credential namespace."""
        if not self._api or not reference.startswith("HaruQuantAI/"):
            raise OSError("Credential vault or reference is unavailable")
        credential = ctypes.POINTER(_Credential)()
        if not self._api.CredReadW(reference, 1, 0, ctypes.byref(credential)):
            raise OSError("Credential reference is unavailable")
        try:
            value = credential.contents
            return ctypes.string_at(
                value.CredentialBlob, value.CredentialBlobSize
            ).decode("utf-8")
        finally:
            self._api.CredFree(credential)

    def revoke(self, reference: str) -> None:
        """Delete one owned credential; an already deleted reference is successful."""
        if not self._api or not reference.startswith("HaruQuantAI/"):
            raise OSError("Credential vault or reference is unavailable")
        if (
            not self._api.CredDeleteW(reference, 1, 0)
            and ctypes.get_last_error() != _ERROR_NOT_FOUND
        ):
            raise OSError("Unable to revoke the OS credential")
        logger.debug("FR-HOST-VAULT-STORAGE: revoked credential ref=%s", reference)


class Vault(Protocol):
    """Injected secret store; revoke must be idempotent and refs independently owned."""

    def store(self, secret: str) -> str:
        """Store a credential and return an opaque owned reference."""
        ...

    def resolve(self, reference: str) -> str:
        """Resolve one opaque reference without logging its secret."""
        ...

    def revoke(self, reference: str) -> None:
        """Permanently revoke a reference; repeated revocation must succeed."""
        ...


class ConnectionMetadata(BaseModel):
    """Allowlisted public connection fields; inline credentials cannot be saved."""

    model_config = ConfigDict(extra="forbid", strict=True)
    connection_id: str = Field(
        default_factory=lambda: secrets.token_hex(16), min_length=1, max_length=128
    )
    name: str = Field(min_length=1, max_length=200)
    provider: str = Field(min_length=1, max_length=100)
    kind: Literal["broker", "exchange"] = "broker"
    endpoint: str
    vault_refs: dict[str, str] = Field(default_factory=dict)


def prepare_credentials(  # noqa: C901 - secret staging and rollback share one scope
    vault: Vault | None, values: dict[str, Any]
) -> tuple[ConnectionMetadata, list[str]]:
    """Stage and validate owned secrets without exposing plaintext in metadata."""
    from app.core.host.transport import TransportError
    from app.core.lib.responses import ErrorCode

    credentials = values.pop("credentials", {})
    if not isinstance(credentials, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in credentials.items()
    ):
        raise ValueError("Credentials must contain string fields")
    staged: list[str] = []
    try:
        if credentials:
            if vault is None or not callable(getattr(vault, "store", None)):
                raise TransportError(  # noqa: TRY301 - enclosing scope owns rollback
                    ErrorCode.UNAVAILABLE, "Credential vault is not configured"
                )
            refs = dict(values.get("vault_refs") or {})
            for name, secret in credentials.items():
                if secret:
                    reference = vault.store(secret)
                    refs[name] = reference
                    staged.append(reference)
                else:
                    refs.pop(name, None)
            values["vault_refs"] = refs
        record = ConnectionMetadata.model_validate(values)
        _endpoint(record.endpoint)
        if vault is not None:
            for reference in record.vault_refs.values():
                vault.resolve(reference)
        elif record.vault_refs:
            raise TransportError(  # noqa: TRY301 - enclosing scope owns rollback
                ErrorCode.UNAVAILABLE, "Credential vault is not configured"
            )
        logger.info(
            "FR-HOST-VAULT-PREPARE-CREDENTIALS: credentials staged successfully"
        )
        return record, staged
    except BaseException:
        if vault is not None:
            for reference in staged:
                vault.revoke(reference)
        raise


def _endpoint(endpoint: str) -> tuple[str, int]:
    p = urlsplit(endpoint)
    bad = (
        p.scheme not in {"http", "https"}
        or not p.hostname
        or p.username is not None
        or p.password is not None
        or p.query
        or p.fragment
    )
    if bad:
        raise ValueError("Invalid endpoint URL")
    return p.hostname or "127.0.0.1", p.port or (443 if p.scheme == "https" else 80)
