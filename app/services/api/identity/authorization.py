"""Authenticated identity and governance enforcement for API routes."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING, Any, Final, Literal, NoReturn, cast

from fastapi import HTTPException, status

from app.composition.logging import get_logger
from app.contracts.common.models import create_auth_context
from app.kernel.time import utc_now

if TYPE_CHECKING:
    from app.services.api.contracts import GovernedRequestContext

logger = get_logger(__name__)

AuthenticationErrorCode: Final = "AUTHENTICATION_REQUIRED"
AuthorizationErrorCode: Final = "AUTHORIZATION_DENIED"
GovernanceErrorCode: Final = "GOVERNANCE_REQUIRED"
StaleGovernedErrorCode: Final = "GOVERNED_REQUEST_STALE"
CsrfRequiredCode: Final = "CSRF_REQUIRED"
CsrfInvalidCode: Final = "CSRF_INVALID"
IdempotencyKeyCode: Final = "IDEMPOTENCY_KEY_REQUIRED"

_APPROVAL_REQUIRED_PREFIXES: Final[tuple[str, ...]] = ("risk.", "ops.")

type AuthSource = Mapping[str, object] | object
type AuthContext = Any


def _raise_authentication_required() -> NoReturn:
    """Raise a fail-closed authentication error.

    Raises:
        HTTPException: If the declared validation fails.
    """
    logger.warning("Rejecting request without validated authentication")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=AuthenticationErrorCode,
    )


def _raise_authorized_denied() -> NoReturn:
    """Raise an authorization denied error.

    Raises:
        HTTPException: If the declared validation fails.
    """
    logger.warning("Rejecting unauthorized API request")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=AuthorizationErrorCode,
    )


def _raise_governance_failure(*, detail: str) -> NoReturn:
    """Raise a governed-request validation failure.

    Raises:
        HTTPException: If the declared validation fails.
    """
    logger.warning("Governed-request validation failed: %s", detail)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _get_field(source: AuthSource, field_name: str) -> object:
    """Read one field from a protocol object or mapping.

    Args:
        source: Claim-like source object.
        field_name: Field to read.

    Returns:
        The requested field.

    Raises:
        HTTPException: If the field cannot be read.
    """
    if isinstance(source, Mapping):
        if field_name not in source:
            logger.debug("Missing field in claim mapping: %s", field_name)
            _raise_authentication_required()
        return source[field_name]
    if not hasattr(source, field_name):
        logger.debug("Missing field on claim object: %s", field_name)
        _raise_authentication_required()
    return getattr(source, field_name)


def _coerce_non_empty_text(value: object, field_name: str) -> str:
    """Read one non-empty text field.

    Args:
        value: Raw candidate value.
        field_name: Field label for diagnostics.

    Returns:
        Trimmed string value.

    Raises:
        HTTPException: If the value cannot be normalized.
    """
    if not isinstance(value, str):
        logger.debug("Invalid non-text field for %s", field_name)
        _raise_authentication_required()
    text = value.strip()
    if not text:
        logger.debug("Empty text field for %s", field_name)
        _raise_authentication_required()
    return text


def _coerce_text_list(value: object, field_name: str) -> tuple[str, ...]:
    """Read and validate one bounded immutable text tuple.

    Args:
        value: Raw list/tuple value.
        field_name: Field label for diagnostics.

    Returns:
        Stable and validated tuple.

    Raises:
        HTTPException: If the candidate cannot be normalized.
    """
    if isinstance(value, str):
        items: tuple[object, ...] = (value,)
    elif isinstance(value, list):
        items = tuple(value)
    elif isinstance(value, tuple):
        items = value
    else:
        logger.debug("Invalid list-like field for %s", field_name)
        _raise_authentication_required()
    normalized = tuple(_coerce_non_empty_text(item, field_name) for item in items)
    if len(set(normalized)) != len(normalized):
        logger.debug("Duplicate entries in %s", field_name)
        _raise_authentication_required()
    return normalized


def _coerce_utc_datetime(value: object, field_name: str) -> datetime:
    """Read a UTC-aware datetime field.

    Args:
        value: Raw datetime value.
        field_name: Field label for diagnostics.

    Returns:
        UTC-aware datetime.

    Raises:
        HTTPException: If the value is missing or naive.
    """
    if not isinstance(value, datetime):
        logger.debug("Invalid datetime for %s", field_name)
        _raise_authentication_required()
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        logger.debug("Naive datetime for %s", field_name)
        _raise_authentication_required()
    return value


def _requires_approval(permission: str) -> bool:
    """Return whether one permission should require explicit approval scope."""
    return permission.startswith(_APPROVAL_REQUIRED_PREFIXES)


def require_auth_context() -> AuthContext:
    """Fail closed until composition injects a validated authentication context.

    Raises:
        HTTPException: Always when no authentication provider is configured.
    """
    _raise_authentication_required()


def require_permission(context: AuthContext, permission: str) -> None:
    """Require exact permission on validated context.

    Args:
        context: Validated shared authentication context.
        permission: Exact receiver permission.

    Raises:
        HTTPException: If permission is absent from the context.
    """
    logger.debug("Checking API permission: %s", permission)
    required = _coerce_non_empty_text(permission, "permission")
    if required not in context.permissions:
        _raise_authorized_denied()


def require_human_permission(context: AuthContext, permission: str) -> None:
    """Require USER principal plus exact permission.

    Args:
        context: Validated shared authentication context.
        permission: Exact receiver permission.

    Raises:
        HTTPException: If caller is not a human principal or lacks permission.
    """
    logger.debug("Checking human API permission: %s", permission)
    if context.principal_type != "USER":
        _raise_authorized_denied()
    require_permission(context, permission)


def build_auth_context(*, principal: AuthSource, trace: AuthSource) -> AuthContext:
    """Build a strict `AuthContext` from validated authority claims.

    Args:
        principal: Verified principal claims from authentication.
        trace: Verified request trace context.

    Returns:
        Validated immutable `AuthContext`.

    Raises:
        HTTPException: If validated claims are incomplete or malformed.
    """
    principal_id = _coerce_non_empty_text(
        _get_field(principal, "principal_id"),
        "principal_id",
    )
    principal_type = _coerce_non_empty_text(
        _get_field(principal, "principal_type"),
        "principal_type",
    )
    if principal_type not in {"USER", "SERVICE_ACCOUNT"}:
        logger.debug("Unsupported principal_type: %s", principal_type)
        _raise_authentication_required()
    roles = _coerce_text_list(_get_field(principal, "roles"), "roles")
    permissions = _coerce_text_list(
        _get_field(principal, "permissions"),
        "permissions",
    )
    scopes = _coerce_text_list(_get_field(principal, "scopes"), "scopes")
    tenant = _coerce_non_empty_text(
        _get_field(principal, "tenant_or_environment"),
        "tenant_or_environment",
    )
    runtime_profile = _coerce_non_empty_text(
        _get_field(principal, "runtime_profile"),
        "runtime_profile",
    )
    if runtime_profile not in {"research", "simulation", "demo", "live"}:
        logger.debug("Unsupported runtime_profile claim")
        _raise_authentication_required()
    issued_at = _coerce_utc_datetime(_get_field(trace, "issued_at"), "issued_at")
    request_id = _coerce_non_empty_text(_get_field(trace, "request_id"), "request_id")
    workflow_id = _coerce_non_empty_text(
        _get_field(trace, "workflow_id"),
        "workflow_id",
    )
    correlation_id = _coerce_non_empty_text(
        _get_field(trace, "correlation_id"),
        "correlation_id",
    )
    return create_auth_context(
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id=principal_id,
        principal_type=cast("Literal['USER', 'SERVICE_ACCOUNT']", principal_type),
        roles=roles,
        permissions=permissions,
        scopes=scopes,
        tenant_or_environment=tenant,
        runtime_profile=cast(
            "Literal['research', 'simulation', 'demo', 'live']",
            runtime_profile,
        ),
        request_id=request_id,
        workflow_id=workflow_id,
        correlation_id=correlation_id,
        issued_at=issued_at,
    )


def _validate_user_csrf(context: AuthContext, governed: GovernedRequestContext) -> None:
    """Validate user-context anti-CSRF request binding.

    Args:
        context: Validated authentication context.
        governed: Candidate governed request envelope.

    Raises:
        HTTPException: If CSRF binding is missing or mismatched.
    """
    if governed.request_id is None:
        _raise_governance_failure(detail=CsrfRequiredCode)
    if governed.request_id != context.request_id:
        _raise_governance_failure(detail=CsrfInvalidCode)
    if governed.trace_id is None:
        _raise_governance_failure(detail=CsrfRequiredCode)
    if governed.trace_id != context.correlation_id:
        _raise_governance_failure(detail=CsrfInvalidCode)


def validate_governed_request(
    context: AuthContext, governed: GovernedRequestContext
) -> None:
    """Validate request binding for one governed write before delegation.

    Args:
        context: Validated shared authentication context.
        governed: Evidence and policy envelope from upstream caller.

    Raises:
        HTTPException: If any authorization, freshness, CSRF, or governance check fails.
    """
    logger.debug("Validating governed request for permission: %s", governed.permission)
    if context.principal_id != governed.actor_id:
        _raise_governance_failure(detail=GovernanceErrorCode)
    require_permission(context, governed.permission)
    if context.principal_type == "USER":
        _validate_user_csrf(context, governed)
    if governed.idempotency_key is None:
        _raise_governance_failure(detail=IdempotencyKeyCode)
    if governed.route_id is None or not governed.route_id.strip():
        _raise_governance_failure(detail=GovernanceErrorCode)
    if governed.audit_reference is None or not governed.audit_reference.strip():
        _raise_governance_failure(detail=GovernanceErrorCode)
    if _requires_approval(governed.permission) and governed.approval_id is None:
        _raise_governance_failure(detail=GovernanceErrorCode)
    if governed.is_stale(now=utc_now()):
        _raise_governance_failure(detail=StaleGovernedErrorCode)


__all__ = (
    "build_auth_context",
    "require_auth_context",
    "require_human_permission",
    "require_permission",
    "validate_governed_request",
)
