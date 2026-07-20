"""Authentication context and deterministic authorization helpers.

This module provides side-effect-free support helpers for building and
validating an immutable authentication context and for making deterministic,
deny-by-default authorization decisions. Support helpers return native values
or raise typed HaruQuant exceptions; the single official AI tool returns the
standard HaruQuant response envelope.

Exported AI Tools:
    validate_auth_context: Official low-risk, read-only auth-context validator
        that returns a standard response envelope.

Support helpers:
    build_auth_context, authorize_action, require_authorization.

Side effects:
    None on import. No network calls, file creation, or environment mutation.
"""

from __future__ import annotations

import time
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final, Literal

from app.services.utils.errors import (
    SecurityError,
    ValidationError,
    normalize_error_code,
)
from app.services.utils.identity import validate_request_id, validate_workflow_id
from app.services.utils.logger import logger
from app.services.utils.standard import (
    StandardResponse,
    build_metadata,
    error_response,
    success_response,
)

TOOL_NAME: Final[str] = "validate_auth_context"
TOOL_VERSION: Final[str] = "1.0.0"
TOOL_CATEGORY: Final[str] = "utils"
TOOL_RISK_LEVEL: Literal["low"] = "low"
REQUIRES_APPROVAL = False
READS = False
WRITES = False
UPDATES = False
DELETES = False
TRADES = False
REQUIRES_NETWORK = False

PrincipalType = Literal["owner", "operator", "service", "agent", "viewer"]
DecisionStatus = Literal["allowed", "denied"]


def _string_set(value: object) -> set[str]:
    """Return a set of strings coerced from an iterable object.

    Args:
        value: Candidate iterable of values, or ``None``. Strings are
            rejected because a bare string is an iterable of characters
            and almost always indicates a caller error.

    Returns:
        A set containing the ``str`` form of each item in ``value``, or an
        empty set when ``value`` is ``None``.

    Raises:
        ValidationError: If ``value`` is a string or is not iterable.

    Side effects:
        None.
    """
    if value is None:
        logger.info("Implemented string set coercion")
        return set()
    if isinstance(value, str) or not isinstance(value, Iterable):
        raise ValidationError("auth collection fields must be iterable.")
    res = {str(item) for item in value}
    logger.info("Implemented string set coercion")
    return res


@dataclass(frozen=True, slots=True)
class AuthContext:
    """Immutable authentication context for a single request or workflow.

    Attributes:
        principal_id: Stable identifier of the authenticated principal.
        principal_type: Principal category (owner, operator, service,
            agent, or viewer).
        roles: Frozen set of role names granted to the principal.
        permissions: Frozen set of permission names granted to the
            principal.
        scopes: Frozen set of scope names granted to the principal.
        request_id: Validated trace request identifier.
        workflow_id: Validated trace workflow identifier.
        correlation_id: Optional cross-request correlation identifier.
    """

    principal_id: str
    principal_type: PrincipalType
    roles: frozenset[str]
    permissions: frozenset[str]
    scopes: frozenset[str]
    request_id: str
    workflow_id: str
    correlation_id: str | None = None


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    """Deterministic, deny-by-default authorization decision.

    Attributes:
        status: Decision status, either ``"allowed"`` or ``"denied"``.
        allowed: ``True`` only when the principal satisfies every required
            permission and scope.
        reason: Short, secret-free explanation of the decision.
        missing_permissions: Sorted tuple of the permissions and scopes
            that were required but not present. Empty when allowed.
    """

    status: DecisionStatus
    allowed: bool
    reason: str
    missing_permissions: tuple[str, ...]


def build_auth_context(
    *,
    principal_id: str,
    principal_type: PrincipalType,
    roles: set[str] | frozenset[str],
    permissions: set[str] | frozenset[str],
    scopes: set[str] | frozenset[str],
    request_id: str,
    workflow_id: str,
    correlation_id: str | None = None,
) -> AuthContext:
    """Build and validate an immutable authentication context.

    Args:
        principal_id: Non-empty identifier of the principal.
        principal_type: Principal category (owner, operator, service,
            agent, or viewer).
        roles: Role names to grant; coerced to a frozen set.
        permissions: Permission names to grant; coerced to a frozen set.
        scopes: Scope names to grant; coerced to a frozen set.
        request_id: Trace request identifier; validated for shape.
        workflow_id: Trace workflow identifier; validated for shape.
        correlation_id: Optional cross-request correlation identifier.

    Returns:
        A validated, immutable ``AuthContext``.

    Raises:
        ValidationError: If ``principal_id`` is empty, ``principal_type``
            is unknown, or ``request_id``/``workflow_id`` fail validation.

    Side effects:
        None.
    """
    if not principal_id.strip():
        raise ValidationError("principal_id must be non-empty.", code="INVALID_INPUT")
    if principal_type not in {"owner", "operator", "service", "agent", "viewer"}:
        raise ValidationError("principal_type is invalid.", code="INVALID_INPUT")
    context = AuthContext(
        principal_id=principal_id.strip(),
        principal_type=principal_type,
        roles=frozenset(roles),
        permissions=frozenset(permissions),
        scopes=frozenset(scopes),
        request_id=validate_request_id(request_id),
        workflow_id=validate_workflow_id(workflow_id),
        correlation_id=correlation_id,
    )
    logger.info("Implemented building auth context")
    return context


