"""Create operations for API-owned database records."""

from __future__ import annotations

from typing import Protocol, cast

from app.services.api.persistence import IdentityError
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.utils import get_logger

logger = get_logger(__name__)


class _TransactionResult(Protocol):
    """Fields consumed from Data's normalized transaction result."""

    affected_rows: int


def _execute_create(
    statements: tuple[str, ...],
    parameter_sets: tuple[tuple[object, ...], ...],
    *,
    request_id: str,
) -> _TransactionResult:
    """Execute one bounded API create plan through Data.

    Args:
        statements: Parameterized create statements.
        parameter_sets: Bound parameters matching the statements.
        request_id: Canonical operation request identifier.

    Returns:
        Normalized committed transaction result.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=statements,
                parameter_sets=parameter_sets,
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise IdentityError("IDENTITY_STORE_UNAVAILABLE")
    return cast("_TransactionResult", response.data)


def create_account_record(
    *,
    user_id: str,
    username: str,
    password_hash: str,
    roles: tuple[str, ...],
    permissions: tuple[str, ...],
    scopes: tuple[str, ...],
    environment: str,
    runtime_profile: str,
    created_at: str,
    request_id: str,
) -> None:
    """Create one active verified API account record.

    Args:
        user_id: Stable account identifier.
        username: Unique normalized login name.
        password_hash: One-way password verifier.
        roles: Server-owned normalized role names.
        permissions: Server-owned normalized permission keys.
        scopes: Server-owned normalized scope keys.
        environment: Account authority environment.
        runtime_profile: Bounded execution-safety profile.
        created_at: ISO-formatted creation instant.
        request_id: Canonical operation request identifier.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    logger.debug("Creating API account and normalized authority records")
    statements: list[str] = []
    parameter_sets: list[tuple[object, ...]] = []
    permission_ids = tuple(f"permission:{item}" for item in permissions)
    authority_checks: list[str] = []
    authority_parameters: list[object] = []
    for role in roles:
        role_id = f"role:{role}"
        if permission_ids:
            placeholders = ", ".join("?" for _ in permission_ids)
            authority_checks.append(
                "(NOT EXISTS (SELECT 1 FROM api_roles WHERE role_id = ?) OR ("  # noqa: S608
                "(SELECT COUNT(*) FROM api_role_permissions WHERE role_id = ?) = ? "
                "AND NOT EXISTS (SELECT 1 FROM api_role_permissions "
                f"WHERE role_id = ? AND permission_id NOT IN ({placeholders}))"
                "))"
            )
            authority_parameters.extend(
                (role_id, role_id, len(permission_ids), role_id, *permission_ids)
            )
        else:
            authority_checks.append(
                "(NOT EXISTS (SELECT 1 FROM api_roles WHERE role_id = ?) OR "
                "NOT EXISTS (SELECT 1 FROM api_role_permissions WHERE role_id = ?) "
                ")"
            )
            authority_parameters.extend((role_id, role_id))
    authority_predicate = " AND ".join(authority_checks) or "1 = 1"
    statements.append(
        "INSERT INTO api_accounts "
        "(user_id, username, password_hash, roles_json, permissions_json, "
        "scopes_json, environment, runtime_profile, active, verified, "
        "created_at, last_login_at) "
        "SELECT ?, ?, ?, '[]', '[]', '[]', ?, ?, 1, 1, ?, NULL "
        f"WHERE {authority_predicate}"
    )
    parameter_sets.append(
        (
            user_id,
            username,
            password_hash,
            environment,
            runtime_profile,
            created_at,
            *authority_parameters,
        )
    )
    for role in roles:
        role_id = f"role:{role}"
        statements.append(
            "INSERT INTO api_roles "
            "(role_id, role_name, description, is_system, created_at, updated_at) "
            "SELECT ?, ?, '', 0, ?, ? WHERE EXISTS "
            "(SELECT 1 FROM api_accounts WHERE user_id = ?) "
            "ON CONFLICT(role_id) DO NOTHING"
        )
        parameter_sets.append((role_id, role, created_at, created_at, user_id))
    for permission in permissions:
        permission_id = f"permission:{permission}"
        domain = permission.replace(".", ":").split(":", maxsplit=1)[0]
        suffix = permission.replace(".", ":").rsplit(":", maxsplit=1)[-1]
        action = (
            suffix if suffix in {"read", "write", "approve", "admin"} else "execute"
        )
        statements.append(
            "INSERT INTO api_permissions "
            "(permission_id, permission_key, domain, action, is_mutating, "
            "created_at, updated_at) SELECT ?, ?, ?, ?, ?, ?, ? WHERE EXISTS "
            "(SELECT 1 FROM api_accounts WHERE user_id = ?) "
            "ON CONFLICT(permission_id) DO NOTHING"
        )
        parameter_sets.append(
            (
                permission_id,
                permission,
                domain,
                action,
                int(action != "read"),
                created_at,
                created_at,
                user_id,
            )
        )
    for role in roles:
        role_id = f"role:{role}"
        for permission_id in permission_ids:
            statements.append(
                "INSERT INTO api_role_permissions "
                "(role_id, permission_id, granted_at, granted_by, created_at) "
                "SELECT ?, ?, ?, ?, ? WHERE EXISTS "
                "(SELECT 1 FROM api_accounts WHERE user_id = ?) "
                "ON CONFLICT(role_id, permission_id) "
                "DO NOTHING"
            )
            parameter_sets.append(
                (role_id, permission_id, created_at, user_id, created_at, user_id)
            )
        binding_scopes = scopes or ("",)
        for scope in binding_scopes:
            statements.append(
                "INSERT INTO api_role_bindings "
                "(binding_id, account_id, role_id, scope_key, granted_by, "
                "expires_at, revoked_at, created_at, updated_at) "
                "SELECT ?, ?, ?, ?, ?, NULL, NULL, ?, ? WHERE EXISTS "
                "(SELECT 1 FROM api_accounts WHERE user_id = ?)"
            )
            parameter_sets.append(
                (
                    f"binding:{user_id}:{role}:{scope}",
                    user_id,
                    role_id,
                    scope,
                    user_id,
                    created_at,
                    created_at,
                    user_id,
                )
            )
    result = _execute_create(
        tuple(statements),
        tuple(parameter_sets),
        request_id=request_id,
    )
    if result.affected_rows == 0:
        raise IdentityError("IDENTITY_AUTHORITY_CONFLICT")


