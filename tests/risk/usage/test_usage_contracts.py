"""Runnable usage examples for every public Risk contract symbol."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.data.contracts import (
    AccountBalance,
    AccountStateSnapshot,
    MarketContextEvidence,
)
from app.services.risk.contracts import (
    ActionPolicyVerdict,
    AllocationBudgetActivationRequest,
    AllocationReviewRequest,
    AllocationRiskDecision,
    ApprovalAttestation,
    ApprovalValidationResult,
    DecisionReuseValidationResult,
    DecisionState,
    KillSwitchCommand,
    KillSwitchState,
    LimitStatus,
    PortfolioBudgetExecutionVerdict,
    PortfolioRiskSnapshot,
    PortfolioState,
    PositionSizingRequest,
    PositionSizingResult,
    ProposedTrade,
    RegimeAssessment,
    RiskApprovalToken,
    RiskAuditRecord,
    RiskDecisionPackage,
    RiskDomainError,
    RiskErrorCode,
    RiskLimitResult,
    RiskReport,
    ScenarioDefinition,
    ScenarioResult,
    StrategyOperationalEligibilityDecision,
    StrategyOperationalEligibilityRequest,
    validate_market_context_evidence,
)
from app.services.strategy import TradeIntent

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _trade_intent() -> TradeIntent:
    """Return one immutable Strategy intent for receiver-contract examples."""
    return TradeIntent(
        intent_id="intent-1",
        decision_id="strategy-decision-1",
        idempotency_key="intent-key-1",
        strategy_id="strategy-1",
        strategy_version="1.0.0",
        strategy_sequence=1,
        symbol="EURUSD",
        side="BUY",
        intent_type="OPEN",
        order_type="MARKET",
        limit_price=None,
        stop_price=None,
        time_in_force=None,
        requested_sizing_mode="fixed_risk",
        quantity_hint=Decimal(1),
        notional_hint=None,
        signal_timestamp=NOW,
        decision_timestamp=NOW,
        parent_intent_id=None,
        stop_loss=Decimal("1.09"),
        take_profit=None,
        expiration=NOW + timedelta(minutes=1),
        allow_partial_fills=False,
        min_fill_size=None,
        rationale_ref=None,
        lineage={"config_hash": "a" * 64},
    )


def _portfolio_state() -> PortfolioState:
    """Return one complete Risk portfolio evidence contract."""
    return PortfolioState(
        account_snapshot=AccountStateSnapshot(
            account_id="account-1",
            currency="USD",
            balances=(
                AccountBalance(
                    asset="USD", total=Decimal(10000), available=Decimal(9500)
                ),
            ),
            equity=Decimal(10000),
            margin_used=Decimal(500),
            margin_available=Decimal(9500),
            positions=(),
            orders=(),
            connected=True,
            trading_allowed=True,
            source_id="broker-1",
            snapshot_at=NOW,
            expires_at=NOW + timedelta(minutes=1),
            request_id="req-12345678-1234-4234-8234-123456789abc",
        ),
        peak_equity=Decimal(10500),
        day_start_equity=Decimal(10000),
        inception_equity=Decimal(10000),
        symbol_prices={"EURUSD": Decimal("1.10")},
        symbol_contract_sizes={"EURUSD": Decimal(100000)},
        symbol_quote_currencies={"EURUSD": "USD"},
        fx_conversions=(),
        return_timestamps=(NOW - timedelta(minutes=1),),
        return_history={"EURUSD": (Decimal("0.01"),)},
        correlations={},
        exposure_dimensions={"EURUSD": ("asset:fx", "currency:USD")},
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        provenance={"source": "data"},
        missing_fields=(),
        request_id="request-1",
        workflow_id="workflow-1",
    )


def _snapshot() -> PortfolioRiskSnapshot:
    """Return one reproducible Risk snapshot contract."""
    return PortfolioRiskSnapshot(
        snapshot_id="snapshot-1",
        account_id="account-1",
        base_currency="USD",
        equity=Decimal(10000),
        daily_loss=Decimal(0),
        total_loss=Decimal(0),
        gross_exposure=Decimal(1000),
        net_exposure=Decimal(500),
        drawdown=Decimal("0.05"),
        margin_utilization=Decimal("0.05"),
        effective_leverage=Decimal("0.10"),
        historical_var=Decimal(100),
        historical_cvar=Decimal(125),
        volatility=Decimal("0.10"),
        portfolio_correlation=Decimal("0.20"),
        exposure_by_dimension={"symbol:EURUSD": Decimal(1000)},
        contributions={"EURUSD": Decimal(100)},
        limit_statuses={"daily_loss": LimitStatus.PASS},
        assumptions=("historical",),
        coverage={"returns": "complete"},
        gaps=(),
        regime="normal",
        as_of=NOW,
        config_hash="a" * 64,
        evidence_refs={"state": "state-1"},
        request_id="request-1",
        workflow_id="workflow-1",
    )


def _limit() -> RiskLimitResult:
    """Return one passing ordered limit result."""
    return RiskLimitResult(
        limit_id="daily-loss",
        status=LimitStatus.PASS,
        observed_value=Decimal("0.01"),
        threshold_value=Decimal("0.02"),
        reason_code=None,
        evidence_refs=("snapshot-1",),
        precedence=1,
    )


def _verdict() -> ActionPolicyVerdict:
    """Return one action-policy verdict bound to a reservation."""
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


def test_usage_enums_decision_state() -> None:
    """Use the exact Risk decision vocabulary."""
    assert DecisionState.APPROVE.value == "approve"


def test_usage_enums_limit_status() -> None:
    """Use the exact Risk limit vocabulary."""
    assert LimitStatus.BLOCKED.value == "blocked"


def test_usage_errors_codes() -> None:
    """Use a stable Risk boundary error code."""
    assert RiskErrorCode.MISSING_EVIDENCE.value == "MISSING_EVIDENCE"


def test_usage_evidence_portfolio_state() -> None:
    """Construct immutable point-in-time portfolio evidence."""
    assert _portfolio_state().contract_version == "v1"


def test_usage_evidence_portfolio_snapshot() -> None:
    """Read exact Decimal data from a reproducible snapshot."""
    assert _snapshot().equity == Decimal(10000)


def test_usage_evidence_market_context() -> None:
    """Validate the Data-owned market-context contract without redefining it."""
    evidence = MarketContextEvidence(
        symbol="EURUSD",
        spread=Decimal("0.0001"),
        spread_unit="price",
        liquidity=Decimal(100),
        volatility=Decimal("0.10"),
        correlations={},
        crisis_flags=(),
        timezone="UTC",
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        provenance={"source": "data"},
        missing_fields=("session", "calendar"),
        request_id="req-12345678-1234-4234-8234-123456789abc",
    )
    validate_market_context_evidence(evidence, now=NOW)


def test_usage_results_action_policy() -> None:
    """Construct a reserved action-policy verdict."""
    assert _verdict().allowed


def test_usage_results_limit() -> None:
    """Construct an ordered non-authorizing limit result."""
    assert _limit().status is LimitStatus.PASS


def test_usage_requests_proposed_trade() -> None:
    """Embed an exact Strategy intent in a Risk-owned review request."""
    proposal = ProposedTrade(
        intent=_trade_intent(),
        account_id="account-1",
        portfolio_id=None,
        requested_size=Decimal(1),
        current_price=Decimal("1.10"),
        stop_distance=Decimal("0.01"),
        market_as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        risk_profile="paper",
        evidence_refs={"market": "market-1"},
        provenance={"source": "strategy"},
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )
    assert proposal.intent.intent_id == "intent-1"


def test_usage_requests_sizing() -> None:
    """Construct a complete fixed-lot sizing request."""
    request = PositionSizingRequest(
        method="fixed_lot",
        requested_size=Decimal(1),
        fixed_lot=Decimal(1),
        risk_amount=None,
        risk_fraction=None,
        stop_distance=None,
        unit_value=None,
        milestone_multiplier=None,
        win_rate=None,
        payoff_ratio=None,
        trade_count=None,
        volatility_multiplier=None,
        asset_volatility=None,
        broker_min_size=Decimal("0.01"),
        broker_max_size=Decimal(100),
        broker_size_step=Decimal("0.01"),
        evidence_refs={"broker": "broker-1"},
        request_id="request-1",
    )
    assert request.method == "fixed_lot"


def test_usage_results_sizing() -> None:
    """Consume a sizing recommendation without approval authority."""
    result = PositionSizingResult(
        method="fixed_lot",
        requested_size=Decimal(1),
        calculated_size=Decimal(1),
        normalized_size=Decimal(1),
        constraints_applied=(),
        evidence_gaps=(),
        fallback_used=False,
        fallback_reason=None,
        correlation_adjustment=None,
    )
    assert not result.approved


def test_usage_requests_allocation_review() -> None:
    """Construct a self-contained Risk allocation projection."""
    request = AllocationReviewRequest(
        projection_kind="construction",
        portfolio_id="portfolio-1",
        portfolio_version="1",
        result_id="result-1",
        plan_id=None,
        ordered_components=({"strategy_id": "strategy-1", "weight": "0.5"},),
        eligibility_decision_refs=("eligibility-1",),
        account_evidence_ref="account-1",
        market_evidence_ref="market-1",
        fx_evidence_refs=(),
        evidence_hashes={"account": "a" * 64},
        runtime_profile="paper",
        execution_route="paper",
        approval_refs=(),
        requested_at=NOW,
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )
    assert request.portfolio_version == "1"


def test_usage_requests_strategy_eligibility() -> None:
    """Bind admission review to one registered strategy version."""
    request = StrategyOperationalEligibilityRequest(
        strategy_id="strategy-1",
        strategy_version="1.0.0",
        runtime_profile="paper",
        execution_route="paper",
        policy_version="policy-1",
        registration_ref="registration-1",
        evidence_refs={"market": "market-1"},
        approval_refs=(),
        requested_scope={"account_id": "account-1"},
        requested_at=NOW,
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )
    assert request.strategy_version == "1.0.0"


def test_usage_results_regime() -> None:
    """Construct a deterministic Risk regime transition."""
    result = RegimeAssessment(
        assessment_id="assessment-1",
        states={"volatility": "elevated"},
        previous_states={"volatility": "normal"},
        transitions=("volatility:normal->elevated",),
        modifiers={"size": Decimal("0.75")},
        evidence_refs=("market-1",),
        missing_fields=(),
        assessed_at=NOW,
    )
    assert result.modifiers["size"] <= 1


def test_usage_requests_scenario() -> None:
    """Construct a deterministic advisory scenario."""
    scenario = ScenarioDefinition(
        scenario_id="shock-1",
        shocks={"EURUSD": Decimal("-0.10")},
        randomized=False,
        seed=None,
        assumptions=("parallel shock",),
    )
    assert not scenario.randomized


def test_usage_results_scenario() -> None:
    """Consume an explicitly advisory scenario result."""
    result = ScenarioResult(
        scenario_id="shock-1",
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


def test_usage_results_decision() -> None:
    """Construct a canonical non-executable Risk decision package."""
    decision = RiskDecisionPackage(
        decision_id="decision-1",
        intent_id="intent-1",
        state=DecisionState.WARN,
        requested_size=Decimal(1),
        approved_size=None,
        ordered_checks=(_limit(),),
        primary_failure_limit=None,
        composite_breach_flags=(),
        evidence_refs={"snapshot": "snapshot-1"},
        config_hash="a" * 64,
        concurrency_disclosure="not reserved",
        recommendations=("review warning",),
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        token=None,
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )
    assert decision.state is DecisionState.WARN


def test_usage_results_token() -> None:
    """Construct a signed token with complete public bindings."""
    token = RiskApprovalToken(
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
    assert token.scope["account_id"] == "account-1"


def test_usage_requests_kill_switch() -> None:
    """Construct a scoped kill-switch activation command."""
    command = KillSwitchCommand(
        action="activate",
        scope_level="global",
        portfolio_id=None,
        strategy_id=None,
        symbol=None,
        reason="operator stop",
        requested_at=NOW,
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )
    assert command.action == "activate"


def test_usage_results_kill_switch() -> None:
    """Represent a canonical active kill-switch state."""
    state = KillSwitchState(
        state_id="state-1",
        scope_level="global",
        scope={},
        state="active",
        reason="operator stop",
        version=1,
        updated_at=NOW,
    )
    assert state.state == "active"


def test_usage_results_audit() -> None:
    """Construct an unsealed audit input for append processing."""
    record = RiskAuditRecord(
        record_id="record-1",
        event_type="decision",
        payload={"state": "warn"},
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
    assert not record.sealed


def test_usage_results_report() -> None:
    """Construct a report with separated evidence and recommendations."""
    report = RiskReport(
        report_id="report-1",
        format="markdown",
        content="# Risk",
        evidence=("snapshot-1",),
        assumptions=(),
        warnings=(),
        decision=("warn",),
        recommendations=("review",),
        approval_claimed=False,
        generated_at=NOW,
    )
    assert report.format == "markdown"


def test_usage_results_token_validation() -> None:
    """Consume a durable successful token validation result."""
    result = ApprovalValidationResult(
        valid=True,
        consumed=True,
        reason_code=None,
        audit_ref="audit-1",
        reservation_id="reservation-1",
        action_policy_verdict=_verdict(),
    )
    assert result.valid
    assert result.consumed


def test_usage_errors_domain_error() -> None:
    """Raise and inspect a redacted Risk boundary error."""
    with pytest.raises(RiskDomainError) as captured:
        raise RiskDomainError(RiskErrorCode.MISSING_EVIDENCE, "market missing")
    assert captured.value.risk_code is RiskErrorCode.MISSING_EVIDENCE


def test_usage_requests_approval_attestation() -> None:
    """Construct bounded human approval evidence."""
    attestation = ApprovalAttestation(
        attestation_id="attestation-1",
        principal_id="principal-1",
        action="trade.open",
        scope={"account_id": "account-1"},
        policy_ref="policy-ref-1",
        policy_version="policy-1",
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )
    assert attestation.action == "trade.open"


def test_usage_requests_budget_activation() -> None:
    """Bind budget activation to one allocation decision and predecessor."""
    request = AllocationBudgetActivationRequest(
        portfolio_id="portfolio-1",
        allocation_version="2",
        decision_id="decision-1",
        scope={"portfolio_id": "portfolio-1"},
        effective_at=NOW,
        predecessor_version="1",
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )
    assert request.predecessor_version == "1"


def test_usage_results_strategy_eligibility_decision() -> None:
    """Construct a scoped Risk eligibility decision."""
    decision = StrategyOperationalEligibilityDecision(
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
        suspended=False,
        audit_ref="audit-1",
    )
    assert decision.state is DecisionState.APPROVE


def test_usage_results_allocation_decision() -> None:
    """Construct a version-bound Risk allocation decision."""
    decision = AllocationRiskDecision(
        decision_id="decision-1",
        portfolio_id="portfolio-1",
        reviewed_version="1",
        state=DecisionState.APPROVE,
        capped_weights={"strategy-1": Decimal("0.5")},
        risk_budget_projection={"strategy-1": Decimal("0.1")},
        conditions=(),
        policy_version="policy-1",
        evidence_refs={"snapshot": "snapshot-1"},
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        active=False,
        predecessor_version=None,
        audit_ref="audit-1",
    )
    assert decision.reviewed_version == "1"


def test_usage_results_portfolio_budget_execution_verdict() -> None:
    """Construct an exact plan-bound Risk budget execution verdict."""
    verdict = PortfolioBudgetExecutionVerdict(
        verdict_id="budget-verdict-1",
        allocation_decision_id="decision-1",
        portfolio_id="portfolio-1",
        allocation_version="1",
        plan_id="plan-1",
        plan_hash="a" * 64,
        budget_unit="USD",
        allowed=True,
        reasons=(),
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )
    assert verdict.allowed is True


def test_usage_results_decision_reuse_validation() -> None:
    """Construct a non-authorizing successful decision-reuse result."""
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
