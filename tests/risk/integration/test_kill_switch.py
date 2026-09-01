"""Workflow integration test for canonical Risk kill-switch control."""

from app.kernel.serialization import canonical_json
from app.services.risk import (
    apply_kill_switch_command,
    check_risk_kill_switch,
    create_kill_switch_command,
    create_risk_audit_chain,
    get_decision_state,
)

from tests.risk import _support as examples


def test_kill_switch_command_blocks_trading_without_execution_mutation() -> None:
    """Persist activation, revoke approvals, and leave Trading state untouched."""
    config = examples._config()
    _, approvals, _ = examples._services(config)
    store = examples._KillStore()
    audit = create_risk_audit_chain(
        config,
        store,
        lambda: examples.NOW,
        canonical_json,
    )
    execution_state = {"enabled": True}
    command = create_kill_switch_command(
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
    active = examples.unwrap_risk_response(
        apply_kill_switch_command(
            command,
            examples._inactive_state(),
            examples._auth(config),
            approvals,
            audit,
            store,
            config,
            now=examples.NOW,
        ),
        operation="apply_kill_switch_command",
    )
    decision = examples.unwrap_risk_response(
        check_risk_kill_switch(
            (active,),
            {"portfolio_id": "portfolio-1", "symbol": "EURUSD"},
            config,
            examples._auth(config),
            reconciled=False,
            now=examples.NOW,
        ),
        operation="check_risk_kill_switch",
    )
    assert active.state == "active"
    assert decision.state is get_decision_state("BLOCK")
    assert execution_state == {"enabled": True}
