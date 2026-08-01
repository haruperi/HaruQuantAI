"""Unit tests for identity authorization boundary behavior."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from app.services.api import build_governed_request_context
from app.services.api.identity import (
    build_auth_context,
    require_human_permission,
    require_permission,
    validate_governed_request,
)
from fastapi import HTTPException


def _principal() -> dict[str, object]:
    """Return a canonical authenticated principal payload."""
    return {
        "principal_id": "operator-identity-01",
        "principal_type": "USER",
        "roles": ("risk_operator",),
        "permissions": (
            "risk.kill.activate",
            "strategy:update",
            "research:run",
        ),
        "scopes": ("risk", "strategy"),
        "tenant_or_environment": "simulation",
        "runtime_profile": "simulation",
    }


def _trace() -> dict[str, object]:
    """Return a canonical trace payload."""
    return {
        "issued_at": datetime(2026, 7, 24, 10, 0, 0, tzinfo=UTC),
        "request_id": "req-11111111-1111-4111-8111-111111111111",
        "workflow_id": "wf-22222222-2222-4222-8222-222222222222",
        "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
    }


def _governed_context(
    *,
    principal_id: str,
    permission: str,
    request_id: str,
    trace_id: str,
    stale_after_seconds: int = 30,
    idempotency_key: str | None = "idem-1111",
    approval_id: str | None = "approval-01",
    route_id: str = "api.identity.write",
    audit_reference: str = "audit-11",
    generated_at: datetime | None = None,
) -> object:
    """Build one validated governed request context."""
    return build_governed_request_context(
        workflow="risk.review",
        permission=permission,
        actor_id=principal_id,
        evidence_id="evidence-01",
        approval_id=approval_id,
        idempotency_key=idempotency_key,
        route_id=route_id,
        audit_reference=audit_reference,
        stale_after_seconds=stale_after_seconds,
        request_id=request_id,
        trace_id=trace_id,
        generated_at=generated_at or datetime.now(UTC),
    )


def test_role_header_cannot_create_principal() -> None:
    """Reject missing principal roles even when caller sends arbitrary headers."""

    class HeaderDrivenPrincipal:
        """Mimic request-level claims with caller-controlled role header fields."""

        principal_id = "operator-identity-01"
        principal_type = "USER"
        permissions = ("risk.kill.activate",)
        scopes = ("risk",)
        tenant_or_environment = "simulation"
        role_header = "super_admin"

    with pytest.raises(HTTPException) as exc_info:
        build_auth_context(principal=HeaderDrivenPrincipal(), trace=_trace())
    assert exc_info.value.status_code == 401


def test_missing_permission_rejected() -> None:
    """Reject missing approvals before route execution."""
    context = build_auth_context(principal=_principal(), trace=_trace())
    with pytest.raises(HTTPException) as exc_info:
        require_permission(context, "portfolio:delete")
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "AUTHORIZATION_DENIED"


def test_runtime_profile_claim_is_required_and_bounded() -> None:
    """Reject missing or caller-tampered runtime authority claims."""
    missing = dict(_principal())
    missing.pop("runtime_profile")
    with pytest.raises(HTTPException) as missing_error:
        build_auth_context(principal=missing, trace=_trace())
    assert missing_error.value.status_code == 401

    invalid = {**_principal(), "runtime_profile": "development"}
    with pytest.raises(HTTPException) as invalid_error:
        build_auth_context(principal=invalid, trace=_trace())
    assert invalid_error.value.status_code == 401


def test_require_human_permission_rejects_service_account() -> None:
    """Only USER principals can invoke human permission checks."""
    context = build_auth_context(
        principal={
            **_principal(),
            "principal_id": "service-identity-01",
            "principal_type": "SERVICE_ACCOUNT",
        },
        trace=SimpleNamespace(**_trace()),
    )
    with pytest.raises(HTTPException) as exc_info:
        require_human_permission(context, "risk.kill.activate")
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "AUTHORIZATION_DENIED"


def test_missing_governed_context_fails_closed() -> None:
    """Fail governed operations when required envelope fields are absent."""
    context = build_auth_context(principal=_principal(), trace=_trace())
    governed = _governed_context(
        principal_id=context.principal_id,
        permission="risk.kill.activate",
        request_id=context.request_id,
        trace_id=context.correlation_id,
        idempotency_key=None,
    )
    with pytest.raises(HTTPException) as exc_info:
        validate_governed_request(context, governed)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "IDEMPOTENCY_KEY_REQUIRED"


def test_validate_governed_request_blocks_stale_context() -> None:
    """Reject stale governed data before delegation."""
    context = build_auth_context(principal=_principal(), trace=_trace())
    governed = _governed_context(
        principal_id=context.principal_id,
        permission="risk.kill.activate",
        request_id=context.request_id,
        trace_id=context.correlation_id,
        stale_after_seconds=1,
        generated_at=datetime.now(UTC) - timedelta(seconds=61),
    )
    with pytest.raises(HTTPException) as exc_info:
        validate_governed_request(context, governed)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "GOVERNED_REQUEST_STALE"


def test_validate_governed_request_requires_service_csrf_match() -> None:
    """Require CSRF binding for USER-governed requests."""
    context = build_auth_context(principal=_principal(), trace=_trace())
    governed = _governed_context(
        principal_id=context.principal_id,
        permission="risk.kill.activate",
        request_id="req-99999999-9999-4999-8999-999999999999",
        trace_id=context.correlation_id,
    )
    with pytest.raises(HTTPException) as exc_info:
        validate_governed_request(context, governed)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "CSRF_INVALID"


def test_validate_governed_request_allows_service_account_without_csrf() -> None:
    """Skip CSRF binding for SERVICE_ACCOUNT principals."""
    context = build_auth_context(
        principal={
            **_principal(),
            "principal_id": "svc-identity-01",
            "principal_type": "SERVICE_ACCOUNT",
        },
        trace=_trace(),
    )
    governed = _governed_context(
        principal_id=context.principal_id,
        permission="risk.kill.activate",
        request_id="different-request-id",
        trace_id="different-trace-id",
    )
    validate_governed_request(context, governed)
