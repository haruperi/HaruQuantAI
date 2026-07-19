"""Unit tests for deterministic Trading projections."""

# ruff: noqa: INP001

from datetime import UTC, datetime

import pytest
from app.services.trading.contracts import TradingError
from app.services.trading.state import (
    TradingEvent,
    TradingProjection,
    apply_execution_event,
)
from pydantic import ValidationError

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


class _ProjectionStore:
    """Optimistic in-memory projection fake."""

    def __init__(
        self,
        *,
        fail_read: bool = False,
        fail_write: bool = False,
        foreign_projection: TradingProjection | None = None,
    ) -> None:
        """Initialize empty event and projection state."""
        self.events: list[TradingEvent] = []
        self.projection: TradingProjection | None = None
        self.fail_read = fail_read
        self.fail_write = fail_write
        self.foreign_projection = foreign_projection

    def load_projection(
        self, scope: tuple[object, str, str]
    ) -> TradingProjection | None:
        """Return projection only for its exact scope."""
        if self.fail_read:
            raise RuntimeError("read failed")
        if self.foreign_projection is not None:
            return self.foreign_projection
        if self.projection is None:
            return None
        current_scope = (
            self.projection.route,
            self.projection.tenant_id,
            self.projection.authority_id,
        )
        return self.projection if current_scope == scope else None

    def append_event(self, event: TradingEvent) -> None:
        """Append one immutable event."""
        if self.fail_write:
            raise RuntimeError("write failed")
        self.events.append(event)

    def save_projection(
        self,
        projection: TradingProjection,
        expected_version: int,
    ) -> None:
        """Save if the expected version matches current state."""
        current_version = 0 if self.projection is None else self.projection.version
        if expected_version != current_version:
            raise RuntimeError("stale save")
        self.projection = projection


def _event(
    *,
    event_id: str = "event-001",
    event_type: str = "send_attempted",
    aggregate_version: int = 0,
    payload: dict[str, object] | None = None,
) -> TradingEvent:
    """Build one scoped send-attempt event."""
    return TradingEvent(
        event_id=event_id,
        event_type=event_type,  # type: ignore[arg-type]
        aggregate_version=aggregate_version,
        route="sim",
        tenant_id="tenant-001",
        authority_id="simulator",
        occurred_at=NOW,
        request_id="request-001",
        workflow_id="workflow-001",
        correlation_id="correlation-001",
        payload=payload or {"order_id": "order-001"},
    )


def test_apply_event_rejects_stale_version() -> None:
    """Stale aggregate versions fail before any event is persisted."""
    store = _ProjectionStore()
    with pytest.raises(TradingError) as captured:
        apply_execution_event(_event(aggregate_version=1), store)  # type: ignore[arg-type]
    assert captured.value.trading_code == "VERSION_CONFLICT"
    assert store.events == []
    with pytest.raises(TradingError) as read_failure:
        apply_execution_event(_event(), _ProjectionStore(fail_read=True))  # type: ignore[arg-type]
    assert read_failure.value.trading_code == "PERSISTENCE_FAILED"
    with pytest.raises(TradingError) as write_failure:
        apply_execution_event(_event(), _ProjectionStore(fail_write=True))  # type: ignore[arg-type]
    assert write_failure.value.trading_code == "PERSISTENCE_FAILED"
    foreign = TradingProjection(
        route="sim",
        tenant_id="other-tenant",
        authority_id="simulator",
        version=0,
        orders={},
        positions={},
        fills={},
        receipts={},
        authority_state={},
        updated_at=NOW,
    )
    with pytest.raises(TradingError) as scope_failure:
        apply_execution_event(
            _event(),
            _ProjectionStore(foreign_projection=foreign),  # type: ignore[arg-type]
        )
    assert scope_failure.value.trading_code == "SCOPE_MISMATCH"


def test_projection_requires_scope_and_version() -> None:
    """Projection requires a valid exact scope and non-negative version."""
    with pytest.raises(ValidationError):
        TradingProjection(
            route="sim",
            tenant_id="",
            authority_id="simulator",
            version=-1,
            orders={},
            positions={},
            fills={},
            receipts={},
            authority_state={},
            updated_at=NOW,
        )
    store = _ProjectionStore()
    projected = apply_execution_event(_event(), store)  # type: ignore[arg-type]
    duplicate = apply_execution_event(_event(), store)  # type: ignore[arg-type]
    assert projected.version == 1
    assert duplicate == projected
    receipt = apply_execution_event(
        _event(
            event_id="event-002",
            event_type="receipt_recorded",
            aggregate_version=1,
            payload={"attempt_event_id": "event-001"},
        ),
        store,  # type: ignore[arg-type]
    )
    fill = apply_execution_event(
        _event(
            event_id="event-003",
            event_type="fill_recorded",
            aggregate_version=2,
            payload={"position_id": "position-001", "position": {"size": "1.00"}},
        ),
        store,  # type: ignore[arg-type]
    )
    reconciled = apply_execution_event(
        _event(
            event_id="event-004",
            event_type="reconciliation_transitioned",
            aggregate_version=3,
            payload={"resolved_attempt_event_id": "event-001"},
        ),
        store,  # type: ignore[arg-type]
    )
    assert receipt.unresolved_attempt_ids == ()
    assert fill.positions["position-001"] == {"size": "1.00"}
    assert reconciled.version == 4
