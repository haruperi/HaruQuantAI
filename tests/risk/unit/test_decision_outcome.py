"""Unit tests for the explainable Risk decision outcome classifier."""

from datetime import timedelta
from decimal import Decimal

from app.services.risk.contracts import (
    DecisionState,
    create_risk_decision_package,
    get_decision_state,
)
from app.services.risk.reporting import classify_decision_outcome

from tests.risk import _support as examples


def _decision(**overrides: object) -> object:
    """Build a bounded decision package with explicit field overrides."""
    values: dict[str, object] = {
        "decision_id": "decision-1",
        "intent_id": "intent-1",
        "state": get_decision_state("APPROVE"),
        "requested_size": Decimal(10),
        "approved_size": Decimal(10),
        "ordered_checks": (),
        "primary_failure_limit": None,
        "composite_breach_flags": (),
        "evidence_refs": {"portfolio": "snapshot-1"},
        "config_hash": "a" * 64,
        "concurrency_disclosure": "risk_store",
        "recommendations": (),
        "issued_at": examples.NOW,
        "expires_at": examples.NOW + timedelta(seconds=120),
        "token": None,
        "request_id": examples.REQUEST_ID,
        "workflow_id": examples.WORKFLOW_ID,
        "correlation_id": examples.CORRELATION_ID,
    }
    values.update(overrides)
    return create_risk_decision_package(**values)


def test_reduced_approved_size_classifies_as_resize() -> None:
    """Classify an approved decision with a reduced size as a resize."""
    decision = _decision(approved_size=Decimal(6))
    assert classify_decision_outcome(decision) is DecisionState.RESIZE


def test_full_approved_size_stays_approve() -> None:
    """Keep an approved decision at full requested size as approve."""
    decision = _decision()
    assert classify_decision_outcome(decision) is DecisionState.APPROVE


def test_kill_switch_block_classifies_as_restrict() -> None:
    """Classify a kill-switch-driven block as a restriction."""
    decision = _decision(
        state=get_decision_state("BLOCK"),
        approved_size=None,
        primary_failure_limit="kill_switch",
    )
    assert classify_decision_outcome(decision) is DecisionState.RESTRICT


def test_non_kill_switch_block_stays_block() -> None:
    """Keep a non-kill-switch block as an ordinary block."""
    decision = _decision(
        state=get_decision_state("BLOCK"),
        approved_size=None,
        primary_failure_limit="daily_loss",
    )
    assert classify_decision_outcome(decision) is DecisionState.BLOCK
