"""Unit tests for route-aware Trading order actions."""

from dataclasses import replace

import pytest
from app.services.brokers import get_broker_error_code
from app.services.trading.actions import cancel_order, modify_order, submit_order
from app.services.trading.contracts import TradingRoute
from app.services.trading.monitoring import OperationalEvent

from tests.trading.unit.actions.test_controls import authority as authority_snapshot
from tests.trading.unit.actions.test_dependencies import (
    dependencies,
    execution_store,
    request,
)
from tests.trading.unit.routing.test_dispatcher import _Adapter, _ErrorAdapter


@pytest.fixture
def anyio_backend() -> str:
    """Select the installed asyncio AnyIO backend."""
    return "asyncio"


@pytest.mark.anyio
async def test_submit_order_route_parity() -> None:
    """Simulation dispatches while a Broker route without a session fails closed."""
    outcome = await submit_order(request(), dependencies())
    assert outcome.status == "success"
    assert outcome.metadata.extensions["legacy_status"] == "sent"
    live = request(route=TradingRoute.LIVE, provider_id="mt5")
    result = await submit_order(live, dependencies())
    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "SERVICE_UNAVAILABLE"


@pytest.mark.anyio
async def test_completed_idempotency_replay_does_not_dispatch() -> None:
    """A completed reservation returns its receipt without another mutation."""
    store = execution_store()
    adapter = _Adapter(broker="sim", environment="simulation")
    deps = replace(dependencies(store=store), broker_adapter=adapter)
    item = request()

    first = await submit_order(item, deps)
    replay = await submit_order(item, deps)

    assert first.status == "success"
    assert first.metadata.extensions["legacy_status"] == "sent"
    assert replay.status == "success"
    assert replay.data is not None
    assert replay.data.receipt_id == store.reservations[item.idempotency_key].receipt_id
    assert adapter.calls == 1


@pytest.mark.anyio
async def test_simulation_requires_current_typed_risk_authority() -> None:
    """Simulation mutation fails closed when current Risk authority is absent."""
    deps = replace(
        dependencies(),
        execution_risk_decision_source=lambda _item: None,
    )
    result = await submit_order(request(), deps)
    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "GATE_BLOCKED"


@pytest.mark.anyio
async def test_unknown_outcome_persists_lock_before_critical_event() -> None:
    """An uncertain mutation is durably retry-locked before critical publication."""
    item = request()
    store = execution_store()
    published: list[OperationalEvent] = []

    def event_sink(event: OperationalEvent) -> None:
        """Observe that reconciliation transition precedes publication."""
        assert store.events[-1].event_type == "reconciliation_transitioned"
        published.append(event)

    base = dependencies(store=store)
    authority = authority_snapshot()
    authority = authority.model_copy(
        update={"orders": {"authority-only": {"state": "pending"}}}
    )
    deps = replace(
        base,
        broker_adapter=_ErrorAdapter(
            get_broker_error_code("BROKER_RATE_LIMITED"),
            broker="sim",
            environment="simulation",
        ),
        reconciliation_source=lambda _value: authority,
        event_sink=event_sink,
    )

    outcome = await submit_order(item, deps)

    assert outcome.status == "error"
    assert outcome.error is not None
    assert outcome.error.code == "UNKNOWN_OUTCOME"
    assert outcome.metadata.extensions["legacy_status"] == "unknown_outcome"
    assert "receipt" in outcome.error.details
    assert store.reservations[item.idempotency_key].status == "reconciliation_required"
    assert store.projection is not None
    assert store.projection.unresolved_attempt_ids
    assert [event.event_type for event in published] == ["BROKER_STATE_UNKNOWN"]


@pytest.mark.anyio
async def test_modify_order_rejects_stale_version() -> None:
    """Order modification requires explicit optimistic version evidence."""
    item = request(
        action="modify_order",
        order_id="order-001",
        target_broker_order_id="order-001",
        expected_version=None,
    )
    result = await modify_order(item, dependencies())
    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "VERSION_CONFLICT"


@pytest.mark.anyio
async def test_cancel_order_is_idempotent() -> None:
    """Repeated cancellation cannot cause a second authority mutation."""
    store = execution_store()
    deps = dependencies(store=store)
    item = request(
        action="cancel_order",
        order_id="order-001",
        target_broker_order_id="order-001",
        expected_version=1,
    )
    first = await cancel_order(item, deps)
    assert first.status == "success"
    assert first.metadata.extensions["legacy_status"] == "cancelled"
    replay = await cancel_order(item, deps)
    assert replay.status == "error"
    assert replay.error is not None
    assert replay.error.code == "VERSION_CONFLICT"
    assert tuple(event.event_type for event in store.events) == (
        "send_attempted",
        "receipt_recorded",
    )


@pytest.mark.anyio
async def test_order_verbs_reject_mismatched_actions() -> None:
    """Each order verb accepts only its exact canonical action."""
    result = await cancel_order(request(), dependencies())
    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "INVALID_REQUEST"
