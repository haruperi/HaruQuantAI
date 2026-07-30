"""Standalone API contract usage demonstrations."""

from __future__ import annotations

from datetime import UTC, datetime

from app.services.api import (
    build_api_error,
    build_api_metadata,
    build_api_response,
    build_governed_request_context,
    build_page_context,
    build_route_contract,
    build_route_contract_registry,
    build_stream_event,
    get_route_contract_registry,
    register_route_contract,
)

_NOW = datetime(2026, 7, 24, 12, 0, 0, tzinfo=UTC)


def _print(label: str, value: object) -> None:
    """Emit one bounded usage result."""
    print(f"{label}: {value}")


def fr_api_001() -> object:
    """FR-API-001: build one valid request metadata envelope."""
    return build_api_metadata(
        request_id="req-2026-07-24-01",
        route="/api/contracts/usage",
        operation="contracts.boundary.read",
        side_effect="read",
        stale=False,
    )


def fr_api_002() -> object:
    """FR-API-002: build one bounded API error."""
    return build_api_error(
        code="VALIDATION_FAILED",
        message="request payload rejected",
        details={"field": "operation"},
        request_id="req-2026-07-24-01",
        retryable=False,
    )


def fr_api_003() -> dict[str, object]:
    """FR-API-003: build success and error response envelopes."""
    metadata = fr_api_001()
    success = build_api_response(
        status="SUCCESS",
        message="ok",
        data={"ready": True},
        metadata=metadata,
    )
    return {
        "success": success,
        "error": build_api_response(
            status="ERROR",
            message="failed",
            error=fr_api_002(),
            metadata=metadata,
        ),
    }


def fr_api_004() -> list[object]:
    """FR-API-004: build heartbeat and payload stream events."""
    request_id = "req-2026-07-24-01"
    return [
        build_stream_event(
            sequence=0,
            request_id=request_id,
            route="/api/contracts/usage",
            event_type="heartbeat",
        ),
        build_stream_event(
            sequence=1,
            request_id=request_id,
            route="/api/contracts/usage",
            event_type="payload",
            payload={"status": "ready"},
        ),
    ]


def fr_api_005() -> object:
    """FR-API-005: define one complete route contract."""
    return build_route_contract(
        route_id="api.contracts.usage",
        method="GET",
        path="/api/contracts/usage",
        owner="api",
        response_contract="ApiResponse.v1",
        auth_required=True,
        governance_scope="none",
    )


def fr_api_006() -> bool:
    """FR-API-006: build governed context and check freshness."""
    context = build_governed_request_context(
        workflow="risk.review",
        permission="risk.review",
        actor_id="operator-01",
        evidence_id="evidence-01",
        stale_after_seconds=30,
    )
    return context.is_stale(now=_NOW)


def fr_api_007() -> tuple[str, ...]:
    """FR-API-007: expose redacted visible entity IDs."""
    context = build_page_context(
        route="/app/contracts",
        user_id="user-01",
        page_name="contracts",
        approved_actions=("view", "approve"),
        visible_entity_ids=("entity-01", "entity-02"),
    )
    return context.redacted_visible_entity_ids


def fr_api_008() -> bool:
    """FR-API-008: register a contract and verify idempotent collisions."""
    registry = build_route_contract_registry(())
    contract = fr_api_005()
    registry.register_route_contract(contract)
    registry.register_route_contract(contract)
    registry_route = registry.get(contract.method, contract.path)

    if registry_route is None:
        return False

    register_route_contract(contract)
    return (
        get_route_contract_registry().get(contract.method, contract.path) is not None
        and registry_route.route_id == contract.route_id
    )


def main() -> None:
    """Run all contract usage demonstrations."""
    _print("fr_api_001", fr_api_001().model_dump())
    _print("fr_api_002", fr_api_002().code.value)
    _print("fr_api_003", len(fr_api_003()))
    _print("fr_api_004", [event.event_type for event in fr_api_004()])
    _print("fr_api_005", fr_api_005().route_id)
    _print("fr_api_006", fr_api_006())
    _print("fr_api_007", fr_api_007())
    _print("fr_api_008", fr_api_008())


if __name__ == "__main__":
    main()
