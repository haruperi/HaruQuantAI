"""Executable Trading state usage example.

Demonstrates Trading state stores, idempotency, and projections.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.trading.contracts import TradingRequest, TradingRoute
from app.services.trading.state import (
    TRADING_SCHEMA_VERSION,
    IdempotencyReservation,
    TradingEvent,
    TradingProjection,
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


def _request() -> TradingRequest:
    """Build one governed request for idempotency usage."""
    return TradingRequest(
        request_id="usage-request-001",
        workflow_id="usage-workflow-001",
        correlation_id="usage-correlation-001",
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
        request_id="usage-request-001",
        workflow_id="usage-workflow-001",
        correlation_id="usage-correlation-001",
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
    print("=" * 80)
    print("Trading Example 2: State Store and Idempotency Reservation")
    print("=" * 80)

    store = _UsageStore()

    # 1. Idempotency reservation
    res = reserve_idempotency(
        _request(),
        store,
        reservation_time=NOW,
        retention_seconds=300,
        concurrency_lock_timeout_seconds=Decimal(30),
    )
    print(f"Idempotency reservation status: {res.status}")

    # 2. Append and apply event
    event = _event()
    store.append_event(event)
    print(f"Appended event type: {event.event_type}, version: {event.event_version}")

    updated_proj = apply_execution_event(event, store)
    print(f"Applied execution event updated projection version: {updated_proj.version}")

    # 3. Schema versions and migrations
    print(f"Trading schema version: {TRADING_SCHEMA_VERSION}")
    migrations = get_trading_migrations()
    print(f"Trading migrations domain: {migrations[0].domain}")


def main() -> None:
    """Run Trading state usage example."""
    example_state()


if __name__ == "__main__":
    main()
