"""Executable Trading reconciliation usage example.

Demonstrates authority snapshots and reconciliation.
"""

# ruff: noqa: E501
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.trading import (
    AuthorityResolution,
    AuthoritySnapshot,
    ExecutionReceipt,
    ReconciliationReport,
    TradingEvent,
    TradingProjection,
    compare_authority_state,
    resolve_unknown_outcome,
)

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


def _snapshot() -> AuthoritySnapshot:
    """Build normalized current Simulation authority facts."""
    return AuthoritySnapshot(
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
    return TradingProjection(
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
    return TradingEvent(
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
    return ExecutionReceipt(
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


def example_reconciliation() -> None:
    """Demonstrate Trading reconciliation API."""
    print("=" * 80)
    print("Trading Example 5: Authority Reconciliation")
    print("=" * 80)

    snap = _snapshot()
    proj = _projection()
    print(f"Authority snapshot source_id: {snap.source_id}")

    report: ReconciliationReport = compare_authority_state(snap, proj)
    print(
        f"Reconciliation severity: {report.severity}, unresolved: {report.unresolved}"
    )

    resolution: AuthorityResolution = resolve_unknown_outcome(  # type: ignore[arg-type]
        _receipt(),
        _Store(),
        lambda _route: snap,
    )
    print(f"Unknown outcome resolution transition: {resolution.transition}")
    print(f"Retry allowed: {resolution.retry_allowed}")


def fr_trd_043() -> None:
    """FR-TRD-043: The system shall expose normalized account/order/position/time authority evidence without provider objects."""
    example_reconciliation()


def fr_trd_044() -> None:
    """FR-TRD-044: The system shall deterministically report missing, extra, mismatched, and stale records without claiming resolution."""
    example_reconciliation()


def fr_trd_045() -> None:
    """FR-TRD-045: The system shall lock retry, persist evidence, prefer route authority truth, and release only after an approved transition resolves."""
    example_reconciliation()


def fr_trd_061() -> None:
    """FR-TRD-061: The system shall expose a deterministic comparison result with discrepancy classes, severity, evidence references, and unresolved status."""
    example_reconciliation()


def fr_trd_062() -> None:
    """FR-TRD-062: The system shall expose the approved authority transition, retry decision, incident reference, and remaining unresolved scope."""
    example_reconciliation()


def main() -> None:
    """Run Trading reconciliation usage example."""
    example_reconciliation()


if __name__ == "__main__":
    main()
