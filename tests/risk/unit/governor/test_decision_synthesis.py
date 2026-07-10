"""Unit tests for final RiskGovernor decision synthesis logic.

Verifies status precedence, primary reason selection, reduction aggregation,
and token eligibility logic under various simulated gate outputs.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.risk.governor.decision_synthesis import (
    GateResult,
    GovernorEvaluationContext,
    aggregate_reductions,
    determine_decision_status,
    is_decision_token_eligible,
    select_primary_risk_reason,
    synthesize_decision,
)
from app.services.risk.models import (
    ProposedTrade,
    RiskConfig,
    RiskDecisionPackage,
    RiskSeverity,
)
from app.services.risk.models.enums import (
    RiskDecisionStatus,
    RiskReasonCode,
)
from app.services.risk.policy.contracts import EffectiveRiskPolicy


@pytest.fixture
def mock_policy() -> EffectiveRiskPolicy:
    """Fixture providing a mock EffectiveRiskPolicy."""
    return EffectiveRiskPolicy(
        policy_id="test-policy-123",
        resolved_config=RiskConfig(profile_name="default"),
        policy_hash="mock-policy-hash",
        applied_rules=[],
        provenance={"policy_version": "v1.0.0", "policy_scope": {"env": "test"}},
    )


@pytest.fixture
def mock_proposed_trade() -> ProposedTrade:
    """Fixture providing a mock ProposedTrade."""
    return ProposedTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
    )


def test_determine_decision_status_empty(mock_policy):
    """Test that empty results default to APPROVE."""
    assert determine_decision_status([], mock_policy) == RiskDecisionStatus.APPROVE


def test_determine_decision_status_precedence(mock_policy):
    """Test that the status with highest precedence (lowest index) is selected."""
    results = [
        GateResult(
            gate_name=" sizing",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="Passed",
            severity=RiskSeverity.INFO,
            breached=False,
        ),
        GateResult(
            gate_name="correlation",
            status=RiskDecisionStatus.REDUCE_SIZE,
            reason_code=RiskReasonCode.CORRELATION_BREACH,
            message="Reduce",
            severity=RiskSeverity.WARNING,
            breached=True,
        ),
        GateResult(
            gate_name="limits",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.DAILY_LOSS_BREACH,
            message="Rejected",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        ),
    ]
    # REJECT (rank 3) has higher precedence than REDUCE_SIZE (rank 6)
    assert determine_decision_status(results, mock_policy) == RiskDecisionStatus.REJECT

    # Add BLOCK (rank 2)
    results.append(
        GateResult(
            gate_name="drawdown",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.DRAWDOWN_BREACH,
            message="Blocked",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    )
    assert determine_decision_status(results, mock_policy) == RiskDecisionStatus.BLOCK

    # Add HALT_ALL (rank 0)
    results.append(
        GateResult(
            gate_name="kill_switch",
            status=RiskDecisionStatus.HALT_ALL,
            reason_code=RiskReasonCode.KILL_SWITCH_ACTIVE,
            message="Halt All",
            severity=RiskSeverity.EMERGENCY_HALT,
            breached=True,
        )
    )
    assert (
        determine_decision_status(results, mock_policy) == RiskDecisionStatus.HALT_ALL
    )


def test_select_primary_risk_reason_empty():
    """Test select_primary_risk_reason on empty inputs."""
    assert select_primary_risk_reason([]) == RiskReasonCode.OK


def test_select_primary_risk_reason_single_failure():
    """Test select_primary_risk_reason with one failure."""
    results = [
        GateResult(
            gate_name="limits",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.DAILY_LOSS_BREACH,
            message="Breached daily loss",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
    ]
    assert select_primary_risk_reason(results) == RiskReasonCode.DAILY_LOSS_BREACH


def test_select_primary_risk_reason_multiple_failures_priority():
    """Test select_primary_risk_reason prioritization by severity rank."""
    results = [
        GateResult(
            gate_name="correlation",
            status=RiskDecisionStatus.REDUCE_SIZE,
            reason_code=RiskReasonCode.CORRELATION_BREACH,
            message="Reduce",
            severity=RiskSeverity.WARNING,
            breached=True,
        ),
        GateResult(
            gate_name="limits",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.DAILY_LOSS_BREACH,
            message="Rejected",
            severity=RiskSeverity.CRITICAL_BREACH,  # higher severity rank than WARNING
            breached=True,
        ),
        GateResult(
            gate_name="exposure",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.CONCENTRATION_BREACH,
            message="Exposure limits",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        ),
    ]
    # CRITICAL_BREACH is rank 4, HARD_BREACH is rank 3. DAILY_LOSS_BREACH should win.
    assert select_primary_risk_reason(results) == RiskReasonCode.DAILY_LOSS_BREACH


def test_aggregate_reductions():
    """Test reduction aggregation math."""
    results = [
        GateResult(
            gate_name="sizing",
            status=RiskDecisionStatus.REDUCE_SIZE,
            reason_code=RiskReasonCode.OK,
            message="Sized",
            severity=RiskSeverity.INFO,
            breached=False,
            calculated_volume=Decimal("0.8"),
            details={"original_size": Decimal("1.0")},
        ),
        GateResult(
            gate_name="correlation",
            status=RiskDecisionStatus.REDUCE_SIZE,
            reason_code=RiskReasonCode.CORRELATION_BREACH,
            message="Correlation reduce",
            severity=RiskSeverity.WARNING,
            breached=True,
            calculated_volume=Decimal("0.6"),
        ),
        GateResult(
            gate_name="drawdown",
            status=RiskDecisionStatus.REDUCE_SIZE,
            reason_code=RiskReasonCode.DRAWDOWN_BREACH,
            message="Drawdown throttle",
            severity=RiskSeverity.WARNING,
            breached=True,
            calculated_volume=Decimal("0.5"),
        ),
    ]

    plan = aggregate_reductions(results)
    assert plan.original_size == Decimal("1.0")
    assert plan.recommended_size == Decimal("0.8")
    assert plan.correlation_reduced_size == Decimal("0.6")
    assert plan.drawdown_reduced_size == Decimal("0.5")
    assert plan.final_reduced_size == Decimal("0.5")
    assert "correlation" in plan.applied_reductions
    assert "drawdown" in plan.applied_reductions
    assert "exposure" not in plan.applied_reductions


def test_is_decision_token_eligible():
    """Test token eligibility helper."""
    # Eligible approved decision
    decision = RiskDecisionPackage(
        decision_id="dec-1",
        request_id="req-1",
        workflow_id="wf-1",
        status=RiskDecisionStatus.APPROVE,
        rule_key="limits",
        snapshot_as_of=datetime.now(UTC),
        config_hash="abc",
        reason="Passed",
        approved_size=Decimal("1.0"),
    )
    assert is_decision_token_eligible(decision) is True

    # Eligible reduced size
    decision.status = RiskDecisionStatus.REDUCE_SIZE
    assert is_decision_token_eligible(decision) is True

    # Ineligible status
    decision.status = RiskDecisionStatus.REJECT
    assert is_decision_token_eligible(decision) is False

    # Ineligible non-positive size
    decision.status = RiskDecisionStatus.APPROVE
    decision.approved_size = Decimal("0.0")
    assert is_decision_token_eligible(decision) is False

    # Ineligible expired
    decision.approved_size = Decimal("1.0")
    decision.expiry = datetime.now(UTC) - timedelta(seconds=1)
    assert is_decision_token_eligible(decision) is False

    # Eligible non-expired
    decision.expiry = datetime.now(UTC) + timedelta(minutes=5)
    assert is_decision_token_eligible(decision) is True


def test_synthesize_decision_all_pass(mock_policy, mock_proposed_trade):
    """Test synthesize_decision when all gates pass."""
    results = [
        GateResult(
            gate_name="sizing",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="Passed sizing",
            severity=RiskSeverity.INFO,
            breached=False,
            calculated_volume=Decimal("1.0"),
        )
    ]
    context = GovernorEvaluationContext(
        decision_id="dec-test",
        request_id="req-test",
        workflow_id="wf-test",
        proposed_action=mock_proposed_trade,
        policy=mock_policy,
        gate_results=results,
        requested_size=Decimal("1.0"),
    )

    pkg = synthesize_decision(context)
    assert pkg.status == RiskDecisionStatus.APPROVE
    assert pkg.rule_key == "default_approve"
    assert pkg.reason == "All risk gates passed successfully."
    assert pkg.approved_size == Decimal("1.0")
    assert len(pkg.composite_breach_flags) == 0


def test_synthesize_decision_with_breach(mock_policy, mock_proposed_trade):
    """Test synthesize_decision with failing gates."""
    results = [
        GateResult(
            gate_name="sizing",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="Passed",
            severity=RiskSeverity.INFO,
            breached=False,
            calculated_volume=Decimal("1.0"),
        ),
        GateResult(
            gate_name="limits",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.DAILY_LOSS_BREACH,
            message="Breached daily loss limit",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        ),
    ]
    context = GovernorEvaluationContext(
        decision_id="dec-test",
        request_id="req-test",
        workflow_id="wf-test",
        proposed_action=mock_proposed_trade,
        policy=mock_policy,
        gate_results=results,
    )

    pkg = synthesize_decision(context)
    assert pkg.status == RiskDecisionStatus.REJECT
    assert pkg.rule_key == "limits"
    assert "limits: Breached daily loss limit" in pkg.reason
    assert pkg.approved_size is None
    assert pkg.composite_breach_flags == ["limits"]
