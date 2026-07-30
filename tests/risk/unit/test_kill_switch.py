"""Unit tests for hierarchical canonical Risk kill-switch policy."""

from datetime import timedelta

from app.services.risk import create_risk_audit_chain
from app.services.risk.config import compute_config_hash
from app.services.risk.contracts import (
    ApprovalAttestation,
    DecisionState,
    KillSwitchCommand,
    RiskErrorCode,
)
from app.services.risk.contracts.responses import unwrap_risk_response
from app.services.risk.kill_switch import (
    apply_kill_switch_command,
    check_risk_kill_switch,
)
from app.utils import canonical_json

from tests.risk import _support as examples


def test_child_clear_cannot_override_active_parent() -> None:
    """Keep an action blocked when global is active and symbol is inactive."""
    config = examples._config()
    parent = examples._inactive_state().model_copy(
        update={"state": "active", "reason": "global safety stop"}
    )
    child = examples._inactive_state("symbol")
    decision = unwrap_risk_response(
        check_risk_kill_switch(
            (child, parent),
            {"portfolio_id": "portfolio-1", "symbol": "EURUSD"},
            config,
            examples._auth(config),
            reconciled=True,
            now=examples.NOW,
        ),
        operation="check_risk_kill_switch",
    )
    assert decision.state is DecisionState.BLOCK
    assert decision.ordered_checks[0].evidence_refs[0] == parent.state_id


def test_recovery_requires_clear_hierarchy_and_reconciliation() -> None:
    """Require all applicable states inactive plus Trading reconciliation."""
    config = examples._config()
    states = (examples._inactive_state(), examples._inactive_state("symbol"))
    unreconciled = unwrap_risk_response(
        check_risk_kill_switch(
            states,
            {"portfolio_id": "portfolio-1", "symbol": "EURUSD"},
            config,
            examples._auth(config),
            reconciled=False,
            now=examples.NOW,
        ),
        operation="check_risk_kill_switch",
    )
    recovered = unwrap_risk_response(
        check_risk_kill_switch(
            states,
            {"portfolio_id": "portfolio-1", "symbol": "EURUSD"},
            config,
            examples._auth(config),
            reconciled=True,
            now=examples.NOW,
        ),
        operation="check_risk_kill_switch",
    )
    assert unreconciled.state is DecisionState.BLOCK
    assert recovered.state is DecisionState.APPROVE


def test_clearance_requires_matching_current_attestation() -> None:
    """Deny unapproved clearance and apply exact authorized evidence."""
    config = examples._config()
    _, approvals, _ = examples._services(config)
    store = examples._KillStore()
    audit = create_risk_audit_chain(
        config,
        store,
        lambda: examples.NOW,
        canonical_json,
    )
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
    response = apply_kill_switch_command(
        command,
        current,
        examples._auth(config, clearance=True),
        approvals,
        audit,
        store,
        config,
        now=examples.NOW,
    )
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == RiskErrorCode.PERMISSION_DENIED.value
    attestation = ApprovalAttestation(
        attestation_id="clearance-1",
        principal_id="operator-2",
        action="risk.kill.clear",
        scope={"global": "*"},
        policy_ref=examples._risk_value(
            compute_config_hash(config), "compute_config_hash"
        ),
        policy_version=config.policy_version,
        issued_at=examples.NOW,
        expires_at=examples.NOW + timedelta(minutes=1),
        request_id=examples.REQUEST_ID,
        workflow_id=examples.WORKFLOW_ID,
        correlation_id=examples.CORRELATION_ID,
    )
    cleared = unwrap_risk_response(
        apply_kill_switch_command(
            command,
            current,
            examples._auth(config, clearance=True),
            approvals,
            audit,
            store,
            config,
            attestation=attestation,
            now=examples.NOW,
        ),
        operation="apply_kill_switch_command",
    )
    assert cleared.state == "inactive"
    assert store.state == cleared
    assert len(store.records) == 1


def test_clearance_requires_distinct_principal() -> None:
    """Reject same-principal clearance without changing state or audit."""
    config = examples._config()
    _, approvals, _ = examples._services(config)
    store = examples._KillStore()
    audit = create_risk_audit_chain(
        config,
        store,
        lambda: examples.NOW,
        canonical_json,
    )
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
    attestation = ApprovalAttestation(
        attestation_id="clearance-same-principal",
        principal_id="operator-1",
        action="risk.kill.clear",
        scope={"global": "*"},
        policy_ref=examples._risk_value(
            compute_config_hash(config), "compute_config_hash"
        ),
        policy_version=config.policy_version,
        issued_at=examples.NOW,
        expires_at=examples.NOW + timedelta(minutes=1),
        request_id=examples.REQUEST_ID,
        workflow_id=examples.WORKFLOW_ID,
        correlation_id=examples.CORRELATION_ID,
    )

    response = apply_kill_switch_command(
        command,
        current,
        examples._auth(config, clearance=True),
        approvals,
        audit,
        store,
        config,
        attestation=attestation,
        now=examples.NOW,
    )

    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == RiskErrorCode.PERMISSION_DENIED.value
    assert store.state is None
    assert store.records == []


def test_missing_or_unknown_state_blocks() -> None:
    """Treat absent and explicit unknown applicable state as fail-closed."""
    config = examples._config()
    scope = {"portfolio_id": "portfolio-1", "symbol": "EURUSD"}
    missing = unwrap_risk_response(
        check_risk_kill_switch(
            (),
            scope,
            config,
            examples._auth(config),
            reconciled=True,
            now=examples.NOW,
        ),
        operation="check_risk_kill_switch",
    )
    unknown_state = examples._inactive_state().model_copy(
        update={"state": "unknown", "reason": "state store unavailable"}
    )
    unknown = unwrap_risk_response(
        check_risk_kill_switch(
            (unknown_state,),
            scope,
            config,
            examples._auth(config),
            reconciled=True,
            now=examples.NOW,
        ),
        operation="check_risk_kill_switch",
    )
    assert missing.ordered_checks[0].reason_code is RiskErrorCode.KILL_SWITCH_UNKNOWN
    assert unknown.ordered_checks[0].reason_code is RiskErrorCode.KILL_SWITCH_UNKNOWN
