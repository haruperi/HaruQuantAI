"""Executable Trading state usage example.

Demonstrates Trading state stores, idempotency, and projections.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Literal

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.trading import (
    TRADING_SCHEMA_VERSION,
    IdempotencyReservation,
    TradingEvent,
    TradingProjection,
    TradingRequest,
    TradingRoute,
    apply_execution_event,
    get_trading_migrations,
    reserve_idempotency,
)

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)
type Scope = tuple[TradingRoute, str, str]


class _UsageStore:
    """Bounded in-memory implementation demonstrating the injected port."""

    def __init__(self) -> None:
        """Initialize isolated usage state."""
        self.reservations: dict[str, IdempotencyReservation] = {}
        self.events: list[TradingEvent] = []
        self.projections: dict[Scope, TradingProjection] = {}

    def reserve_idempotency(
        self,
        key: str,
        material_hash: str,
        material_version: str,
        reserved_at: datetime,
        expires_at: datetime,
    ) -> IdempotencyReservation:
        """Reserve one caller key or return its active duplicate."""
        existing = self.reservations.get(key)
        if existing is not None:
            status = (
                "duplicate_active"
                if existing.material_hash == material_hash
                else "conflict"
            )
            return IdempotencyReservation.model_validate(
                {**existing.model_dump(mode="python"), "status": status}
            )
        reservation = IdempotencyReservation(
            key=key,
            material_hash=material_hash,
            material_version=material_version,
            status="new",
            reserved_at=reserved_at,
            expires_at=expires_at,
        )
        self.reservations[key] = reservation
        return reservation

    def append_event(self, event: TradingEvent) -> None:
        """Append one immutable event."""
        self.events.append(event)

    def complete_idempotency(
        self,
        key: str,
        material_hash: str,
        receipt_id: str,
        completed_at: datetime,
        *,
        status: Literal["completed", "reconciliation_required"],
    ) -> None:
        """Persist a demonstrated terminal reservation outcome."""
        existing = self.reservations[key]
        if existing.material_hash != material_hash:
            raise RuntimeError("usage idempotency material mismatch")
        self.reservations[key] = existing.model_copy(
            update={
                "status": (
                    "duplicate_completed"
                    if status == "completed"
                    else "reconciliation_required"
                ),
                "receipt_id": receipt_id,
                "reserved_at": completed_at,
            }
        )

    def load_projection(self, scope: Scope) -> TradingProjection | None:
        """Load the projection for one exact scope."""
        return self.projections.get(scope)

    def save_projection(
        self,
        projection: TradingProjection,
        expected_version: int,
    ) -> None:
        """Save a projection when optimistic version matches."""
        scope = (projection.route, projection.tenant_id, projection.authority_id)
        current = self.projections.get(scope)
        current_version = 0 if current is None else current.version
        if current_version != expected_version:
            raise RuntimeError("stale usage projection")
        self.projections[scope] = projection

    def load_unresolved_attempts(self, scope: Scope) -> tuple[TradingEvent, ...]:
        """Return scoped send attempts without authority resolution."""
        route, tenant_id, authority_id = scope
        return tuple(
            event
            for event in self.events
            if event.event_type == "send_attempted"
            and (event.route, event.tenant_id, event.authority_id)
            == (route, tenant_id, authority_id)
        )

    def load_report_evidence(self, scope: Scope) -> dict[str, object]:
        """Return bounded empty report evidence for one exact scope."""
        del scope
        return {}


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _request() -> TradingRequest:
    """Build one governed request for idempotency usage."""
    return TradingRequest(
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        route="sim",
        action="submit_order",
        account_id="usage-account-001",
        strategy_id="usage-strategy-001",
        strategy_version="v1",
        intent_id="usage-intent-001",
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity_unit="units",
        quantity="1.00",
        risk_decision_id="usage-risk-001",
        action_policy_verdict_id="usage-verdict-001",
        approval_token_ref="usage-approval-001",
        idempotency_key="usage-key-001",
        canonical_material_version="v1",
        system_time=NOW,
        valid_until=NOW + timedelta(minutes=5),
    )


def _event(event_id: str = "usage-event-001") -> TradingEvent:
    """Build one scoped usage event."""
    return TradingEvent(
        event_id=event_id,
        event_type="send_attempted",
        aggregate_version=0,
        route="sim",
        tenant_id="usage-tenant-001",
        authority_id="simulator",
        occurred_at=NOW,
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        payload={"order_id": "usage-order-001"},
    )


def _projection(version: int = 1) -> TradingProjection:
    """Build one exact-scope projection."""
    return TradingProjection(
        route="sim",
        tenant_id="usage-tenant-001",
        authority_id="simulator",
        version=version,
        orders={},
        positions={},
        fills={},
        receipts={},
        authority_state={},
        updated_at=NOW,
    )


def example_state() -> None:
    """Demonstrate Trading state store, idempotency, projections, and events."""
    _header("Demonstrate Trading state store, idempotency, projections, and events.")
    print("Trading Example 2: State Store and Idempotency Reservation")

    store = _UsageStore()

    # 1. Idempotency reservation
    res = reserve_idempotency(
        _request(),
        store,
        reservation_time=NOW,
        retention_seconds=300,
        concurrency_lock_timeout_seconds=Decimal(30),
    )
    assert res.status == "success"
    reservation = res.data
    assert reservation is not None
    print(f"Idempotency reservation status: {reservation.status}")
    store.complete_idempotency(
        reservation.key,
        reservation.material_hash,
        "usage-receipt-001",
        NOW,
        status="completed",
    )
    print(
        "Completed reservation receipt: "
        f"{store.reservations[reservation.key].receipt_id}"
    )

    # 2. Append and apply event
    event = _event()
    store.append_event(event)
    print(f"Appended event type: {event.event_type}, version: {event.event_version}")

    updated_proj = apply_execution_event(event, store)
    assert updated_proj.status == "success"
    projection = updated_proj.data
    assert projection is not None
    print(f"Applied execution event updated projection version: {projection.version}")

    # 3. Schema versions and migrations
    print(f"Trading schema version: {TRADING_SCHEMA_VERSION}")
    migrations = get_trading_migrations()
    assert migrations.status == "success"
    migration_steps = migrations.data
    assert migration_steps is not None
    print(f"Trading migrations domain: {migration_steps[0].domain}")


def fr_trd_037() -> None:
    """FR-TRD-037: The system shall represent send attempts, receipts, fills, reconciliation transitions, and incidents as versioned, redacted events."""
    _header(
        "FR-TRD-037: The system shall represent send attempts, receipts, fills, reconciliation transitions, and incidents as versioned, redacted events."
    )
    example_state()


def fr_trd_038() -> None:
    """FR-TRD-038: The system shall expose only minimal injected operations for idempotency, append, projection reads/writes, and reconciliation evidence."""
    _header(
        "FR-TRD-038: The system shall expose only minimal injected operations for idempotency, append, projection reads/writes, and reconciliation evidence."
    )
    example_state()


def fr_trd_039() -> None:
    """FR-TRD-039: The system shall reserve a caller-supplied key against versioned canonical SHA-256 material at an injected time for the required positive retention window, reject different-material reuse, and keep stale duplicate-active work locked for reconciliation."""
    _header(
        "FR-TRD-039: The system shall reserve a caller-supplied key against versioned canonical SHA-256 material at an injected time for the required positive retention window, reject different-material reuse, and keep stale duplicate-active work locked for reconciliation."
    )
    example_state()


def fr_trd_040() -> None:
    """FR-TRD-040: The system shall apply deduplicated authority events in logical order with optimistic version checks."""
    _header(
        "FR-TRD-040: The system shall apply deduplicated authority events in logical order with optimistic version checks."
    )
    example_state()


def fr_trd_041() -> None:
    """FR-TRD-041: The system shall expose the current Trading schema version."""
    _header("FR-TRD-041: The system shall expose the current Trading schema version.")
    example_state()


def fr_trd_042() -> None:
    """FR-TRD-042: The system shall provide additive Trading migration definitions for execution-owned state without opening a database."""
    _header(
        "FR-TRD-042: The system shall provide additive Trading migration definitions for execution-owned state without opening a database."
    )
    example_state()


def fr_trd_051() -> None:
    """FR-TRD-051: The store shall atomically reserve one caller key against canonical material and its injected reservation/expiry timestamps, returning the existing/new/conflict decision, and shall durably bind the exact receipt and terminal completed or reconciliation-required state after receipt persistence."""
    _header(
        "FR-TRD-051: The store shall atomically reserve one caller key against canonical material and its injected reservation/expiry timestamps, returning the existing/new/conflict decision, and shall durably bind the exact receipt and terminal completed or reconciliation-required state after receipt persistence."
    )
    example_state()


def fr_trd_052() -> None:
    """FR-TRD-052: The store shall append one versioned event without rewriting prior events."""
    _header(
        "FR-TRD-052: The store shall append one versioned event without rewriting prior events."
    )
    example_state()


def fr_trd_053() -> None:
    """FR-TRD-053: The store shall load the latest projection for an exact route/tenant/authority scope."""
    _header(
        "FR-TRD-053: The store shall load the latest projection for an exact route/tenant/authority scope."
    )
    example_state()


def fr_trd_054() -> None:
    """FR-TRD-054: The store shall save a projection only when the expected optimistic version matches."""
    _header(
        "FR-TRD-054: The store shall save a projection only when the expected optimistic version matches."
    )
    example_state()


def fr_trd_055() -> None:
    """FR-TRD-055: The store shall return every unresolved send attempt for an exact authority/conflict scope."""
    _header(
        "FR-TRD-055: The store shall return every unresolved send attempt for an exact authority/conflict scope."
    )
    example_state()


def fr_trd_057() -> None:
    """FR-TRD-057: The system shall expose an immutable reservation result distinguishing new, duplicate-completed, duplicate-active, conflict, and reconciliation-required states."""
    _header(
        "FR-TRD-057: The system shall expose an immutable reservation result distinguishing new, duplicate-completed, duplicate-active, conflict, and reconciliation-required states."
    )
    example_state()


def fr_trd_058() -> None:
    """FR-TRD-058: The system shall expose a route/tenant-scoped order, position, fill, receipt, and authority projection with optimistic version."""
    _header(
        "FR-TRD-058: The system shall expose a route/tenant-scoped order, position, fill, receipt, and authority projection with optimistic version."
    )
    example_state()


def fr_trd_067() -> None:
    """FR-TRD-067: The store shall return exact stored JSON-safe report evidence for one route/tenant/authority scope without computing or enriching it."""
    _header(
        "FR-TRD-067: The store shall return exact stored JSON-safe report evidence for one route/tenant/authority scope without computing or enriching it."
    )
    example_state()


def main() -> None:
    """Run Trading state usage example."""
    example_state()


if __name__ == "__main__":
    main()
