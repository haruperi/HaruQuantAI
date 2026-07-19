from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.risk.contracts import (
    AllocationBudgetActivationRequest,
    AllocationReviewRequest,
    ApprovalAttestation,
    KillSwitchCommand,
    PositionSizingRequest,
    ProposedTrade,
    ScenarioDefinition,
    StrategyOperationalEligibilityRequest,
)
from app.services.strategy import TradeIntent
from pydantic import ValidationError

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _intent() -> TradeIntent:
    """Build one exact immutable Strategy intent."""
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


def test_proposed_trade_requires_fixed_risk_stop() -> None:
    """Reject risk-increasing proposals without stop evidence."""
    with pytest.raises(ValidationError):
        ProposedTrade(
            intent=_intent(),
            account_id="account-1",
            portfolio_id=None,
            requested_size=Decimal(1),
            current_price=Decimal("1.10"),
            stop_distance=None,
            market_as_of=NOW,
            expires_at=NOW + timedelta(minutes=1),
            risk_profile="live",
            evidence_refs={"market": "market-1"},
            provenance={"source": "strategy"},
            request_id="request-1",
            workflow_id="workflow-1",
            correlation_id="correlation-1",
        )


def test_sizing_request_is_method_strict() -> None:
    """Require the complete evidence set for the selected method."""
    with pytest.raises(ValidationError):
        PositionSizingRequest(
            method="fractional_kelly",
            requested_size=None,
            fixed_lot=None,
            risk_amount=None,
            risk_fraction=None,
            stop_distance=Decimal("0.01"),
            unit_value=Decimal(10),
            milestone_multiplier=None,
            win_rate=None,
            payoff_ratio=None,
            trade_count=None,
            volatility_multiplier=None,
            asset_volatility=None,
            broker_min_size=Decimal("0.01"),
            broker_max_size=Decimal(100),
            broker_size_step=Decimal("0.01"),
            evidence_refs={"history": "history-1"},
            request_id="request-1",
        )


def test_allocation_review_request_is_self_contained() -> None:
    """Reject allocation projections without ordered components."""
    with pytest.raises(ValidationError):
        AllocationReviewRequest(
            projection_kind="construction",
            portfolio_id="portfolio-1",
            portfolio_version="1",
            result_id="result-1",
            plan_id=None,
            ordered_components=(),
            eligibility_decision_refs=("eligibility-1",),
            account_evidence_ref="account-1",
            market_evidence_ref="market-1",
            fx_evidence_refs=("fx-1",),
            evidence_hashes={},
            runtime_profile="live",
            execution_route="live",
            approval_refs=("approval-1",),
            requested_at=NOW,
            request_id="request-1",
            workflow_id="workflow-1",
            correlation_id="correlation-1",
        )


def test_strategy_eligibility_request_binds_exact_version() -> None:
    """Bind operational review to the exact Strategy version."""
    request = StrategyOperationalEligibilityRequest(
        strategy_id="strategy-1",
        strategy_version="1.0.0",
        runtime_profile="paper",
        execution_route="paper",
        policy_version="policy-1",
        registration_ref="registration-1",
        evidence_refs={"market": "market-1"},
        approval_refs=("approval-1",),
        requested_scope={"strategy": "strategy-1"},
        requested_at=NOW,
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )
    assert request.strategy_version == "1.0.0"


def test_scenario_requires_seed_if_randomized() -> None:
    """Reject randomized scenarios without an explicit seed."""
    with pytest.raises(ValidationError):
        ScenarioDefinition(
            scenario_id="scenario-1",
            shocks={"EURUSD": Decimal("-0.10")},
            randomized=True,
            seed=None,
            assumptions=(),
        )


def test_kill_switch_command_requires_scope_and_reason() -> None:
    """Require the identifier for the selected kill-switch scope."""
    with pytest.raises(ValidationError):
        KillSwitchCommand(
            action="activate",
            scope_level="strategy",
            portfolio_id=None,
            strategy_id=None,
            symbol=None,
            reason="operator stop",
            requested_at=NOW,
            request_id="request-1",
            workflow_id="workflow-1",
            correlation_id="correlation-1",
        )


def test_approval_attestation_requires_scope_and_expiry() -> None:
    """Require bounded scope and a future attestation expiry."""
    with pytest.raises(ValidationError):
        ApprovalAttestation(
            attestation_id="attestation-1",
            principal_id="user-1",
            action="trade.open",
            scope={},
            policy_ref="policy-ref-1",
            policy_version="policy-1",
            issued_at=NOW,
            expires_at=NOW,
            request_id="request-1",
            workflow_id="workflow-1",
            correlation_id="correlation-1",
        )


def test_budget_activation_request_binds_decision_and_version() -> None:
    """Bind activation to an exact decision and predecessor version."""
    request = AllocationBudgetActivationRequest(
        portfolio_id="portfolio-1",
        allocation_version="2",
        decision_id="decision-1",
        scope={"portfolio": "portfolio-1"},
        effective_at=NOW,
        predecessor_version="1",
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )
    assert request.predecessor_version == "1"


"""Unit tests for strict Risk request contracts."""
