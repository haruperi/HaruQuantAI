"""Unit tests for hierarchical canonical Risk kill-switch policy."""

from datetime import timedelta
from typing import TYPE_CHECKING, cast

import pytest
from app.services.risk.config import compute_config_hash
from app.services.risk.contracts import (
    ApprovalAttestation,
    DecisionState,
    KillSwitchCommand,
    RiskDomainError,
    RiskErrorCode,
)
from app.services.risk.decisions import (
    apply_kill_switch_command,
    check_risk_kill_switch,
)

from tests.risk.usage import test_usage_decisions as examples

if TYPE_CHECKING:
    from app.services.risk.audit import RiskAuditChain


def test_child_clear_cannot_override_active_parent() -> None:
    """Keep an action blocked when global is active and symbol is inactive."""
    config = examples._config()
    parent = examples._inactive_state().model_copy(
        update={"state": "active", "reason": "global safety stop"}
    )
    child = examples._inactive_state("symbol")
    decision = check_risk_kill_switch(
        (child, parent),
        {"portfolio_id": "portfolio-1", "symbol": "EURUSD"},
        config,
        examples._auth(config),
        reconciled=True,
        now=examples.NOW,
    )
    assert decision.state is DecisionState.BLOCK
    assert decision.ordered_checks[0].evidence_refs[0] == parent.state_id


def test_recovery_requires_clear_hierarchy_and_reconciliation() -> None:
    """Require all applicable states inactive plus Trading reconciliation."""
    config = examples._config()
    states = (examples._inactive_state(), examples._inactive_state("symbol"))
    unreconciled = check_risk_kill_switch(
        states,
        {"portfolio_id": "portfolio-1", "symbol": "EURUSD"},
        config,
        examples._auth(config),
        reconciled=False,
        now=examples.NOW,
    )
    recovered = check_risk_kill_switch(
        states,
        {"portfolio_id": "portfolio-1", "symbol": "EURUSD"},
        config,
        examples._auth(config),
        reconciled=True,
        now=examples.NOW,
    )
    assert unreconciled.state is DecisionState.BLOCK
    assert recovered.state is DecisionState.APPROVE


def test_clearance_requires_matching_current_attestation() -> None:
    """Deny unapproved clearance and apply exact authorized evidence."""
    config = examples._config()
    _, approvals, audit = examples._services(config)
    current = examples._inactive_state().model_copy(
        update={"state": "active", "reason": "operator safety stop"}
    )
    command = KillSwitchCommand(
        action="clear",
        scope_level="global",
        portfolio_id=None,
        strategy_id=None,
        symbol=None,
        reason="reconciled and approved",
        requested_at=examples.NOW,
        request_id=examples.REQUEST_ID,
        workflow_id=examples.WORKFLOW_ID,
        correlation_id=examples.CORRELATION_ID,
    )
    with pytest.raises(RiskDomainError) as captured:
        apply_kill_switch_command(
            command,
            current,
            examples._auth(config, clearance=True),
            approvals,
            cast("RiskAuditChain", audit),
            examples._KillStore(),
            config,
            now=examples.NOW,
        )
    assert captured.value.risk_code is RiskErrorCode.PERMISSION_DENIED
    attestation = ApprovalAttestation(
        attestation_id="clearance-1",
        principal_id="operator-1",
        action="risk.kill.clear",
        scope={"global": "*"},
        policy_ref=compute_config_hash(config),
        policy_version=config.policy_version,
        issued_at=examples.NOW,
        expires_at=examples.NOW + timedelta(minutes=1),
        request_id=examples.REQUEST_ID,
        workflow_id=examples.WORKFLOW_ID,
        correlation_id=examples.CORRELATION_ID,
    )
    cleared = apply_kill_switch_command(
        command,
        current,
        examples._auth(config, clearance=True),
        approvals,
        cast("RiskAuditChain", audit),
        examples._KillStore(),
        config,
        attestation=attestation,
        now=examples.NOW,
    )
    assert cleared.state == "inactive"


def test_missing_or_unknown_state_blocks() -> None:
    """Treat absent and explicit unknown applicable state as fail-closed."""
    config = examples._config()
    scope = {"portfolio_id": "portfolio-1", "symbol": "EURUSD"}
    missing = check_risk_kill_switch(
        (),
        scope,
        config,
        examples._auth(config),
        reconciled=True,
        now=examples.NOW,
    )
    unknown_state = examples._inactive_state().model_copy(
        update={"state": "unknown", "reason": "state store unavailable"}
    )
    unknown = check_risk_kill_switch(
        (unknown_state,),
        scope,
        config,
        examples._auth(config),
        reconciled=True,
        now=examples.NOW,
    )
    assert missing.ordered_checks[0].reason_code is RiskErrorCode.KILL_SWITCH_UNKNOWN
    assert unknown.ordered_checks[0].reason_code is RiskErrorCode.KILL_SWITCH_UNKNOWN
