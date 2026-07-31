"""Executable Trading monitoring usage example.

Demonstrates FEAT-TRD-06 operational events, runtime event emission, and budget gates.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.trading import (
    build_broker_state_unknown_event,
    create_execution_receipt,
    create_operational_event,
    emit_runtime_event,
    validate_budget_authority,
)
from tests.trading import conftest as examples

NOW = datetime(2026, 7, 19, tzinfo=UTC)
REQUEST_ID = "req-11111111-1111-4111-8111-111111111111"
WORKFLOW_ID = "wf-22222222-2222-4222-8222-222222222222"
CORRELATION_ID = "cor-33333333-3333-4333-8333-333333333333"
OperationalEvent = Any


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_trd_046() -> None:
    """FR-TRD-046: Stage 3 — Represent focused operational evidence in a Trading-owned contract."""
    _header("Stage 3: Operational Events - Construct Operational Event (FR-TRD-046)")
    event = create_operational_event(
        event_id="usage-event-001",
        event_type="LATENCY_OBSERVED",
        severity="info",
        occurred_at=NOW,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
        facts={"elapsed_seconds": "0.125"},
        source_refs={"operation": "submit_order"},
    )
    print(_format_result(event))
    print(f"Data -> event_id='{event.event_id}', event_type='{event.event_type}'")


def fr_trd_047() -> None:
    """FR-TRD-047: Stage 2 — Validate Risk-owned allocation decision and budget verdict."""
    _header("Stage 2: Budget Gate Validation - Validate Budget Authority (FR-TRD-047)")
    budget_request = examples.monitoring_request()
    budget_result = validate_budget_authority(
        budget_request,
        examples.monitoring_allocation(),
        examples.monitoring_verdict(budget_request),
        now=NOW,
    )
    print(_format_result(budget_result))
    print(f"Data -> status='{budget_result.status}'")


def fr_trd_048() -> None:
    """FR-TRD-048: Stage 3 — Emit redacted runtime event through composition sink."""
    _header("Stage 3: Runtime Event Emission - Emit Runtime Event (FR-TRD-048)")
    published: list[OperationalEvent] = []
    event = create_operational_event(
        event_id="usage-event-002",
        event_type="HEALTH_CHANGED",
        severity="info",
        occurred_at=NOW,
        request_id="req-44444444-4444-4444-8444-444444444444",
        workflow_id="wf-55555555-5555-4555-8555-555555555555",
        correlation_id="cor-66666666-6666-4666-8666-666666666666",
        facts={"health": "ready"},
        source_refs={"session": "session-001"},
    )
    emit_response = emit_runtime_event(event, published.append)
    print(_format_result(emit_response))
    print(f"Data -> status='{emit_response.status}', published_count={len(published)}")


def fr_trd_068() -> None:
    """FR-TRD-068: Stage 3 — Build BROKER_STATE_UNKNOWN OperationalEvent after unknown_outcome transition."""
    _header(
        "Stage 3: Critical Incident Event - Build BROKER_STATE_UNKNOWN Event (FR-TRD-068)"
    )
    receipt = create_execution_receipt(
        receipt_id="usage-receipt-unknown",
        intent_id="usage-intent-unknown",
        client_order_id="usage-client-order-unknown",
        route="sim",
        authority="simulator",
        status="unknown_outcome",
        requested_quantity=Decimal("1.00"),
        filled_quantity=Decimal(0),
        authority_timestamp=NOW,
        received_at=NOW,
        response_classification="timeout",
        retry_safe=False,
        reconciliation_required=True,
        request_id=REQUEST_ID,
        correlation_id=CORRELATION_ID,
    )
    event_response = build_broker_state_unknown_event(
        receipt,
        incident_id="usage-incident-unknown",
        unresolved_scope=("order:usage-order",),
        occurred_at=NOW,
        workflow_id=WORKFLOW_ID,
    )
    published: list[OperationalEvent] = []
    if event_response.data is not None:
        emit_runtime_event(event_response.data, published.append)
    print(_format_result(event_response))
    print(
        f"Data -> status='{event_response.status}', event_type='{event_response.data.event_type if event_response.data else None}'"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-TRD-06 — monitoring/ — Operational and Budget Evidence\n\n"
        "Purpose: Represent operational events, validate Risk-owned budget authority, and publish runtime telemetry.\n\n"
        "Module flow:\n"
        "-> Stage 1: Operational event mapping and evidence payload definition\n"
        "-> Stage 2: Fail-closed budget authority verdict validation\n"
        "-> Stage 3: Operational event construction, critical incident creation, and runtime event emission"
    )

    # Stage 2: Fail-closed budget validation
    fr_trd_047()

    # Stage 3: Event construction & Emission
    fr_trd_046()
    fr_trd_048()
    fr_trd_068()


if __name__ == "__main__":
    main()
