"""Executable Trading state usage example.

Demonstrates FEAT-TRD-02 Trading state stores, idempotency, and projections.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.trading import (
    apply_execution_event,
    create_idempotency_reservation,
    create_trading_event,
    create_trading_projection,
    create_trading_request,
    get_trading_migrations,
    get_trading_schema_version,
    reserve_idempotency,
)

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)
IdempotencyReservation = Any
TradingEvent = Any
TradingProjection = Any
TradingRequest = Any
TradingRoute = Any
type Scope = tuple[TradingRoute, str, str]


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
            return create_idempotency_reservation(
                **{**existing.model_dump(mode="python"), "status": status}
            )
        reservation = create_idempotency_reservation(
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


def _request() -> TradingRequest:
    """Build one governed request for idempotency usage."""
    return create_trading_request(
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
    return create_trading_event(
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
    return create_trading_projection(
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


def fr_trd_037() -> None:
    """FR-TRD-037: Stage 1 — Represent send attempts and transitions as versioned events."""
    _header("Stage 1: Event Representation - Trading Events (FR-TRD-037)")
    event = _event()
    print(_format_result(event))
    print(f"Data -> event_id='{event.event_id}', event_type='{event.event_type}'")


def fr_trd_038() -> None:
    """FR-TRD-038: Stage 1 — Expose minimal injected store operations."""
    _header("Stage 1: Store Boundary - Injected Store Interface (FR-TRD-038)")
    store = _UsageStore()
    print("Output Result -> _UsageStore : _UsageStore")
    print(f"Data -> reservations_count={len(store.reservations)}")


def fr_trd_039() -> None:
    """FR-TRD-039: Stage 2 — Reserve caller key against canonical material."""
    _header("Stage 2: Idempotency Check - Reserve Key (FR-TRD-039)")
    store = _UsageStore()
    res = reserve_idempotency(
        _request(),
        store,
        reservation_time=NOW,
        retention_seconds=300,
        concurrency_lock_timeout_seconds=Decimal(30),
    )
    print(_format_result(res))
    print(f"Data -> status='{res.status}'")


def fr_trd_040() -> None:
    """FR-TRD-040: Stage 2 — Apply deduplicated authority events to projection."""
    _header("Stage 2: Event Application - Projection Update (FR-TRD-040)")
    store = _UsageStore()
    event = _event()
    store.append_event(event)
    updated_proj = apply_execution_event(event, store)
    print(_format_result(updated_proj))
    print(f"Data -> status='{updated_proj.status}'")


def fr_trd_041() -> None:
    """FR-TRD-041: Stage 1 — Expose current Trading schema version."""
    _header("Stage 1: Schema Version - Current Schema Version (FR-TRD-041)")
    version = get_trading_schema_version()
    print("Output Result -> str : str")
    print(f"Data -> schema_version='{version}'")


def fr_trd_042() -> None:
    """FR-TRD-042: Stage 1 — Provide additive Trading migration definitions."""
    _header("Stage 1: Migrations - Additive Migration Manifest (FR-TRD-042)")
    migrations = get_trading_migrations()
    print(_format_result(migrations))
    print(f"Data -> status='{migrations.status}'")


def fr_trd_051() -> None:
    """FR-TRD-051: Stage 2 — Atomically reserve key and bind receipt."""
    _header("Stage 2: Store Idempotency - Atomic Reservation & Completion (FR-TRD-051)")
    store = _UsageStore()
    res = reserve_idempotency(
        _request(),
        store,
        reservation_time=NOW,
        retention_seconds=300,
        concurrency_lock_timeout_seconds=Decimal(30),
    )
    reservation = res.data
    if reservation is not None:
        store.complete_idempotency(
            reservation.key,
            reservation.material_hash,
            "usage-receipt-001",
            NOW,
            status="completed",
        )
    print(_format_result(reservation))
    print(
        f"Data -> key='{reservation.key if reservation else None}', receipt_id='{store.reservations[reservation.key].receipt_id if reservation else None}'"
    )


def fr_trd_052() -> None:
    """FR-TRD-052: Stage 3 — Append versioned event without rewriting prior events."""
    _header("Stage 3: Event Store - Append Event (FR-TRD-052)")
    store = _UsageStore()
    event = _event()
    store.append_event(event)
    print(_format_result(event))
    print(f"Data -> total_events={len(store.events)}")


def fr_trd_053() -> None:
    """FR-TRD-053: Stage 1 — Load projection for exact scope."""
    _header("Stage 1: Projection Store - Load Projection (FR-TRD-053)")
    store = _UsageStore()
    scope = ("sim", "usage-tenant-001", "simulator")
    proj = store.load_projection(scope)
    print("Output Result -> TradingProjection : TradingProjection")
    print(f"Data -> projection={proj}")


def fr_trd_054() -> None:
    """FR-TRD-054: Stage 3 — Save projection with optimistic version check."""
    _header("Stage 3: Projection Store - Save Projection (FR-TRD-054)")
    store = _UsageStore()
    proj = _projection(version=1)
    store.save_projection(proj, expected_version=0)
    print(_format_result(proj))
    print(f"Data -> saved_version={proj.version}")


def fr_trd_055() -> None:
    """FR-TRD-055: Stage 1 — Return unresolved send attempts."""
    _header("Stage 1: Recovery Store - Unresolved Attempts (FR-TRD-055)")
    store = _UsageStore()
    store.append_event(_event())
    scope = ("sim", "usage-tenant-001", "simulator")
    unresolved = store.load_unresolved_attempts(scope)
    print("Output Result -> tuple : tuple")
    print(f"Data -> unresolved_count={len(unresolved)}")


def fr_trd_057() -> None:
    """FR-TRD-057: Stage 3 — Expose immutable reservation result."""
    _header("Stage 3: Idempotency Result - Reservation Result DTO (FR-TRD-057)")
    reservation = create_idempotency_reservation(
        key="usage-key-001",
        material_hash="a" * 64,
        material_version="v1",
        status="new",
        reserved_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
    )
    print(_format_result(reservation))
    print(f"Data -> key='{reservation.key}', status='{reservation.status}'")


def fr_trd_058() -> None:
    """FR-TRD-058: Stage 3 — Expose scoped projection with optimistic version."""
    _header("Stage 3: Projection DTO - Trading Projection (FR-TRD-058)")
    projection = _projection(version=1)
    print(_format_result(projection))
    print(
        f"Data -> authority_id='{projection.authority_id}', version={projection.version}"
    )


def fr_trd_067() -> None:
    """FR-TRD-067: Stage 1 — Return exact stored report evidence for scope."""
    _header("Stage 1: Evidence Store - Load Report Evidence (FR-TRD-067)")
    store = _UsageStore()
    scope = ("sim", "usage-tenant-001", "simulator")
    evidence = store.load_report_evidence(scope)
    print("Output Result -> dict : dict")
    print(f"Data -> evidence={evidence}")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-TRD-02 — state/ — State and Deterministic Projections\n\n"
        "Purpose: Manage state persistence interfaces, idempotency reservation, event log append, and projection snapshot updates.\n\n"
        "Module flow:\n"
        "-> Stage 1: Store definition, event initialization, schema inspection, and evidence loading\n"
        "-> Stage 2: Idempotency reservation check and fail-closed state validation\n"
        "-> Stage 3: Event appending, atomic projection state updates, and reservation persistence"
    )

    # Stage 1: Store definition & Schema inspection
    fr_trd_037()
    fr_trd_038()
    fr_trd_041()
    fr_trd_042()
    fr_trd_053()
    fr_trd_055()
    fr_trd_067()

    # Stage 2: Idempotency check & Validation
    fr_trd_039()
    fr_trd_040()
    fr_trd_051()

    # Stage 3: Event appending & Projection persistence
    fr_trd_052()
    fr_trd_054()
    fr_trd_057()
    fr_trd_058()


if __name__ == "__main__":
    main()
