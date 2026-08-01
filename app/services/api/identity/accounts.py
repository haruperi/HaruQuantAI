"""UI/API-owned account registration and authentication persistence."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Literal, Protocol, Self, cast

from pydantic import BaseModel, ConfigDict, field_validator

from app.services.api.identity.passwords import hash_password, verify_password
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.utils import derive_stable_id, get_logger, utc_now

logger = get_logger(__name__)

_AUTH_FAILURE_LIMIT = 5
_AUTH_FAILURE_WINDOW_SECONDS = 300
_AUTH_LOCK_SECONDS = 300


class IdentityError(RuntimeError):
    """Bounded UI/API identity failure."""


class _TransactionResult(Protocol):
    """Fields consumed from Data's normalized transaction result."""

    rows: tuple[Mapping[str, object], ...]
    affected_rows: int


class AuthenticatedUser(BaseModel):
    """Validated account authority claims after authentication."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    user_id: str
    username: str
    roles: tuple[str, ...]
    permissions: tuple[str, ...]
    scopes: tuple[str, ...]
    tenant_or_environment: str
    runtime_profile: Literal["research", "simulation", "paper", "live"]
    active: bool = True
    verified: bool = True
    last_login_at: datetime | None = None

    @field_validator("user_id", "username", "tenant_or_environment", mode="after")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one trimmed account field.

        Returns:
            Validated text.

        Raises:
            ValueError: If the value is empty or padded.
        """
        if not value or value != value.strip():
            raise ValueError("account text fields must be non-empty and trimmed")
        return value

    @classmethod
    def from_row(cls, row: Mapping[str, object]) -> Self:
        """Build authority claims from one normalized persistence row.

        Args:
            row: Data-owned normalized query row.

        Returns:
            Validated authenticated user.
        """
        last_login = row.get("last_login_at")
        return cls(
            user_id=str(row["user_id"]),
            username=str(row["username"]),
            roles=tuple(json.loads(str(row["roles_json"]))),
            permissions=tuple(json.loads(str(row["permissions_json"]))),
            scopes=tuple(json.loads(str(row["scopes_json"]))),
            tenant_or_environment=str(row["environment"]),
            runtime_profile=cast(
                "Literal['research', 'simulation', 'paper', 'live']",
                str(row["runtime_profile"]),
            ),
            active=bool(row["active"]),
            verified=bool(row["verified"]),
            last_login_at=(
                datetime.fromisoformat(str(last_login))
                if last_login is not None
                else None
            ),
        )


def _username_hash(username: str) -> str:
    """Return a non-reversible normalized login-attempt key."""
    return hashlib.sha256(username.casefold().encode("utf-8")).hexdigest()


def _check_auth_rate_limit(username: str, request_id: str, now: datetime) -> None:
    """Fail closed while a login-attempt key is locked.

    Raises:
        IdentityError: If the login-attempt key is currently rate limited.
    """
    result = _execute(
        ("SELECT locked_until FROM api_auth_failures WHERE username_hash = ?",),
        ((_username_hash(username),),),
        request_id=request_id,
    )
    rows = tuple(result.rows)
    if (
        rows
        and rows[0]["locked_until"] is not None
        and datetime.fromisoformat(str(rows[0]["locked_until"])) > now
    ):
        raise IdentityError("RATE_LIMITED")


def _record_auth_failure(username: str, request_id: str, now: datetime) -> None:
    """Persist one bounded authentication failure window."""
    key = _username_hash(username)
    result = _execute(
        (
            "SELECT failure_count, window_started_at FROM api_auth_failures "
            "WHERE username_hash = ?",
        ),
        ((key,),),
        request_id=request_id,
    )
    rows = tuple(result.rows)
    window_started = now
    count = 1
    if rows:
        prior_started = datetime.fromisoformat(str(rows[0]["window_started_at"]))
        if now - prior_started <= timedelta(seconds=_AUTH_FAILURE_WINDOW_SECONDS):
            window_started = prior_started
            count = int(str(rows[0]["failure_count"])) + 1
    locked_until = (
        now + timedelta(seconds=_AUTH_LOCK_SECONDS)
        if count >= _AUTH_FAILURE_LIMIT
        else None
    )
    _execute(
        (
            "INSERT INTO api_auth_failures "
            "(username_hash, failure_count, window_started_at, locked_until) "
            "VALUES (?, ?, ?, ?) ON CONFLICT(username_hash) DO UPDATE SET "
            "failure_count=excluded.failure_count, "
            "window_started_at=excluded.window_started_at, "
            "locked_until=excluded.locked_until",
        ),
        (
            (
                key,
                count,
                window_started.isoformat(),
                locked_until.isoformat() if locked_until else None,
            ),
        ),
        request_id=request_id,
    )


def _clear_auth_failures(username: str, request_id: str) -> None:
    """Clear a login-attempt window after successful authentication."""
    _execute(
        ("DELETE FROM api_auth_failures WHERE username_hash = ?",),
        ((_username_hash(username),),),
        request_id=request_id,
    )


