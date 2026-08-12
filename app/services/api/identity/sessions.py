"""Opaque server-side UI/API session lifecycle."""

from __future__ import annotations

import hashlib
import secrets
from collections.abc import Mapping
from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict

from app.services.api.identity.accounts import AuthenticatedUser
from app.services.api.identity.errors import IdentityError
from app.services.api.identity.persistence import (
    read_csrf_record,
    read_session_record,
    replace_active_session_record,
    revoke_session_record,
)
from app.utils import get_logger, utc_now

logger = get_logger(__name__)

_MIN_SESSION_TTL_SECONDS = 60
_MAX_SESSION_TTL_SECONDS = 2_592_000


class SessionCredential(BaseModel):
    """Opaque session and CSRF credentials returned only at authentication."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    session_token: str
    csrf_token: str
    expires_at: datetime


class SessionIdentity(BaseModel):
    """Non-secret identity recovered from one validated server-side session."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    user_id: str
    username: str
    expires_at: datetime


def _digest(value: str) -> str:
    """Return a stable one-way token digest."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def create_session(
    user: AuthenticatedUser,
    *,
    request_id: str,
    ttl_seconds: int,
) -> SessionCredential:
    """Replace a user's active session and create one opaque credential.

    Args:
        user: Authenticated active account.
        request_id: Canonical operation request identifier.
        ttl_seconds: Positive bounded session lifetime.

    Returns:
        One-time opaque session and CSRF credentials.

    Raises:
        IdentityError: If the account is inactive or persistence fails.
        ValueError: If the requested lifetime is invalid.
    """
    logger.info("Creating one UI/API session")
    if not user.active or not user.verified:
        raise IdentityError("ACCOUNT_STATE_INVALID")
    if not _MIN_SESSION_TTL_SECONDS <= ttl_seconds <= _MAX_SESSION_TTL_SECONDS:
        raise ValueError("ttl_seconds is outside the approved range")
    now = utc_now()
    expires_at = now + timedelta(seconds=ttl_seconds)
    session_token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    replace_active_session_record(
        user_id=user.user_id,
        session_digest=_digest(session_token),
        csrf_digest=_digest(csrf_token),
        created_at=now.isoformat(),
        expires_at=expires_at.isoformat(),
        request_id=request_id,
    )
    return SessionCredential(
        session_token=session_token,
        csrf_token=csrf_token,
        expires_at=expires_at,
    )


def _validated_session_row(
    session_token: str,
    *,
    request_id: str,
    now: datetime | None = None,
) -> Mapping[str, object]:
    """Return one validated persisted session/account row.

    Args:
        session_token: Opaque browser or service credential.
        request_id: Canonical operation request identifier.
        now: Injectable UTC instant for deterministic tests.

    Returns:
        Validated normalized persistence row.

    Raises:
        IdentityError: If the session or account is invalid.
    """
    logger.info("Validating one UI/API session")
    if not session_token:
        raise IdentityError("AUTHENTICATION_REQUIRED")
    current = now or utc_now()
    rows = read_session_record(_digest(session_token), request_id=request_id)
    if len(rows) != 1:
        raise IdentityError("AUTHENTICATION_REQUIRED")
    row = dict(rows[0])
    expires_at = datetime.fromisoformat(str(row["expires_at"]))
    if row["revoked_at"] is not None or expires_at <= current:
        if row["revoked_at"] is None:
            revoke_session(session_token, request_id=request_id, now=current)
        raise IdentityError("AUTHENTICATION_REQUIRED")
    user = AuthenticatedUser.from_row(row)
    if not user.active or not user.verified:
        raise IdentityError("ACCOUNT_STATE_INVALID")
    return row


def validate_session(
    session_token: str,
    *,
    request_id: str,
    now: datetime | None = None,
) -> AuthenticatedUser:
    """Validate session, expiry, revocation, and current account state.

    Args:
        session_token: Opaque browser or service credential.
        request_id: Canonical operation request identifier.
        now: Injectable UTC instant for deterministic tests.

    Returns:
        Current validated account claims.

    Raises:
        IdentityError: If the session or account is invalid.
    """
    row = _validated_session_row(
        session_token,
        request_id=request_id,
        now=now,
    )
    return AuthenticatedUser.from_row(row)


def recover_session_identity(
    session_token: str,
    *,
    request_id: str,
    now: datetime | None = None,
) -> SessionIdentity:
    """Recover non-secret display identity from a validated persisted session.

    Args:
        session_token: Opaque browser or service credential.
        request_id: Canonical operation request identifier.
        now: Injectable UTC instant for deterministic tests.

    Returns:
        Current identity and exact session expiry without any credential material.

    Raises:
        IdentityError: If the session or account is invalid.
    """
    row = _validated_session_row(
        session_token,
        request_id=request_id,
        now=now,
    )
    return SessionIdentity(
        user_id=str(row["user_id"]),
        username=str(row["username"]),
        expires_at=datetime.fromisoformat(str(row["expires_at"])),
    )


def revoke_session(
    session_token: str,
    *,
    request_id: str,
    now: datetime | None = None,
) -> None:
    """Idempotently revoke one persisted session.

    Args:
        session_token: Opaque session credential.
        request_id: Canonical operation request identifier.
        now: Injectable UTC revocation instant.
    """
    logger.info("Revoking one UI/API session")
    if not session_token:
        return
    revoke_session_record(
        session_digest=_digest(session_token),
        revoked_at=(now or utc_now()).isoformat(),
        request_id=request_id,
    )


def validate_csrf(
    session_token: str,
    csrf_token: str,
    *,
    request_id: str,
) -> None:
    """Validate a CSRF token against one active session.

    Args:
        session_token: Opaque session credential.
        csrf_token: Double-submit anti-CSRF credential.
        request_id: Canonical operation request identifier.

    Raises:
        IdentityError: If the token binding is absent or mismatched.
    """
    rows = read_csrf_record(_digest(session_token), request_id=request_id)
    if len(rows) != 1 or not secrets.compare_digest(
        str(rows[0]["csrf_digest"]), _digest(csrf_token)
    ):
        raise IdentityError("CSRF_INVALID")


__all__ = (
    "SessionCredential",
    "SessionIdentity",
    "create_session",
    "recover_session_identity",
    "revoke_session",
    "validate_csrf",
    "validate_session",
)