def authorize_action(
    context: AuthContext | None,
    *,
    required_permissions: set[str] | frozenset[str],
    required_scopes: set[str] | frozenset[str] = frozenset(),
) -> AuthorizationDecision:
    """Return a deny-by-default authorization decision.

    A missing context, or any required permission or scope that the
    principal does not hold, results in a denial.

    Args:
        context: Authentication context to evaluate, or ``None``.
        required_permissions: Permissions the principal must hold.
        required_scopes: Scopes the principal must hold. Defaults to an
            empty set.

    Returns:
        An ``AuthorizationDecision`` describing the outcome and any
        missing permissions or scopes.

    Side effects:
        None.
    """
    if context is None:
        logger.info("Implemented authorize action check")
        return AuthorizationDecision(
            "denied", False, "missing auth context", tuple(required_permissions)
        )
    missing_permissions = tuple(
        sorted(set(required_permissions) - set(context.permissions))
    )
    missing_scopes = tuple(sorted(set(required_scopes) - set(context.scopes)))
    missing = (*missing_permissions, *missing_scopes)
    if missing:
        logger.info("Implemented authorize action check")
        return AuthorizationDecision(
            "denied", False, "missing permissions or scopes", missing
        )
    logger.info("Implemented authorize action check")
    return AuthorizationDecision("allowed", True, "authorized", ())


def require_authorization(
    context: AuthContext | None,
    *,
    required_permissions: set[str] | frozenset[str],
    required_scopes: set[str] | frozenset[str] = frozenset(),
) -> None:
    """Authorize an action or raise when the principal is not permitted.

    Args:
        context: Authentication context to evaluate, or ``None``.
        required_permissions: Permissions the principal must hold.
        required_scopes: Scopes the principal must hold. Defaults to an
            empty set.

    Returns:
        ``None`` when authorization succeeds.

    Raises:
        SecurityError: If authorization is denied. The error carries the
            deterministic ``AUTHORIZATION_FAILED`` code and a secret-free
            reason.

    Side effects:
        None.
    """
    decision = authorize_action(
        context,
        required_permissions=required_permissions,
        required_scopes=required_scopes,
    )
    if not decision.allowed:
        raise SecurityError(decision.reason, code="AUTHORIZATION_FAILED")
    logger.info("Implemented require authorization enforcement")


def validate_auth_context(
    payload: dict[str, object],
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Official low-risk read-only auth context validator.

    Use this tool to validate an auth context payload (e.g. principal_id, type, roles).

    Args:
        payload (dict[str, object]): The auth context payload to validate.
        request_id (str | None, optional): Optional trace request ID.

    Returns:
        StandardResponse: Standard tool response envelope.

    Raises:
        N/A — all exceptions are caught and returned as error responses.
            INVALID_INPUT: Missing required auth fields or malformed
                collection values.
            PERMISSION_DENIED: Auth context violates security validation.
            TOOL_EXECUTION_FAILED: Unexpected validation runtime failure.

    Side effects:
        Emits structured tool call, validation failure, success, and exception
        logs. It does not mutate auth state or grant permissions.
    """
    start = time.perf_counter()
    logger.info(
        "validate_auth_context called",
        extra={"event_name": "tool_called", "request_id": request_id},
    )
    metadata = build_metadata(
        tool_name=TOOL_NAME,
        tool_version=TOOL_VERSION,
        tool_category=TOOL_CATEGORY,
        tool_risk_level=TOOL_RISK_LEVEL,
        request_id=request_id,
        reads=READS,
        writes=WRITES,
        updates=UPDATES,
        deletes=DELETES,
        trades=TRADES,
        requires_network=REQUIRES_NETWORK,
        start_time=start,
    )
    try:
        build_auth_context(
            principal_id=str(payload["principal_id"]),
            principal_type=payload["principal_type"],  # type: ignore[arg-type]
            roles=_string_set(payload.get("roles")),
            permissions=_string_set(payload.get("permissions")),
            scopes=_string_set(payload.get("scopes")),
            request_id=str(payload["request_id"]),
            workflow_id=str(payload["workflow_id"]),
            correlation_id=(
                str(payload["correlation_id"])
                if payload.get("correlation_id") is not None
                else None
            ),
        )
        logger.info(
            "validate_auth_context completed",
            extra={"event_name": "tool_success", "request_id": request_id},
        )
    except (KeyError, TypeError, ValidationError, SecurityError) as exc:
        logger.warning(
            "validate_auth_context validation failed",
            extra={"event_name": "tool_validation_failed", "request_id": request_id},
        )
        code = normalize_error_code(getattr(exc, "code", "INVALID_INPUT"))
        return error_response(
            message="Auth context is invalid.",
            code=code,
            details=str(exc),
            metadata=metadata,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "validate_auth_context raised exception",
            extra={"event_name": "tool_exception", "request_id": request_id},
        )
        return error_response(
            message="Auth context validation failed.",
            code="TOOL_EXECUTION_FAILED",
            details=f"{exc.__class__.__name__}: {exc}",
            metadata=metadata,
        )
    roles_count = len(_string_set(payload.get("roles")))
    permissions_count = len(_string_set(payload.get("permissions")))
    return success_response(
        message="Auth context is valid.",
        data={
            "valid": True,
            "principal_type": str(payload.get("principal_type", "")),
            "roles_count": roles_count,
            "permissions_count": permissions_count,
        },
        metadata=metadata,
    )
