"""Standalone identity usage examples."""

from __future__ import annotations

from datetime import UTC, datetime

from app.services.api import build_governed_request_context
from app.services.api.identity import (
    build_auth_context,
    require_human_permission,
    require_permission,
    validate_governed_request,
)


def _principal() -> dict[str, object]:
    """Return one canonical principal payload."""
    return {
        "principal_id": "identity-operator-01",
        "principal_type": "USER",
        "roles": ("ops",),
        "permissions": ("risk.kill.activate", "research:run"),
        "scopes": ("risk",),
        "tenant_or_environment": "simulation",
    }


def _trace() -> dict[str, object]:
    """Return one canonical trace payload."""
    return {
        "issued_at": datetime(2026, 7, 24, 9, 30, 0, tzinfo=UTC),
        "request_id": "req-11111111-1111-4111-8111-111111111111",
        "workflow_id": "wf-22222222-2222-4222-8222-222222222222",
        "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
    }


def fr_api_013() -> object:
    """FR-API-013: build an authoritative AuthContext from claims."""
    return build_auth_context(
        principal=_principal(),
        trace=_trace(),
    )


def fr_api_014() -> bool:
    """FR-API-014: enforce and pass one approved permission."""
    context = fr_api_013()
    require_permission(context, "risk.kill.activate")
    require_human_permission(context, "risk.kill.activate")
    return True


def fr_api_015() -> bool:
    """FR-API-015: validate a complete governed request envelope."""
    context = fr_api_013()
    governed = build_governed_request_context(
        workflow="risk.review",
        permission="risk.kill.activate",
        actor_id=context.principal_id,
        evidence_id="evidence-identity-01",
        approval_id="approval-identity-01",
        idempotency_key="idem-identity-01",
        route_id="api.identity.test",
        audit_reference="audit-identity-01",
        request_id=context.request_id,
        trace_id=context.correlation_id,
        stale_after_seconds=30,
    )
    validate_governed_request(context, governed)
    return True


def main() -> None:
    """Run API identity usage evidence scenarios."""
    context = fr_api_013()
    assert fr_api_014()
    assert fr_api_015()
    print(
        {
            "principal_id": context.principal_id,
            "permission_check": "passed",
            "governed_check": "passed",
        }
    )


if __name__ == "__main__":
    main()
