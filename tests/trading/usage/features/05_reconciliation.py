"""Executable Trading reconciliation usage example.

Demonstrates FEAT-TRD-05 authority snapshots and reconciliation.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.trading import (
    compare_authority_state,
    create_authority_snapshot,
    create_execution_receipt,
    create_trading_event,
    create_trading_projection,
    resolve_unknown_outcome,
)

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)
AuthoritySnapshot = Any
ExecutionReceipt = Any
TradingEvent = Any
TradingProjection = Any


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


def _snapshot() -> AuthoritySnapshot:
    """Build normalized current Simulation authority facts."""
    return create_authority_snapshot(
        route="sim",
        authority_id="simulator",
        account_id="usage-account-001",
        source_id="usage-sim-read-001",
        account={"state": "ready"},
        orders={},
        positions={},
        observed_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
    )


def _projection() -> TradingProjection:
    """Build the matching Trading projection."""
    return create_trading_projection(
        route="sim",
        tenant_id="usage-account-001",
        authority_id="simulator",
        version=1,
        event_ids=("usage-attempt-001",),
        orders={},
        positions={},
        fills={},
        receipts={},
        authority_state={},
        unresolved_attempt_ids=("usage-attempt-001",),
        updated_at=NOW,
    )


def _attempt() -> TradingEvent:
    """Build originating persisted send-attempt evidence."""
    return create_trading_event(
        event_id="usage-attempt-001",
        event_type="send_attempted",
        aggregate_version=0,
        route="sim",
        tenant_id="usage-account-001",
        authority_id="simulator",
        occurred_at=NOW,
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        payload={"client_order_id": "usage-client-order-001"},
    )


def _receipt() -> ExecutionReceipt:
    """Build one unknown-outcome receipt requiring reconciliation."""
    return create_execution_receipt(
        receipt_id="usage-receipt-001",
        intent_id="usage-intent-001",
        client_order_id="usage-client-order-001",
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
        request_id="req-11111111-1111-4111-8111-111111111111",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )


class _Store:
    """Minimal in-memory Trading persistence example."""

    def __init__(self) -> None:
        """Initialize matching projection and send-attempt evidence."""
        self.projection = _projection()
        self.events = [_attempt()]

    def load_projection(
        self,
        scope: tuple[object, str, str],
    ) -> TradingProjection | None:
        """Load the exact current projection."""
        del scope
        return self.projection

    def load_unresolved_attempts(
        self,
        scope: tuple[object, str, str],
    ) -> tuple[TradingEvent, ...]:
        """Load unresolved send-attempt evidence."""
        del scope
        return (self.events[0],)

    def append_event(self, event: TradingEvent) -> None:
        """Append immutable reconciliation evidence."""
        self.events.append(event)

    def save_projection(
        self,
        projection: TradingProjection,
        expected_version: int,
    ) -> None:
        """Save the next optimistic projection version."""
        if self.projection.version != expected_version:
            raise RuntimeError("stale projection")
        self.projection = projection


def fr_trd_043() -> None:
    """FR-TRD-043: Stage 1 — Expose normalized authority snapshot evidence."""
    _header("Stage 1: Evidence Snapshot - Expose Authority Snapshot (FR-TRD-043)")
    snap = _snapshot()
    print(_format_result(snap))
    print(f"Data -> source_id='{snap.source_id}', route='{snap.route}'")


def fr_trd_044() -> None:
    """FR-TRD-044: Stage 2 — Deterministically compare authority state against projection."""
    _header("Stage 2: State Comparison - Compare Authority State (FR-TRD-044)")
    report_response = compare_authority_state(_snapshot(), _projection())
    print(_format_result(report_response))
    print(f"Data -> status='{report_response.status}'")


def fr_trd_045() -> None:
    """FR-TRD-045: Stage 3 — Resolve unknown outcome receipt and unlock retry."""
    _header(
        "Stage 3: Unknown Outcome Resolution - Resolve Unknown Outcome (FR-TRD-045)"
    )
    resolution_response = resolve_unknown_outcome(  # type: ignore[arg-type]
        _receipt(),
        _Store(),
        lambda _route: _snapshot(),
    )
    print(_format_result(resolution_response))
    print(f"Data -> status='{resolution_response.status}'")


def fr_trd_061() -> None:
    """FR-TRD-061: Stage 3 — Expose deterministic reconciliation report DTO."""
    _header("Stage 3: Reconciliation Report - Construct Comparison Report (FR-TRD-061)")
    report_response = compare_authority_state(_snapshot(), _projection())
    report = report_response.data
    print(_format_result(report))
    print(
        f"Data -> severity='{report.severity if report else None}', unresolved={report.unresolved if report else None}"
    )


def fr_trd_062() -> None:
    """FR-TRD-062: Stage 3 — Expose authority resolution result DTO."""
    _header(
        "Stage 3: Authority Resolution DTO - Construct Resolution Result (FR-TRD-062)"
    )
    resolution_response = resolve_unknown_outcome(  # type: ignore[arg-type]
        _receipt(),
        _Store(),
        lambda _route: _snapshot(),
    )
    resolution = resolution_response.data
    print(_format_result(resolution))
    print(
        f"Data -> transition='{resolution.transition if resolution else None}', retry_allowed={resolution.retry_allowed if resolution else None}"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-TRD-05 — reconciliation/ — Reconciliation and Retry Guard\n\n"
        "Purpose: Normalize authority state, compare local projections against authority truth, and resolve unknown outcomes.\n\n"
        "Module flow:\n"
        "-> Stage 1: Authority snapshot loading and projection state inspection\n"
        "-> Stage 2: Deterministic discrepancy analysis and comparison report generation\n"
        "-> Stage 3: Unknown-outcome resolution, retry state unlocking, and resolution DTO creation"
    )

    # Stage 1: Evidence snapshot
    fr_trd_043()

    # Stage 2: Discrepancy analysis & Comparison
    fr_trd_044()

    # Stage 3: Outcome resolution & DTO creation
    fr_trd_045()
    fr_trd_061()
    fr_trd_062()


if __name__ == "__main__":
    main()
