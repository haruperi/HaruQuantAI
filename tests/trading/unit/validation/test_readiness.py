"""Unit tests for bounded execution readiness assessments."""

# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.risk import KillSwitchState, RiskDecisionPackage
from app.services.risk.contracts import DecisionState
from app.services.trading.contracts import TradingError, TradingRequest
from app.services.trading.validation import (
    ReadinessAssessment,
    RouteSnapshot,
    assess_execution_readiness,
)
from pydantic import ValidationError

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)
BOUNDS = {
    "route_snapshot": Decimal(30),
    "risk_decision": Decimal(30),
    "kill_switch": Decimal(30),
}


def _request() -> TradingRequest:
    """Build canonical readiness request material."""
    return TradingRequest(
        request_id="request-001",
        workflow_id="workflow-001",
        correlation_id="correlation-001",
        route="sim",
        action="submit_order",
        account_id="account-001",
        strategy_id="strategy-001",
        strategy_version="v1",
        intent_id="intent-001",
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity_unit="units",
        quantity=Decimal("1.00"),
        risk_decision_id="risk-001",
        action_policy_verdict_id="verdict-001",
        approval_token_ref="approval-001",
        idempotency_key="key-001",
        canonical_material_version="v1",
        system_time=NOW,
        valid_until=NOW + timedelta(minutes=5),
    )


def _snapshot() -> RouteSnapshot:
    """Build current explicit route evidence."""
    return RouteSnapshot(
        route="sim",
        provider_id=None,
        account_id="account-001",
        symbol="EURUSD",
        facts={"permission": "allowed"},
        source_id="data-source-001",
        authority_id="simulator",
        observed_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        available=True,
        fresh=True,
        capabilities=("submit_order",),
    )


def _risk() -> RiskDecisionPackage:
    """Build a real approving Risk decision package."""
    return RiskDecisionPackage(
        decision_id="risk-001",
        intent_id="intent-001",
        state=DecisionState.APPROVE,
        requested_size=Decimal("1.00"),
        approved_size=Decimal("1.00"),
        ordered_checks=(),
        primary_failure_limit=None,
        composite_breach_flags=(),
        evidence_refs={"portfolio": "snapshot-001"},
        config_hash="a" * 64,
        concurrency_disclosure="risk-store",
        recommendations=(),
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        token=None,
        request_id="request-001",
        workflow_id="workflow-001",
        correlation_id="correlation-001",
    )


def _switch(state: str = "inactive") -> KillSwitchState:
    """Build a real Risk kill-switch state."""
    return KillSwitchState(
        state_id="switch-001",
        scope_level="global",
        scope={},
        state=state,  # type: ignore[arg-type]
        reason="unit-test",
        version=1,
        updated_at=NOW,
    )


def test_readiness_fails_on_any_missing_evidence() -> None:
    """Any missing mandatory policy evidence produces a failed assessment."""
    assessment = assess_execution_readiness(
        _request(),
        _snapshot(),
        _risk(),
        _switch("active"),
        {
            "allowed": True,
            "verdict_id": "verdict-001",
            "action": "submit_order",
            "expires_at": (NOW + timedelta(minutes=1)).isoformat(),
        },
        BOUNDS,
    )
    assert not assessment.passed
    assert "KILL_SWITCH_BLOCKING" in assessment.failed_check_codes
    request = _request()
    failed = assess_execution_readiness(
        request,
        _snapshot().model_copy(
            update={
                "available": False,
                "fresh": False,
                "expires_at": NOW,
                "capabilities": (),
            }
        ),
        _risk().model_copy(
            update={
                "decision_id": "other-risk",
                "state": DecisionState.REJECT,
                "expires_at": NOW,
                "approved_size": Decimal("2.00"),
                "intent_id": "other-intent",
            }
        ),
        _switch("unknown"),
        {
            "allowed": False,
            "verdict_id": "other-verdict",
            "action": "cancel_order",
            "expires_at": "not-a-time",
        },
        BOUNDS,
    )
    assert not failed.passed
    assert "ROUTE_EVIDENCE_UNAVAILABLE" in failed.failed_check_codes
    assert "RISK_NOT_APPROVED" in failed.failed_check_codes
    no_expiry = assess_execution_readiness(
        request,
        _snapshot(),
        _risk(),
        _switch(),
        {
            "allowed": True,
            "verdict_id": "verdict-001",
            "action": "submit_order",
            "expires_at": None,
        },
        BOUNDS,
    )
    assert "ACTION_POLICY_STALE" in no_expiry.failed_check_codes


def test_far_future_expiry_cannot_bypass_age_bound() -> None:
    """Old observations fail even when their declared expiry is far in the future."""
    assessment = assess_execution_readiness(
        _request(),
        _snapshot().model_copy(
            update={
                "observed_at": NOW - timedelta(seconds=31),
                "expires_at": NOW + timedelta(days=1),
            }
        ),
        _risk(),
        _switch(),
        {
            "allowed": True,
            "verdict_id": "verdict-001",
            "action": "submit_order",
            "expires_at": (NOW + timedelta(minutes=1)).isoformat(),
        },
        BOUNDS,
    )
    assert "ROUTE_EVIDENCE_STALE" in assessment.failed_check_codes


def test_readiness_fails_on_stale_kill_switch_evidence() -> None:
    """An inactive but stale kill-switch scope cannot prove current clearance."""
    stale_switch = _switch().model_copy(
        update={"updated_at": NOW - timedelta(seconds=31)}
    )
    assessment = assess_execution_readiness(
        _request(),
        _snapshot(),
        _risk(),
        stale_switch,
        {
            "allowed": True,
            "verdict_id": "verdict-001",
            "action": "submit_order",
            "expires_at": (NOW + timedelta(minutes=1)).isoformat(),
        },
        BOUNDS,
    )
    assert stale_switch.state == "inactive"
    assert "KILL_SWITCH_STALE" in assessment.failed_check_codes
    assert not assessment.passed


def test_readiness_requires_kill_switch_staleness_bound() -> None:
    """Omitting the kill-switch bound fails configuration rather than passing open."""
    with pytest.raises(TradingError, match="CONFIGURATION_INVALID"):
        assess_execution_readiness(
            _request(),
            _snapshot(),
            _risk(),
            _switch(),
            {
                "allowed": True,
                "verdict_id": "verdict-001",
                "action": "submit_order",
                "expires_at": (NOW + timedelta(minutes=1)).isoformat(),
            },
            {"route_snapshot": Decimal(30), "risk_decision": Decimal(30)},
        )


def test_readiness_assessment_is_bounded() -> None:
    """Readiness evidence rejects unbounded failed-check collections."""
    with pytest.raises(ValidationError, match="unbounded"):
        ReadinessAssessment(
            passed=False,
            failed_check_codes=tuple(f"CHECK_{item}" for item in range(33)),
            evidence_refs={"source": "test"},
            assessed_at=NOW,
        )
    with pytest.raises(ValidationError, match="conflicts"):
        ReadinessAssessment(
            passed=True,
            failed_check_codes=("FAILED",),
            evidence_refs={"source": "test"},
            assessed_at=NOW,
        )