def _execute(
    statements: tuple[str, ...],
    parameter_sets: tuple[tuple[object, ...], ...],
    *,
    request_id: str,
    max_rows: int = 1,
) -> _TransactionResult:
    """Execute one bounded account-owned statement plan through Data.

    Returns:
        Data-owned transaction result.

    Raises:
        IdentityError: If Data cannot confirm a committed transaction.
    """
    request = build_transaction_request(
        plan=build_statement_plan(
            statements=statements,
            parameter_sets=parameter_sets,
            max_rows=max_rows,
        ),
        request_id=request_id,
    )
    response = execute_transaction(request)
    if response.status != "success" or response.data is None:
        raise IdentityError("IDENTITY_STORE_UNAVAILABLE")
    return cast("_TransactionResult", response.data)


def register_user(
    *,
    username: str,
    password: str,
    request_id: str,
    roles: tuple[str, ...] = ("user",),
    permissions: tuple[str, ...] = (),
    scopes: tuple[str, ...] = (),
    tenant_or_environment: str = "development",
    runtime_profile: Literal["research", "simulation", "paper", "live"] = "research",
) -> AuthenticatedUser:
    """Register one verified active UI/API user.

    Args:
        username: Unique trimmed login name.
        password: Plaintext password held only while hashing.
        request_id: Canonical operation request identifier.
        roles: Server-authoritative roles.
        permissions: Server-authoritative permissions.
        scopes: Server-authoritative scopes.
        tenant_or_environment: Authority environment binding.
        runtime_profile: Server-authoritative execution-safety profile.

    Returns:
        Registered account claims without password material.

    Raises:
        IdentityError: If persistence fails or the username already exists.
        ValueError: If password or account values are invalid.
    """
    logger.info("Registering one UI/API account")
    normalized_username = username.strip()
    if not normalized_username or normalized_username != username:
        raise ValueError("username must be non-empty and trimmed")
    user_id = derive_stable_id("id", f"api-user:{normalized_username.casefold()}")
    created_at = utc_now()
    try:
        _execute(
            (
                "INSERT INTO api_accounts "
                "(user_id, username, password_hash, roles_json, permissions_json, "
                "scopes_json, environment, runtime_profile, active, verified, "
                "created_at, "
                "last_login_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, NULL)",
            ),
            (
                (
                    user_id,
                    normalized_username,
                    hash_password(password),
                    json.dumps(roles, separators=(",", ":")),
                    json.dumps(permissions, separators=(",", ":")),
                    json.dumps(scopes, separators=(",", ":")),
                    tenant_or_environment,
                    runtime_profile,
                    created_at.isoformat(),
                ),
            ),
            request_id=request_id,
        )
    except IdentityError as error:
        raise IdentityError("ACCOUNT_REGISTRATION_FAILED") from error
    return AuthenticatedUser(
        user_id=user_id,
        username=normalized_username,
        roles=roles,
        permissions=permissions,
        scopes=scopes,
        tenant_or_environment=tenant_or_environment,
        runtime_profile=runtime_profile,
    )


def authenticate_user(
    *, username: str, password: str, request_id: str
) -> AuthenticatedUser:
    """Authenticate one active verified account and update last-login evidence.

    Args:
        username: Exact account login name.
        password: Candidate plaintext password.
        request_id: Canonical operation request identifier.

    Returns:
        Validated authority claims.

    Raises:
        IdentityError: If credentials, account state, or persistence are invalid.
    """
    logger.info("Authenticating one UI/API account")
    login_at = utc_now()
    _check_auth_rate_limit(username, request_id, login_at)
    result = _execute(
        (
            "SELECT user_id, username, password_hash, roles_json, permissions_json, "
            "scopes_json, environment, runtime_profile, active, verified, "
            "last_login_at "
            "FROM api_accounts WHERE username = ?",
        ),
        ((username,),),
        request_id=request_id,
    )
    rows = tuple(result.rows)
    if len(rows) != 1:
        _record_auth_failure(username, request_id, login_at)
        raise IdentityError("AUTHENTICATION_REQUIRED")
    row = dict(rows[0])
    if not bool(row["active"]) or not bool(row["verified"]):
        raise IdentityError("ACCOUNT_STATE_INVALID")
    try:
        matches = verify_password(password, str(row["password_hash"]))
    except ValueError as error:
        raise IdentityError("AUTHENTICATION_DEPENDENCY_UNAVAILABLE") from error
    if not matches:
        _record_auth_failure(username, request_id, login_at)
        raise IdentityError("AUTHENTICATION_REQUIRED")
    _clear_auth_failures(username, request_id)
    _execute(
        ("UPDATE api_accounts SET last_login_at = ? WHERE user_id = ?",),
        ((login_at.isoformat(), str(row["user_id"])),),
        request_id=request_id,
    )
    row["last_login_at"] = login_at.isoformat()
    return AuthenticatedUser.from_row(row)


__all__ = ("AuthenticatedUser", "IdentityError", "authenticate_user", "register_user")
