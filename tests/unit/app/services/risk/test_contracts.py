"""Unit tests for Risk Governance contracts and model validations."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.risk.models.contracts import (
    PortfolioState,
    PositionState,
    ProposedAllocation,
    ProposedTrade,
    RiskAssessmentRequest,
    RiskConfig,
    create_risk_decision_package,
    validate_risk_assessment_request,
)
from app.services.risk.models.enums import RiskDecisionStatus, RiskMode
from pydantic import ValidationError


def test_proposed_trade_validation() -> None:
    """Test ProposedTrade validation and field synchronization."""
    trade = ProposedTrade(
        strategy_id="test-strat",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.5"),
        price=Decimal("1.0850"),
        stop_loss=Decimal("1.0800"),
    )
    assert trade.requested_size == Decimal("1.5")
    assert trade.intended_stop == Decimal("1.0800")


def test_finite_decimals_validation() -> None:
    """Test that models reject NaN and infinity values."""
    # Test NaN rejection in ProposedTrade
    with pytest.raises(ValidationError, match="finite"):
        ProposedTrade(
            strategy_id="test-strat",
            symbol="EURUSD",
            side="buy",
            volume=Decimal("NaN"),
        )

    with pytest.raises(ValidationError, match="finite"):
        ProposedTrade(
            strategy_id="test-strat",
            symbol="EURUSD",
            side="buy",
            volume=Decimal("Infinity"),
        )


def test_proposed_allocation_validation() -> None:
    """Test ProposedAllocation contract model."""
    alloc = ProposedAllocation(
        allocations={"strat-1": Decimal("10000.0")},
        as_of=datetime.now(UTC),
    )
    assert alloc.allocations["strat-1"] == Decimal("10000.0")


def test_position_and_portfolio_state() -> None:
    """Test PositionState and PortfolioState validation."""
    pos = PositionState(
        position_id="pos-1",
        symbol="EURUSD",
        direction="long",
        quantity=Decimal("1.0"),
        entry_price=Decimal("1.0850"),
        current_price=Decimal("1.0870"),
        floating_pnl=Decimal("200.0"),
        margin_required=Decimal("1000.0"),
        strategy_id="strat-1",
        open_time=datetime.now(UTC),
    )
    portfolio = PortfolioState(
        account_id="acc-1",
        balance=Decimal("100000.0"),
        equity=Decimal("100200.0"),
        margin_used=Decimal("1000.0"),
        free_margin=Decimal("99000.0"),
        floating_pnl=Decimal("200.0"),
        realized_pnl=Decimal("0.0"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[pos],
    )
    assert len(portfolio.positions) == 1
    assert portfolio.positions[0].position_id == "pos-1"


def test_risk_assessment_request_sync() -> None:
    """Test RiskAssessmentRequest field synchronization."""
    pos = PositionState(
        position_id="pos-1",
        symbol="EURUSD",
        direction="long",
        quantity=Decimal("1.0"),
        entry_price=Decimal("1.0850"),
        current_price=Decimal("1.0870"),
        floating_pnl=Decimal("200.0"),
        margin_required=Decimal("1000.0"),
        strategy_id="strat-1",
        open_time=datetime.now(UTC),
    )
    portfolio = PortfolioState(
        account_id="acc-1",
        balance=Decimal("100000.0"),
        equity=Decimal("100200.0"),
        margin_used=Decimal("1000.0"),
        free_margin=Decimal("99000.0"),
        floating_pnl=Decimal("200.0"),
        realized_pnl=Decimal("0.0"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[pos],
    )
    config = RiskConfig(profile_name="simulation")
    trade = ProposedTrade(
        strategy_id="strat-1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
    )
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=config,
    )
    assert req.account_state is not None
    assert req.account_state["balance"] == 100000.0
    assert req.open_positions is not None
    assert len(req.open_positions) == 1
    assert req.policy_profile == "simulation"


def test_validate_risk_assessment_request() -> None:
    """Test validate_risk_assessment_request validator."""
    pos = PositionState(
        position_id="pos-1",
        symbol="EURUSD",
        direction="long",
        quantity=Decimal("1.0"),
        entry_price=Decimal("1.0850"),
        current_price=Decimal("1.0870"),
        floating_pnl=Decimal("200.0"),
        margin_required=Decimal("1000.0"),
        strategy_id="strat-1",
        open_time=datetime.now(UTC),
    )
    portfolio = PortfolioState(
        account_id="acc-1",
        balance=Decimal("100000.0"),
        equity=Decimal("100200.0"),
        margin_used=Decimal("1000.0"),
        free_margin=Decimal("99000.0"),
        floating_pnl=Decimal("200.0"),
        realized_pnl=Decimal("0.0"),
        currency="USD",
        as_of=datetime.now(UTC),
        positions=[pos],
    )
    config = RiskConfig(profile_name="simulation")
    trade = ProposedTrade(
        strategy_id="strat-1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
    )
    req = RiskAssessmentRequest(
        proposed_action=trade,
        portfolio_state=portfolio,
        risk_config=config,
    )

    # Valid Request
    res = validate_risk_assessment_request(req)
    assert res["valid"] is True

    # Test Live mode with missing or stale freshness
    req.mode = RiskMode.MICRO_LIVE
    req.freshness = None
    res = validate_risk_assessment_request(req)
    assert res["valid"] is False
    assert res["code"] == "STALE_EVIDENCE"

    # Test Live mode with stale freshness
    req.freshness = datetime(2020, 1, 1, tzinfo=UTC)
    res = validate_risk_assessment_request(req)
    assert res["valid"] is False
    assert res["code"] == "STALE_EVIDENCE"


def test_create_risk_decision_package() -> None:
    """Test create_risk_decision_package factory function."""
    pkg = create_risk_decision_package(
        decision_id="dec-1",
        request_id="req-1",
        workflow_id="wf-1",
        status=RiskDecisionStatus.APPROVE,
        rule_key="rule-1",
        config_hash="conf-1",
        reason="all ok",
        composite_breach_flags=[],
        calculated_volume=Decimal("1.0"),
        details={"action": "test_action"},
    )
    assert pkg.status == RiskDecisionStatus.APPROVE
    assert pkg.action == "test_action"
    assert pkg.approved_size == Decimal("1.0")
