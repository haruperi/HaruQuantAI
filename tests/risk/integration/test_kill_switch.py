"""Workflow integration test for canonical Risk kill-switch control."""

from typing import TYPE_CHECKING, cast

from app.services.risk.contracts import DecisionState, KillSwitchCommand
from app.services.risk.kill_switch import (
    apply_kill_switch_command,
    check_risk_kill_switch,
)

from tests.risk import _support as examples

if TYPE_CHECKING:
    from app.services.risk.audit import RiskAuditChain


def test_kill_switch_command_blocks_trading_without_execution_mutation() -> None:
    """Persist activation, revoke approvals, and leave Trading state untouched."""
    config = examples._config()
    _, approvals, audit = examples._services(config)
    execution_state = {"enabled": True}
    command = KillSwitchCommand(
        action="activate",
        scope_level="global",
        portfolio_id=None,
        strategy_id=None,
        symbol=None,
        reason="operator safety stop",
        requested_at=examples.NOW,
        request_id=examples.REQUEST_ID,
        workflow_id=examples.WORKFLOW_ID,
        correlation_id=examples.CORRELATION_ID,
    )
    active = apply_kill_switch_command(
        command,
        examples._inactive_state(),
        examples._auth(config),
        approvals,
        cast("RiskAuditChain", audit),
        examples._KillStore(),
        config,
        now=examples.NOW,
    )
    decision = check_risk_kill_switch(
        (active,),
        {"portfolio_id": "portfolio-1", "symbol": "EURUSD"},
        config,
        examples._auth(config),
        reconciled=False,
        now=examples.NOW,
    )
    assert active.state == "active"
    assert decision.state is DecisionState.BLOCK
    assert execution_state == {"enabled": True}
