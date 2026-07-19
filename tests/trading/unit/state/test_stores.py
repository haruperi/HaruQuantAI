"""Contract tests for the injected TradingStateStore port."""

# ruff: noqa: INP001

from datetime import UTC, datetime

import pytest
from app.services.trading.state import (
    IdempotencyReservation,
    TradingEvent,
    TradingProjection,
    TradingStateStore,
)


class _MemoryStore:
    """Small stateful store used only to exercise the public port contract."""

    def __init__(self) -> None:
        """Initialize isolated in-memory contract evidence."""
        self.reservations: dict[str, IdempotencyReservation] = {}
        self.events: list[TradingEvent] = []
        self.projections: dict[tuple[object, str, str], TradingProjection] = {}

    def reserve_idempotency(
        self,
        key: str,
        material_hash: str,
        material_version: str,
        reserved_at: datetime,
        expires_at: datetime,
    ) -> IdempotencyReservation:
        """Reserve one key atomically for test purposes."""
        existing = self.reservations.get(key)
        if existing is not None:
            status = (
                "duplicate_active"
                if existing.material_hash == material_hash
                else "conflict"
            )
            return existing.model_copy(update={"status": status})
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
        """Append one event and reject duplicate identity."""
        if any(item.event_id == event.event_id for item in self.events):
            raise RuntimeError("duplicate event")
        self.events.append(event)

    def load_projection(
        self, scope: tuple[object, str, str]
    ) -> TradingProjection | None:
        """Load only an exact-scope projection."""
        return self.projections.get(scope)

    def save_projection(
        self,
        projection: TradingProjection,
        expected_version: int,
    ) -> None:
        """Save only when optimistic version matches."""
        scope = (projection.route, projection.tenant_id, projection.authority_id)
        current = self.projections.get(scope)
        current_version = 0 if current is None else current.version
        if current_version != expected_version:
            raise RuntimeError("stale projection")
        self.projections[scope] = projection

    def load_unresolved_attempts(
        self, scope: tuple[object, str, str]
    ) -> tuple[TradingEvent, ...]:
        """Return unresolved attempts only for the exact scope."""
        route, tenant_id, authority_id = scope
        return tuple(
            event
            for event in self.events
            if event.event_type == "send_attempted"
            and event.route == route
            and event.tenant_id == tenant_id
            and event.authority_id == authority_id
        )

    def load_report_evidence(self, scope: tuple[object, str, str]) -> dict[str, object]:
        """Return exact scope evidence without enrichment."""
        return {"scope": list(scope)}


def _event(event_id: str = "event-001", tenant_id: str = "tenant-001") -> TradingEvent:
    """Build a valid send-attempt event."""
    return TradingEvent(
        event_id=event_id,
        event_type="send_attempted",
        aggregate_version=0,
        route="sim",
        tenant_id=tenant_id,
        authority_id="simulator",
        occurred_at=datetime(2026, 7, 19, 8, 0, tzinfo=UTC),
        request_id="request-001",
        workflow_id="workflow-001",
        correlation_id="correlation-001",
        payload={"order_id": "order-001"},
    )


def _projection(tenant_id: str = "tenant-001", version: int = 1) -> TradingProjection:
    """Build a valid scoped projection."""
    return TradingProjection(
        route="sim",
        tenant_id=tenant_id,
        authority_id="simulator",
        version=version,
        orders={},
        positions={},
        fills={},
        receipts={},
        authority_state={},
        updated_at=datetime(2026, 7, 19, 8, 0, tzinfo=UTC),
    )


def test_store_contract_failure_is_visible() -> None:
    """The public port does not silently absorb implementation failures."""
    store: TradingStateStore = _MemoryStore()  # type: ignore[assignment]
    store.append_event(_event())
    with pytest.raises(RuntimeError, match="duplicate event"):
        store.append_event(_event())


def test_reserve_idempotency_is_atomic() -> None:
    """Same-key calls return same-material duplicate or conflict decisions."""
    store = _MemoryStore()
    first = store.reserve_idempotency(
        "key-001",
        "a" * 64,
        "v1",
        datetime(2026, 7, 19, 8, 0, tzinfo=UTC),
        datetime(2026, 7, 19, 9, 0, tzinfo=UTC),
    )
    duplicate = store.reserve_idempotency(
        "key-001",
        "a" * 64,
        "v1",
        datetime(2026, 7, 19, 8, 0, tzinfo=UTC),
        datetime(2026, 7, 19, 9, 0, tzinfo=UTC),
    )
    conflict = store.reserve_idempotency(
        "key-001",
        "b" * 64,
        "v1",
        datetime(2026, 7, 19, 8, 0, tzinfo=UTC),
        datetime(2026, 7, 19, 9, 0, tzinfo=UTC),
    )
    assert (first.status, duplicate.status, conflict.status) == (
        "new",
        "duplicate_active",
        "conflict",
    )


def test_append_event_is_append_only() -> None:
    """Existing event identity cannot be rewritten or appended twice."""
    store = _MemoryStore()
    store.append_event(_event())
    with pytest.raises(RuntimeError, match="duplicate event"):
        store.append_event(_event())


def test_load_projection_is_scope_isolated() -> None:
    """Projection reads use exact route, tenant, and authority scope."""
    store = _MemoryStore()
    projection = _projection()
    store.save_projection(projection, 0)
    assert store.load_projection((projection.route, "tenant-001", "simulator"))
    assert store.load_projection((projection.route, "tenant-002", "simulator")) is None


def test_save_projection_rejects_stale_version() -> None:
    """Projection writes reject stale optimistic expected versions."""
    store = _MemoryStore()
    store.save_projection(_projection(), 0)
    with pytest.raises(RuntimeError, match="stale projection"):
        store.save_projection(_projection(version=2), 0)


def test_unresolved_attempts_are_scope_isolated() -> None:
    """Unresolved attempt reads never mix tenant conflict scopes."""
    store = _MemoryStore()
    store.append_event(_event("event-001", "tenant-001"))
    store.append_event(_event("event-002", "tenant-002"))
    loaded = store.load_unresolved_attempts(("sim", "tenant-001", "simulator"))
    assert tuple(item.event_id for item in loaded) == ("event-001",)


def test_report_evidence_is_scope_isolated() -> None:
    """Report evidence is returned for the exact requested scope."""
    store = _MemoryStore()
    scope = ("sim", "tenant-001", "simulator")
    assert store.load_report_evidence(scope) == {"scope": list(scope)}