def replace_active_session_record(
    *,
    user_id: str,
    session_digest: str,
    csrf_digest: str,
    created_at: str,
    expires_at: str,
    request_id: str,
) -> None:
    """Atomically revoke prior sessions and create one active session.

    Args:
        user_id: Authenticated account identifier.
        session_digest: One-way opaque-session digest.
        csrf_digest: One-way CSRF-token digest.
        created_at: ISO-formatted creation instant.
        expires_at: ISO-formatted expiry instant.
        request_id: Canonical operation request identifier.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    logger.debug("Replacing active API session persistence record")
    _execute_create(
        (
            "UPDATE api_sessions SET revoked_at = ? "
            "WHERE user_id = ? AND revoked_at IS NULL",
            "INSERT INTO api_sessions "
            "(session_digest, user_id, csrf_digest, created_at, expires_at, "
            "revoked_at) VALUES (?, ?, ?, ?, ?, NULL)",
        ),
        (
            (created_at, user_id),
            (session_digest, user_id, csrf_digest, created_at, expires_at),
        ),
        request_id=request_id,
    )


def create_approval_record(
    *,
    approval_id: str,
    issuer_id: str,
    subject_id: str,
    scope: str,
    evidence_hash: str,
    created_at: str,
    expires_at: str,
    request_id: str,
) -> None:
    """Create one scoped approval persistence record.

    Args:
        approval_id: Stable approval identifier.
        issuer_id: Authorized approver identifier.
        subject_id: Approved consumer identifier.
        scope: Exact approved operation scope.
        evidence_hash: Digest of approved request material.
        created_at: ISO-formatted creation instant.
        expires_at: ISO-formatted expiry instant.
        request_id: Canonical operation request identifier.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    logger.debug("Creating API approval persistence record")
    _execute_create(
        (
            "INSERT INTO api_approvals "
            "(approval_id, issuer_id, subject_id, scope, evidence_hash, "
            "created_at, expires_at, consumed_at) VALUES (?, ?, ?, ?, ?, ?, ?, NULL)",
        ),
        (
            (
                approval_id,
                issuer_id,
                subject_id,
                scope,
                evidence_hash,
                created_at,
                expires_at,
            ),
        ),
        request_id=request_id,
    )


def create_idempotency_record(
    *,
    scope_key: str,
    request_hash: str,
    created_at: str,
    expires_at: str,
    request_id: str,
) -> None:
    """Create one pending HTTP idempotency reservation.

    Args:
        scope_key: Canonical request-scope digest.
        request_hash: Canonical request-material digest.
        created_at: ISO-formatted reservation instant.
        expires_at: ISO-formatted retention expiry.
        request_id: Canonical operation request identifier.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    logger.debug("Creating API idempotency persistence record")
    _execute_create(
        (
            "INSERT INTO api_idempotency "
            "(scope_key, request_hash, response_json, status_code, created_at, "
            "expires_at) VALUES (?, ?, NULL, NULL, ?, ?)",
        ),
        ((scope_key, request_hash, created_at, expires_at),),
        request_id=request_id,
    )


def create_settings_record(
    *,
    scope: str,
    subject_id: str,
    settings_json: str,
    version: int,
    created_at: str,
    updated_at: str,
    updated_by: str,
    request_id: str,
) -> int:
    """Create one initial scoped settings record.

    Args:
        scope: Settings authority scope, system or user.
        subject_id: Global or authenticated-user settings subject.
        settings_json: Canonical serialized settings.
        version: Initial optimistic-lock version.
        created_at: ISO-formatted creation instant.
        updated_at: ISO-formatted update instant.
        updated_by: Authenticated actor responsible for the write.
        request_id: Canonical operation request identifier.

    Returns:
        Number of affected rows.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    logger.debug("Creating API settings persistence record")
    result = _execute_create(
        (
            "INSERT INTO api_settings "
            "(scope, subject_id, settings_json, version, created_at, updated_at, "
            "updated_by, request_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                scope,
                subject_id,
                settings_json,
                version,
                created_at,
                updated_at,
                updated_by,
                request_id,
            ),
        ),
        request_id=request_id,
    )
    return int(result.affected_rows)


__all__ = [
    "create_account_record",
    "create_approval_record",
    "create_idempotency_record",
    "create_settings_record",
    "replace_active_session_record",
]
