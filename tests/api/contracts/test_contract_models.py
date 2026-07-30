"""API boundary contract model validation tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.services.api import (
    build_api_error,
    build_api_metadata,
    build_api_response,
    build_governed_request_context,
    build_page_context,
    build_route_contract,
    build_stream_event,
)
from pydantic import ValidationError

_NOW = datetime(2026, 7, 24, 10, tzinfo=UTC)


def _metadata_request() -> object:
    """Build a simple valid metadata object."""
    return build_api_metadata(
        request_id="req-11",
        route="/api/contracts/metadata",
        operation="metadata.read",
        trace_id="trace-11",
        duration_ms=12.0,
    )


def _route_contract() -> object:
    """Build one valid route contract for generic usage."""
    return build_route_contract(
        route_id="api.contracts.boundary",
        method="GET",
        path="/api/contracts/example",
        owner="api",
        response_contract="ApiResponse.v1",
    )


def test_api_metadata_rejects_invalid_time() -> None:
    """Validate metadata requirements for UTC timestamps and stale-state constraints."""
    with pytest.raises(ValidationError, match="timestamp must be UTC-aware"):
        build_api_metadata(
            request_id="req-11",
            route="/api/contracts/metadata",
            operation="metadata.read",
            timestamp="2026-07-24T10:00:00",
        )

    with pytest.raises(ValidationError, match="stale_reason is required"):
        build_api_metadata(
            request_id="req-11",
            route="/api/contracts/metadata",
            operation="metadata.read",
            stale=True,
        )


def test_api_error_bounds_details() -> None:
    """Validate bounded and secret-free error envelopes."""
    base = {
        "code": "VALIDATION_FAILED",
        "message": "invalid request payload",
        "request_id": "req-12",
        "trace_id": "trace-12",
    }

    with pytest.raises(ValidationError, match="at most"):
        build_api_error(**base, details={f"k-{index}": index for index in range(17)})

    with pytest.raises(ValidationError, match="reserved key"):
        build_api_error(
            **base,
            details={"api_key": "value"},  # pragma: allowlist secret
        )

    assert (
        build_api_error(**base, details={"ok": 1}).message == "invalid request payload"
    )


def test_response_envelope_shape() -> None:
    """Validate mutually exclusive success and error fields."""
    metadata = _metadata_request()
    success = build_api_response(
        status="success",
        message="ok",
        data={"ready": True},
        metadata=metadata,
    )
    assert success.error is None
    assert success.data == {"ready": True}

    with pytest.raises(ValidationError):
        build_api_response(
            status="success",
            message="bad",
            error=build_api_error(
                code="INTERNAL_ERROR",
                message="invalid success",
            ),
            metadata=metadata,
        )

    with pytest.raises(ValidationError):
        build_api_response(
            status="ERROR",
            message="failed",
            metadata=metadata,
        )


def test_stream_event_requires_sequence() -> None:
    """Validate stream event sequencing and constrained event shapes."""
    metadata = {"request_id": "req-13", "route": "/api/contracts/stream"}

    with pytest.raises(ValidationError, match="greater than or equal"):
        build_stream_event(
            sequence=-1,
            request_id=metadata["request_id"],
            route=metadata["route"],
        )

    with pytest.raises(
        ValidationError, match="heartbeat events cannot include payload"
    ):
        build_stream_event(
            sequence=0,
            request_id=metadata["request_id"],
            route=metadata["route"],
            event_type="heartbeat",
            payload={"status": "alive"},
        )

    with pytest.raises(ValidationError, match="error events require error"):
        build_stream_event(
            sequence=0,
            request_id=metadata["request_id"],
            route=metadata["route"],
            event_type="error",
        )

    event = build_stream_event(
        sequence=2,
        request_id=metadata["request_id"],
        route=metadata["route"],
        event_type="payload",
        payload={"state": "ready"},
        cursor="cursor-2",
    )
    assert event.timestamp.tzinfo is not None


def test_route_contract_validation_rules() -> None:
    """Require request metadata invariants for route drift-safe declarations."""
    with pytest.raises(ValueError, match="requires a response contract"):
        build_route_contract(
            route_id="api.contracts.bad",
            method="GET",
            path="/api/contracts/example",
            owner="api",
            pagination="cursor",
            response_contract=None,
        )

    valid = _route_contract()
    assert valid.method == "GET"
    assert valid.stability == "stable"
    assert valid.route_id == "api.contracts.boundary"

    with pytest.raises(
        ValueError, match="governed_write routes must require governance"
    ):
        build_route_contract(
            route_id="api.contracts.governed",
            method="POST",
            path="/api/contracts/governed",
            owner="api",
            side_effect="governed_write",
            governance_scope="optional",
            idempotency_policy="required",
            response_contract="ApiResponse.v1",
        )


def test_governed_context_staleness() -> None:
    """Validate freshness checks for governed context objects."""
    with pytest.raises(ValidationError, match="required"):
        build_governed_request_context(
            workflow="",
            permission="risk:approve",
            actor_id="user-1",
            evidence_id="evidence-1",
        )

    context = build_governed_request_context(
        workflow="risk_operator",
        permission="risk:approve",
        actor_id="user-1",
        evidence_id="evidence-1",
        stale_after_seconds=2,
        generated_at=_NOW,
    )
    assert not context.is_stale(now=_NOW + timedelta(seconds=1))
    assert context.is_stale(now=_NOW + timedelta(seconds=3))


def test_page_context_redacts_visible_entities() -> None:
    """Ensure page-context IDs are bounded, unique, and redacted for clients."""
    page = build_page_context(
        route="/app/contracts",
        user_id="user-1",
        page_name="contracts",
        approved_actions=("view", "edit"),
        visible_entity_ids=("entity-1", "entity-2"),
    )
    assert len(page.redacted_visible_entity_ids) == 2
    assert page.redacted_visible_entity_ids[0] != "entity-1"

    with pytest.raises(ValidationError, match="must start with"):
        build_page_context(
            route="app/contracts", user_id="user-1", page_name="contracts"
        )
