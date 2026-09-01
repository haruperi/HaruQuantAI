"""Read operations for Identity-owned database records."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, cast

from app.composition.logging import get_logger
from app.services.api.identity.persistence import IdentityError
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)

logger = get_logger(__name__)

_AUTHORITY_COLUMNS = """
COALESCE((
    SELECT json_group_array(role_name)
    FROM (
        SELECT DISTINCT role.role_name AS role_name
        FROM api_role_bindings AS binding
        JOIN api_roles AS role ON role.role_id = binding.role_id
        WHERE binding.account_id = a.user_id
          AND binding.revoked_at IS NULL
          AND (binding.expires_at IS NULL OR binding.expires_at > CURRENT_TIMESTAMP)
        ORDER BY role.role_name
    )
), '[]') AS roles_json,
COALESCE((
    SELECT json_group_array(permission_key)
    FROM (
        SELECT DISTINCT permission.permission_key AS permission_key
        FROM api_role_bindings AS binding
        JOIN api_role_permissions AS grant_row
          ON grant_row.role_id = binding.role_id
        JOIN api_permissions AS permission
          ON permission.permission_id = grant_row.permission_id
        WHERE binding.account_id = a.user_id
          AND binding.revoked_at IS NULL
          AND (binding.expires_at IS NULL OR binding.expires_at > CURRENT_TIMESTAMP)
        ORDER BY permission.permission_key
    )
), '[]') AS permissions_json,
COALESCE((
    SELECT json_group_array(scope_key)
    FROM (
        SELECT DISTINCT binding.scope_key AS scope_key
        FROM api_role_bindings AS binding
        WHERE binding.account_id = a.user_id
          AND binding.scope_key <> ''
          AND binding.revoked_at IS NULL
          AND (binding.expires_at IS NULL OR binding.expires_at > CURRENT_TIMESTAMP)
        ORDER BY binding.scope_key
    )
), '[]') AS scopes_json
""".strip()


class _TransactionResult(Protocol):
    """Fields consumed from Data's normalized transaction result."""

    rows: tuple[Mapping[str, object], ...]


def _read_rows(
    statement: str,
    parameters: tuple[object, ...],
    *,
    request_id: str,
    max_rows: int = 1,
) -> tuple[Mapping[str, object], ...]:
    """Execute one bounded API read through Data.

    Args:
        statement: Parameterized read statement.
        parameters: Bound statement parameters.
        request_id: Canonical operation request identifier.
        max_rows: Upper bound on rows returned; single-key lookups keep the
            default of 1, multi-row listings pass an explicit bound.

    Returns:
        Zero or more normalized database rows, up to ``max_rows``.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(statement,),
                parameter_sets=(parameters,),
                max_rows=max_rows,
            ),
            request_id=request_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise IdentityError("IDENTITY_STORE_UNAVAILABLE")
    result = cast("_TransactionResult", response.data)
    return tuple(result.rows)


def read_auth_lock_record(
    username_hash: str, *, request_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read the current authentication lock for a username digest.

    Args:
        username_hash: Non-reversible normalized username digest.
        request_id: Canonical operation request identifier.

    Returns:
        Zero or one normalized lock rows.
    """
    logger.debug("Reading API authentication lock persistence record")
    return _read_rows(
        "SELECT locked_until FROM api_auth_failures WHERE username_hash = ?",
        (username_hash,),
        request_id=request_id,
    )


