"""Integration evidence for governed strategy-route pause and resume."""

from dataclasses import replace

import pytest
from app.services.trading import (
    create_authority_snapshot,
    create_execution_position,
    create_execution_position_store,
    create_trading_projection,
    get_execution_position_snapshot,
    pause_strategy,
    resume_strategy,
    set_execution_position,
)

from tests.trading.conftest import (
    NOW,
    MemoryStore,
    action_policy,
    inactive_kill_switch_hierarchy,
    trading_dependencies,
    trading_request,
)


@pytest.mark.anyio
async def test_pause_resume_preserves_orders_and_positions() -> None:
    """Pause/resume mutates admission evidence without broker mutation."""
    store = MemoryStore()
    store.projection = create_trading_projection(
        route="sim",
        tenant_id="account-001",
        authority_id="simulation",
        version=1,
        orders={"order-001": {"state": "pending"}},
        positions={},
        fills={},
        receipts={},
        authority_state={},
        updated_at=NOW,
    )
    positions = create_execution_position_store()
    set_execution_position(
        positions,
        create_execution_position(
            position_id="position-001",
            account_id="account-001",
            symbol="EURUSD",
            broker_position_id="position-001",
            state="OPEN",
            quantity="1.00",
            source_sequence=1,
            version=1,
        ),
    )
    pause_dependencies = replace(
        trading_dependencies(
            store=store,
            action_policy=action_policy("pause_strategy"),
        ),
        execution_positions=positions,
    )
    pause = await pause_strategy(
        trading_request(action="pause_strategy"),
        pause_dependencies,
    )
    assert pause.status == "success"
    before = store.projection
    resume_dependencies = replace(
        trading_dependencies(
            store=store,
            action_policy=action_policy("resume_strategy"),
        ),
        execution_positions=positions,
        kill_switch_state_source=inactive_kill_switch_hierarchy,
        reconciliation_source=lambda _request: create_authority_snapshot(
            route="sim",
            authority_id="simulation",
            account_id="account-001",
            source_id="simulation-read-port",
            account={},
            orders={"order-001": {"state": "pending"}},
            positions=get_execution_position_snapshot(positions),
            observed_at=NOW,
            expires_at=trading_request().valid_until,
        ),
    )
    resume = await resume_strategy(
        trading_request(action="resume_strategy"),
        resume_dependencies,
    )
    assert resume.status == "success"
    assert store.projection is not None
    assert before is not None
    assert store.projection.orders == before.orders
    assert get_execution_position_snapshot(positions)["position-001"]["state"] == "OPEN"
    assert not store.projection.receipts
