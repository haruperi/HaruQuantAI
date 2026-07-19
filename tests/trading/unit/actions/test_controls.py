"""Unit tests for Trading controls and Risk-owned kill-switch transitions."""

# ruff: noqa: ARG005, INP001

from dataclasses import replace
from datetime import timedelta

import pytest
from app.services.risk.contracts import KillSwitchState
from app.services.trading.actions import (
    clear_kill_switch,
    pause_strategy,
    resume_strategy,
    sync_positions,
    trigger_kill_switch,
)
from app.services.trading.contracts import TradingError
from app.services.trading.reconciliation import AuthoritySnapshot
from app.services.trading.state import TradingProjection
from tests.trading.unit.actions.test_dependencies import (
    NOW,
    MemoryStore,
    dependencies,
    policy,
    request,
)


@pytest.fixture
def anyio_backend() -> str:
    """Select the installed asyncio AnyIO backend."""
    return "asyncio"


def projection() -> TradingProjection:
    """Build one empty reconciled Simulation projection."""
    return TradingProjection(
        route="sim",
        tenant_id="account-001",
        authority_id="simulation",
        version=1,
        orders={},
        positions={},
        fills={},
        receipts={},
        authority_state={},
        updated_at=NOW,
    )


def authority() -> AuthoritySnapshot:
    """Build matching current read-only route authority evidence."""
    return AuthoritySnapshot(
        route="sim",
        authority_id="simulation",
        account_id="account-001",
        source_id="simulation-read-port",
        account={},
        orders={},
        positions={},
        observed_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
    )


def switch(level: str, state: str = "inactive") -> KillSwitchState:
    """Build one canonical Risk kill-switch state."""
    scope = {} if level == "global" else {"id": "scope-001"}
    return KillSwitchState(
        state_id=f"switch-{level}",
        scope_level=level,
        scope=scope,
        state=state,
        reason="test state",
        version=1,
        updated_at=NOW,
    )


@pytest.mark.anyio
async def test_pause_does_not_promote_strategy() -> None:
    """Pause records Trading admission state without Strategy lifecycle mutation."""
    item = request(action="pause_strategy")
    outcome = await pause_strategy(
        item, dependencies(action_policy=policy("pause_strategy"))
    )
    assert outcome.status == "success"
    assert "lifecycle" not in str(outcome.data)


@pytest.mark.anyio
async def test_resume_requires_cleared_hierarchy_and_reconciliation() -> None:
    """Resume blocks on any active applicable Risk scope."""
    item = request(action="resume_strategy")
    deps = dependencies(action_policy=policy("resume_strategy"))
    deps = replace(
        deps, kill_switch_state_source=lambda value: (switch("global", "active"),)
    )
    with pytest.raises(TradingError, match="KILL_SWITCH_ACTIVE"):
        await resume_strategy(item, deps)


@pytest.mark.anyio
async def test_resume_succeeds_with_clear_hierarchy_and_route_truth() -> None:
    """Resume records admission only after reconciliation matches."""
    store = MemoryStore()
    store.projection = projection()
    deps = dependencies(store=store, action_policy=policy("resume_strategy"))
    deps = replace(
        deps,
        kill_switch_state_source=lambda value: (switch("global"),),
        reconciliation_source=lambda value: authority(),
    )
    assert (
        await resume_strategy(request(action="resume_strategy"), deps)
    ).status == "success"


@pytest.mark.anyio
async def test_sync_is_route_read_only() -> None:
    """Synchronization reads authority and writes only Trading evidence."""
    deps = replace(dependencies(), reconciliation_source=lambda value: authority())
    outcome = await sync_positions(request(action="sync_positions"), deps)
    assert outcome.status == "success"
    assert outcome.data["unresolved"] is True


@pytest.mark.anyio
async def test_request_text_cannot_self_classify_emergency() -> None:
    """Trigger requires typed Risk policy even when reason claims emergency."""
    item = request(
        action="trigger_kill_switch",
        scope_level="global",
        control_reason="emergency",
    )
    deps = replace(dependencies(), action_policy_source=lambda value: None)
    with pytest.raises(TradingError, match="PERMISSION_DENIED"):
        await trigger_kill_switch(item, deps)


@pytest.mark.anyio
async def test_clear_cannot_override_active_parent() -> None:
    """An active global parent blocks symbol-level clearance."""
    item = request(
        action="clear_kill_switch",
        scope_level="symbol",
        control_reason="operator reviewed",
    )
    deps = dependencies(action_policy=policy("clear_kill_switch"))
    deps = replace(
        deps, kill_switch_state_source=lambda value: (switch("global", "active"),)
    )
    with pytest.raises(TradingError, match="KILL_SWITCH_ACTIVE"):
        await clear_kill_switch(item, deps)
