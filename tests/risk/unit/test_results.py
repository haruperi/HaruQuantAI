"""Unit tests for strict Risk result contracts."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.risk.contracts import (
    ActionPolicyVerdict,
    AllocationRiskDecision,
    ApprovalValidationResult,
    DecisionReuseValidationResult,
    DecisionState,
    KillSwitchState,
    LimitStatus,
    PositionSizingResult,
    RegimeAssessment,
    RiskApprovalToken,
    RiskAuditRecord,
    RiskDecisionPackage,
    RiskErrorCode,
    RiskLimitResult,
    RiskReport,
    ScenarioResult,
    StrategyOperationalEligibilityDecision,
)
from pydantic import ValidationError

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _verdict() -> ActionPolicyVerdict:
    """Build a valid action-policy verdict."""
    return ActionPolicyVerdict(
        verdict_id="verdict-1",
        action="trade.open",
        scope={"account_id": "account-1"},
        policy_version="policy-1",
        attestation_id="attestation-1",
        decision_id="decision-1",
        reservation_id="reservation-1",
        allowed=True,
        reasons=(),
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )


def _limit() -> RiskLimitResult:
    """Build a passing limit result."""
    return RiskLimitResult(
        limit_id="daily-loss",
        status=LimitStatus.PASS,
        observed_value=Decimal("0.01"),
        threshold_value=Decimal("0.02"),
        reason_code=None,
        evidence_refs=("snapshot-1",),
        precedence=1,
    )


def _token() -> RiskApprovalToken:
    """Build a bound approval token."""
    return RiskApprovalToken(
        token_id="token-1",
        decision_id="decision-1",
        config_hash="a" * 64,
        action="trade.open",
        scope={"account_id": "account-1"},
        approver_id="principal-1",
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        nonce="nonce-1",
        signature="signature-1",
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )


def test_action_policy_verdict_requires_reservation() -> None:
    """Reject an allowed verdict without durable reservation identity."""
    with pytest.raises(ValidationError):
        ActionPolicyVerdict(
            verdict_id="verdict-1",
            action="trade.open",
            scope={"account_id": "account-1"},
            policy_version="policy-1",
            attestation_id="attestation-1",
            decision_id="decision-1",
            reservation_id="",
            allowed=True,
            reasons=(),
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=1),
            request_id="request-1",
            workflow_id="workflow-1",
            correlation_id="correlation-1",
        )


def test_limit_result_invariants() -> None:
    """Require a reason for every failing limit result."""
    with pytest.raises(ValidationError):
        RiskLimitResult(
            limit_id="daily-loss",
            status=LimitStatus.FAIL,
            observed_value=Decimal("0.03"),
            threshold_value=Decimal("0.02"),
            reason_code=None,
            evidence_refs=("snapshot-1",),
            precedence=1,
        )


def test_sizing_result_cannot_claim_approval() -> None:
    """Keep sizing recommendations separate from approval."""
    with pytest.raises(ValidationError):
        PositionSizingResult(
            method="fixed_lot",
            requested_size=Decimal(1),
            calculated_size=Decimal(1),
            normalized_size=Decimal(1),
            constraints_applied=(),
            evidence_gaps=(),
            fallback_used=False,
            fallback_reason=None,
            correlation_adjustment=None,
            approved=True,
        )


def test_regime_assessment_carries_transition() -> None:
    """Carry deterministic transitions and tightening modifiers."""
    assessment = RegimeAssessment(
        assessment_id="assessment-1",
        states={"volatility": "elevated"},
        previous_states={"volatility": "normal"},
        transitions=("volatility:normal->elevated",),
        modifiers={"size": Decimal("0.75")},
        evidence_refs=("market-1",),
        missing_fields=(),
        assessed_at=NOW,
    )
    assert assessment.transitions == ("volatility:normal->elevated",)


def test_scenario_result_is_advisory() -> None:
    """Prevent scenario output from becoming executable approval."""
    result = ScenarioResult(
        scenario_id="scenario-1",
        baseline={"equity": Decimal(100)},
        projected={"equity": Decimal(90)},
        differences={"equity": Decimal(-10)},
        assumptions=(),
        seed=None,
        policy_version="policy-1",
        evidence_refs=("snapshot-1",),
        warnings=(),
        generated_at=NOW,
    )
    assert result.advisory_only
    assert not result.approved


def test_decision_package_invariants() -> None:
    """Reject approval without a positive approved size."""
    with pytest.raises(ValidationError):
        RiskDecisionPackage(
            decision_id="decision-1",
            intent_id="intent-1",
            state=DecisionState.APPROVE,
            requested_size=Decimal(1),
            approved_size=None,
            ordered_checks=(_limit(),),
            primary_failure_limit=None,
            composite_breach_flags=(),
            evidence_refs={"snapshot": "snapshot-1"},
            config_hash="a" * 64,
            concurrency_disclosure="serialized",
            recommendations=(),
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=1),
            token=None,
            request_id="request-1",
            workflow_id="workflow-1",
            correlation_id="correlation-1",
        )


def test_token_contract_has_required_bindings() -> None:
    """Carry exact token decision, configuration, and scope bindings."""
    token = _token()
    assert (token.decision_id, token.config_hash, token.scope["account_id"]) == (
        "decision-1",
        "a" * 64,
        "account-1",
    )


def test_kill_switch_unknown_is_representable() -> None:
    """Represent fail-closed unknown kill-switch state."""
    state = KillSwitchState(
        state_id="state-1",
        scope_level="global",
        scope={},
        state="unknown",
        reason="store unavailable",
        version=1,
        updated_at=NOW,
    )
    assert state.state == "unknown"


def test_audit_record_redacts_secrets() -> None:
    """Reject secret-like audit payload keys."""
    with pytest.raises(ValidationError):
        RiskAuditRecord(
            record_id="record-1",
            event_type="decision",
            payload={"api_key": "secret"},  # pragma: allowlist secret
            evidence_refs={"snapshot": "snapshot-1"},
            config_hash="a" * 64,
            decision_id="decision-1",
            occurred_at=NOW,
            sequence=None,
            previous_hash=None,
            record_hash=None,
            sealed=False,
            request_id="request-1",
            correlation_id="correlation-1",
        )


def test_report_contract_separates_sections() -> None:
    """Keep evidence and recommendations in separate report sections."""
    report = RiskReport(
        report_id="report-1",
        format="markdown",
        content="# Risk",
        evidence=("snapshot-1",),
        assumptions=("historical",),
        warnings=("partial coverage",),
        decision=("blocked",),
        recommendations=("refresh evidence",),
        approval_claimed=False,
        generated_at=NOW,
    )
    assert report.evidence != report.recommendations


def test_validation_result_invariants() -> None:
    """Require valid consumption to include an allowed verdict."""
    result = ApprovalValidationResult(
        valid=True,
        consumed=True,
        reason_code=None,
        audit_ref="audit-1",
        reservation_id="reservation-1",
        action_policy_verdict=_verdict(),
    )
    assert result.action_policy_verdict is not None
    with pytest.raises(ValidationError):
        ApprovalValidationResult(
            valid=False,
            consumed=False,
            reason_code=RiskErrorCode.APPROVAL_TOKEN_INVALID,
            audit_ref=None,
            reservation_id=None,
            action_policy_verdict=_verdict(),
        )


def test_current_state_compliance_approves_without_trade_size() -> None:
    """Allow non-authorizing current-state compliance without invented size."""
    current = RiskDecisionPackage(
        decision_id="decision-1",
        intent_id=None,
        state=DecisionState.APPROVE,
        requested_size=None,
        approved_size=None,
        ordered_checks=(_limit(),),
        primary_failure_limit=None,
        composite_breach_flags=(),
        evidence_refs={"snapshot": "snapshot-1"},
        config_hash="a" * 64,
        concurrency_disclosure="not_applicable:current_state_review",
        recommendations=("no_remediation_required",),
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        token=None,
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )
    assert current.state is DecisionState.APPROVE
    assert current.approved_size is None


def test_decision_reuse_result_never_grants_action_authority() -> None:
    """Represent reusable evidence without token consumption or a verdict."""
    result = DecisionReuseValidationResult(
        reusable=True,
        refresh_required=False,
        reason_code=None,
        decision_id="decision-1",
        config_hash="a" * 64,
        evidence_refs={"portfolio": "snapshot-1"},
        validated_at=NOW,
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )
    assert result.reusable is True
    assert not hasattr(result, "action_policy_verdict")
    invalid = result.model_dump(mode="python")
    invalid["refresh_required"] = True
    with pytest.raises(ValidationError):
        DecisionReuseValidationResult.model_validate(invalid)


def test_strategy_eligibility_decision_invariants() -> None:
    """Reject a suspended eligibility approval."""
    with pytest.raises(ValidationError):
        StrategyOperationalEligibilityDecision(
            decision_id="decision-1",
            strategy_id="strategy-1",
            strategy_version="1.0.0",
            scope={"account_id": "account-1"},
            state=DecisionState.APPROVE,
            conditions=(),
            policy_version="policy-1",
            evidence_refs={"market": "market-1"},
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=1),
            suspended=True,
            audit_ref="audit-1",
        )


def test_allocation_risk_decision_invariants() -> None:
    """Reject active allocation state without approval."""
    with pytest.raises(ValidationError):
        AllocationRiskDecision(
            decision_id="decision-1",
            portfolio_id="portfolio-1",
            reviewed_version="1",
            state=DecisionState.BLOCK,
            capped_weights={"strategy-1": Decimal("0.5")},
            risk_budget_projection={"strategy-1": Decimal("0.1")},
            conditions=(),
            policy_version="policy-1",
            evidence_refs={"snapshot": "snapshot-1"},
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=1),
            active=True,
            predecessor_version=None,
            audit_ref="audit-1",
        )