def read_auth_failure_record(
    username_hash: str, *, request_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read the current authentication-failure window.

    Args:
        username_hash: Non-reversible normalized username digest.
        request_id: Canonical operation request identifier.

    Returns:
        Zero or one normalized failure-window rows.
    """
    logger.debug("Reading API authentication failure persistence record")
    return _read_rows(
        "SELECT failure_count, window_started_at FROM api_auth_failures "
        "WHERE username_hash = ?",
        (username_hash,),
        request_id=request_id,
    )


def read_account_record(
    username: str, *, request_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read one API account by exact username.

    Args:
        username: Exact account login name.
        request_id: Canonical operation request identifier.

    Returns:
        Zero or one normalized account rows.
    """
    logger.debug("Reading API account persistence record")
    return _read_rows(
        "SELECT a.user_id, a.username, a.password_hash, "  # noqa: S608
        f"{_AUTHORITY_COLUMNS}, "
        "a.environment, a.runtime_profile, a.active, a.verified, "
        "a.last_login_at FROM api_accounts AS a WHERE a.username = ?",
        (username,),
        request_id=request_id,
    )


def read_account_identity_by_user_id(
    user_id: str, *, request_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read one non-secret API account identity by stable user ID.

    Args:
        user_id: Stable authenticated principal identifier.
        request_id: Canonical operation request identifier.

    Returns:
        Zero or one user ID and username rows.
    """
    return _read_rows(
        "SELECT user_id, username FROM api_accounts WHERE user_id = ?",
        (user_id,),
        request_id=request_id,
    )


def read_session_record(
    session_digest: str, *, request_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read one session and its current account authority.

    Args:
        session_digest: One-way opaque-session digest.
        request_id: Canonical operation request identifier.

    Returns:
        Zero or one normalized joined session rows.
    """
    logger.debug("Reading API session persistence record")
    return _read_rows(
        "SELECT a.user_id, a.username, "  # noqa: S608
        f"{_AUTHORITY_COLUMNS}, "
        "a.environment, a.runtime_profile, a.active, a.verified, "
        "a.last_login_at, s.expires_at, s.revoked_at FROM api_sessions AS s "
        "JOIN api_accounts AS a ON a.user_id = s.user_id "
        "WHERE s.session_digest = ?",
        (session_digest,),
        request_id=request_id,
    )


def read_csrf_record(
    session_digest: str, *, request_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read the CSRF binding for one opaque-session digest.

    Args:
        session_digest: One-way opaque-session digest.
        request_id: Canonical operation request identifier.

    Returns:
        Zero or one normalized CSRF rows.
    """
    logger.debug("Reading API CSRF persistence record")
    return _read_rows(
        "SELECT csrf_digest FROM api_sessions WHERE session_digest = ?",
        (session_digest,),
        request_id=request_id,
    )


def read_credential_record(
    reference: str, *, request_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read one encrypted credential record by opaque reference.

    Args:
        reference: Exact opaque credential reference.
        request_id: Canonical operation request identifier.

    Returns:
        Zero or one normalized encrypted credential rows.
    """
    logger.debug("Reading API credential persistence record")
    return _read_rows(
        "SELECT owner_id, key_id, nonce_b64, ciphertext_b64, created_at, version "
        "FROM api_credentials WHERE reference = ?",
        (reference,),
        request_id=request_id,
    )


def read_approval_record(
    approval_id: str, *, request_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read one scoped approval record.

    Args:
        approval_id: Stable approval identifier.
        request_id: Canonical operation request identifier.

    Returns:
        Zero or one normalized approval rows.
    """
    logger.debug("Reading API approval persistence record")
    return _read_rows(
        "SELECT issuer_id, subject_id, scope, evidence_hash, created_at, "
        "expires_at, consumed_at FROM api_approvals WHERE approval_id = ?",
        (approval_id,),
        request_id=request_id,
    )


def read_idempotency_record(
    scope_key: str, *, request_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read one HTTP idempotency reservation.

    Args:
        scope_key: Canonical request-scope digest.
        request_id: Canonical operation request identifier.

    Returns:
        Zero or one normalized idempotency rows.
    """
    logger.debug("Reading API idempotency persistence record")
    return _read_rows(
        "SELECT request_hash, response_json, status_code, expires_at "
        "FROM api_idempotency WHERE scope_key = ?",
        (scope_key,),
        request_id=request_id,
    )


def read_settings_record(
    scope: str, subject_id: str, *, request_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read one scoped current settings record.

    Args:
        scope: Settings authority scope, system or user.
        subject_id: Global or authenticated-user settings subject.
        request_id: Canonical operation request identifier.

    Returns:
        Zero or one normalized settings rows.
    """
    logger.debug("Reading API settings persistence record")
    return _read_rows(
        "SELECT settings_json, version, created_at, updated_at, updated_by "
        "FROM api_settings WHERE scope = ? AND subject_id = ?",
        (scope, subject_id),
        request_id=request_id,
    )


__all__ = [
    "read_account_identity_by_user_id",
    "read_account_record",
    "read_approval_record",
    "read_auth_failure_record",
    "read_auth_lock_record",
    "read_credential_record",
    "read_csrf_record",
    "read_idempotency_record",
    "read_session_record",
    "read_settings_record",
]
