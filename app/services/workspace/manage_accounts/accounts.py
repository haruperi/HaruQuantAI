"""Account, scoped-session, and current-identity verification service."""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Final

from app.composition.logging import get_logger
from app.contracts.common.models import ProblemDetails
from app.contracts.workspace.errors import (
    WorkspaceFailure,
    WorkspaceFailureCode,
    WorkspaceStorageError,
)
from app.contracts.workspace.models import (
    AccountRecord,
    ManageAccountsRequest,
    ManageAccountsSuccess,
)
from app.services.workspace.manage_accounts._persistence import (
    AccountPersistence,
    SafeSessionAuditRecord,
)
from app.services.workspace.manage_accounts.config import ManageAccountsConfig

if TYPE_CHECKING:
    from app.contracts.workspace.persistence import PersistenceCapability

logger = get_logger(__name__)

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


def _system_utc_now() -> datetime:
    """Return the current aware UTC time."""
    return datetime.now(UTC)


def _format_timestamp(value: datetime) -> str:
    """Format an aware instant as the canonical UTC timestamp.

    Returns:
        Canonical UTC timestamp string.
    """
    return value.astimezone(UTC).strftime(_TIMESTAMP_FORMAT)


def _parse_timestamp(value: object) -> datetime | None:
    """Parse a stored timestamp.

    Returns:
        Aware UTC datetime, or None for invalid values.
    """
    try:
        parsed = datetime.fromisoformat(str(value))
    except TypeError, ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _digest(token: str) -> str:
    """Return the storage-only SHA-256 digest for one opaque token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    """Hash one password using a versioned standard-library scrypt record.

    Args:
        password: Plaintext password to hash.

    Returns:
        Encoded password hash string.

    Raises:
        ValueError: If password is empty.
    """
    if not password:
        raise ValueError("Password must not be empty")
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
    """Verify a password candidate against a versioned scrypt record.

    Args:
        password: Plaintext password candidate.
        stored_hash: Stored encoded scrypt record.

    Returns:
        Whether the password matches.
    """
    if not password or not stored_hash or stored_hash == "disabled":
        return False
    try:
        parts = stored_hash.split("$")
        if len(parts) != _EXPECTED_HASH_PARTS or parts[0] != _ALGORITHM:
            return False
        _, n_text, r_text, p_text, salt_text, digest_text = parts
        expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=base64.urlsafe_b64decode(salt_text.encode("ascii")),
            n=int(n_text),
            r=int(r_text),
            p=int(p_text),
            maxmem=_MAX_MEMORY_BYTES,
            dklen=len(expected),
        )
        return hmac.compare_digest(actual, expected)
    except TypeError, ValueError:
        return False


def _failure(
    request: ManageAccountsRequest,
    *,
    code: WorkspaceFailureCode,
    title: str,
    status: int,
    detail: str,
) -> WorkspaceFailure:
    """Build one bounded Workspace failure envelope.

    Returns:
        Structured failure containing no credential material.
    """
    return WorkspaceFailure(
        request_id=request.request_id,
        code=code,
        problem=ProblemDetails(
            title=title,
            status=status,
            code=code,
            detail=detail,
        ),
    )


def _registration_failure(
    request: ManageAccountsRequest,
    detail: str,
) -> WorkspaceFailure:
    return _failure(
        request,
        code="ACCOUNT_REGISTRATION_FAILED",
        title="Registration failed",
        status=400,
        detail=detail,
    )


def _authentication_failure(
    request: ManageAccountsRequest,
    detail: str = "Session or account scope is not valid",
) -> WorkspaceFailure:
    return _failure(
        request,
        code="ACCOUNT_AUTHENTICATION_FAILED",
        title="Authentication failed",
        status=401,
        detail=detail,
    )


class AccountService:
    """Manage accounts and revalidate bounded current-session identity."""

    def __init__(
        self,
        persistence: PersistenceCapability,
        config: ManageAccountsConfig | None = None,
        *,
        clock: Callable[[], datetime] = _system_utc_now,
    ) -> None:
        """Initialize the account service over bounded Workspace persistence.

        Args:
            persistence: Active `workspace.persistence@1` provider.
            config: Validated feature configuration.
            clock: Aware UTC clock; injectable for deterministic expiry tests.
        """
        self._config = config or ManageAccountsConfig()
        self._clock = clock
        self._store = AccountPersistence(persistence, self._config.workspace_path)
        self._closed = False

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            raise ValueError("account clock must return an aware datetime")
        return value.astimezone(UTC)

    def _new_session(self) -> tuple[str, str, str, str, str]:
        now = self._now()
        session_token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        audit_ref = f"auth_{secrets.token_hex(12)}"
        return (
            session_token,
            csrf_token,
            audit_ref,
            _format_timestamp(now),
            _format_timestamp(now + timedelta(days=_SESSION_TTL_DAYS)),
        )

    async def manage_accounts(
        self,
        request: ManageAccountsRequest,
    ) -> ManageAccountsSuccess | WorkspaceFailure:
        """Serve one account operation and log only bounded safe metadata.

        Args:
            request: REGISTER, LOGIN, ME, or LOGOUT request.

        Returns:
            Typed success or bounded failure.
        """
        logger.debug(
            "Account request admitted",
            event="workspace.accounts.request.admitted",
            operation=request.operation,
            request_id=request.request_id,
        )
        if self._closed:
            result: ManageAccountsSuccess | WorkspaceFailure = _failure(
                request,
                code="CAPABILITY_UNAVAILABLE",
                title="Account capability unavailable",
                status=503,
                detail="The account capability is disposed",
            )
        elif request.operation == "REGISTER":
            result = self._register(request)
        elif request.operation == "LOGIN":
            result = self._login(request)
        elif request.operation == "ME":
            result = self._resolve_session(request)
        else:
            result = self._logout(request)
        if isinstance(result, WorkspaceFailure):
            logger.warning(
                "Account request denied",
                event="workspace.accounts.request.denied",
                operation=request.operation,
                request_id=request.request_id,
                error_code=result.code,
            )
        else:
            logger.info(
                "Account request completed",
                event="workspace.accounts.request.completed",
                operation=request.operation,
                request_id=request.request_id,
            )
        return result

    def _register(
        self,
        request: ManageAccountsRequest,
    ) -> ManageAccountsSuccess | WorkspaceFailure:
        username = (request.username or "").strip()
        password = request.password or ""
        if not _USERNAME_PATTERN.fullmatch(username):
            return _registration_failure(
                request,
                "Username must be 3-64 alphanumeric, underscore, hyphen, "
                "or dot characters",
            )
        if len(password) < _MIN_PASSWORD_LEN:
            return _registration_failure(
                request,
                "Password must be at least 6 characters",
            )
        if self._store.username_exists(
            request_id=request.request_id,
            username=username,
            account_id=request.account_id,
        ):
            return _registration_failure(request, "Username is already taken")
        profile = (
            request.runtime_profile
            if request.runtime_profile in _RUNTIME_PROFILES
            else "research"
        )
        user_id = f"usr_{secrets.token_hex(8)}"
        session_token, csrf_token, audit_ref, created_at, expires_at = (
            self._new_session()
        )
        try:
            self._store.register_account(
                request_id=request.request_id,
                user_id=user_id,
                username=username,
                password_hash=hash_password(password),
                account_id=request.account_id,
                workspace_id=request.workspace_id,
                runtime_profile=profile,
                session_digest=_digest(session_token),
                csrf_digest=_digest(csrf_token),
                audit_ref=audit_ref,
                created_at=created_at,
                expires_at=expires_at,
            )
        except WorkspaceStorageError:
            return _registration_failure(
                request,
                "Username or account scope is unavailable",
            )
        return ManageAccountsSuccess(
            request_id=request.request_id,
            user=AccountRecord(
                user_id=user_id,
                username=username,
                account_id=request.account_id,
                workspace_id=request.workspace_id,
                authentication_audit_ref=audit_ref,
                expires_at=expires_at,
                runtime_profile=profile,
            ),
            session_token=session_token,
            csrf_token=csrf_token,
        )

    def _login(
        self,
        request: ManageAccountsRequest,
    ) -> ManageAccountsSuccess | WorkspaceFailure:
        row = self._store.find_credentials(
            request_id=request.request_id,
            username=(request.username or "").strip(),
            account_id=request.account_id,
            workspace_id=request.workspace_id,
        )
        if row is None or not bool(row["active"]) or not bool(row["verified"]):
            return _authentication_failure(request, "Invalid username or password")
        if not verify_password(request.password or "", str(row["password_hash"])):
            return _authentication_failure(request, "Invalid username or password")
        session_token, csrf_token, audit_ref, created_at, expires_at = (
            self._new_session()
        )
        try:
            self._store.issue_session(
                request_id=request.request_id,
                user_id=str(row["user_id"]),
                account_id=request.account_id,
                workspace_id=request.workspace_id,
                session_digest=_digest(session_token),
                csrf_digest=_digest(csrf_token),
                audit_ref=audit_ref,
                created_at=created_at,
                expires_at=expires_at,
            )
        except WorkspaceStorageError:
            return _authentication_failure(request)
        return ManageAccountsSuccess(
            request_id=request.request_id,
            user=AccountRecord(
                user_id=str(row["user_id"]),
                username=str(row["username"]),
                account_id=request.account_id,
                workspace_id=request.workspace_id,
                authentication_audit_ref=audit_ref,
                expires_at=expires_at,
                runtime_profile=str(row["runtime_profile"]),
            ),
            session_token=session_token,
            csrf_token=csrf_token,
        )

    def _resolve_session(
        self,
        request: ManageAccountsRequest,
    ) -> ManageAccountsSuccess | WorkspaceFailure:
        row = self._store.resolve_session(
            request_id=request.request_id,
            session_digest=_digest(request.session_token or ""),
            account_id=request.account_id,
            workspace_id=request.workspace_id,
        )
        if row is None or row["revoked_at"] is not None:
            return _authentication_failure(request)
        expires_at = _parse_timestamp(row["expires_at"])
        if (
            expires_at is None
            or expires_at <= self._now()
            or not bool(row["active"])
            or not bool(row["verified"])
        ):
            return _authentication_failure(request)
        return ManageAccountsSuccess(
            request_id=request.request_id,
            user=AccountRecord(
                user_id=str(row["user_id"]),
                username=str(row["username"]),
                account_id=str(row["account_id"]),
                workspace_id=str(row["workspace_id"]),
                authentication_audit_ref=str(row["authentication_audit_ref"]),
                expires_at=_format_timestamp(expires_at),
                runtime_profile=str(row["runtime_profile"]),
            ),
        )

    def _logout(self, request: ManageAccountsRequest) -> ManageAccountsSuccess:
        token = request.session_token or ""
        if token:
            self._store.revoke_session(
                request_id=request.request_id,
                session_digest=_digest(token),
                revoked_at=_format_timestamp(self._now()),
                account_id=request.account_id,
            )
        return ManageAccountsSuccess(request_id=request.request_id, revoked=True)

    def safe_session_audit_records(
        self,
        *,
        request_id: str,
        account_id: str,
    ) -> tuple[SafeSessionAuditRecord, ...]:
        """Return credential-free retained authentication references.

        Args:
            request_id: Stable read identity.
            account_id: Authorized account scope.

        Returns:
            Safe session/audit projections without credential material.
        """
        if self._closed:
            return ()
        return self._store.safe_session_audit_records(
            request_id=request_id,
            account_id=account_id,
        )

    def close(self) -> None:
        """Dispose this account provider without closing shared persistence."""
        self._closed = True
