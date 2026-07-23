"""Unit tests for deterministic portfolio Risk snapshot construction."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.data.evidence.account_contracts import (
    AccountBalance,
    AccountOrder,
    AccountPosition,
    AccountStateSnapshot,
)
from app.services.data.evidence.fx_contracts import (
    FXConversionEvidence,
    FXRateLeg,
)
from app.services.risk.config import RiskConfig
from app.services.risk.contracts import PortfolioState
from app.services.risk.portfolio import build_portfolio_risk_snapshot

NOW = datetime(2026, 7, 19, tzinfo=UTC)
REQUEST_ID = "req-12345678-1234-4234-8234-123456789abc"


def _config() -> RiskConfig:
    """Build one deterministic research Risk policy."""
    return RiskConfig(
        profile="research",
        execution_route="none",
        policy_version="policy-1",
        base_currency="USD",
        pending_order_exposure_policy="include_full_remaining_exposure",
        evidence_max_age_seconds={"portfolio": 60},
        clock_skew_tolerance_seconds=Decimal(0),
        var_min_observations=3,
        var_lookback=3,
        regime_assessment_enabled=False,
        approval_token_ttl_seconds=Decimal(60),
        approval_signing_key_ref="secrets/risk-key",
        decision_ttl_seconds=Decimal(30),
        kill_switch_activation_permissions=("risk.kill.activate",),
        kill_switch_clearance_permissions=("risk.kill.clear",),
        report_timeout_seconds=Decimal(5),
    )


def _fx_evidence() -> FXConversionEvidence:
    """Build exact JPY-to-USD conversion evidence."""
    leg = FXRateLeg(
        source_currency="JPY",
        target_currency="USD",
        rate=Decimal("0.01"),
        source_id="fx-source-1",
        provider_symbol="JPYUSD",
        as_of=NOW,
        provenance={"source": "data"},
    )
    return FXConversionEvidence(
        source_currency="JPY",
        target_currency="USD",
        legs=(leg,),
        composite_rate=Decimal("0.01"),
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        path_policy_id="direct",
        path_policy_version="1",
        provenance={"source": "data"},
        request_id=REQUEST_ID,
    )


def _state() -> PortfolioState:
    """Build complete position, pending-order, return, and FX evidence."""
    account = AccountStateSnapshot(
        account_id="account-1",
        currency="USD",
        balances=(
            AccountBalance(
                asset="USD",
                total=Decimal(10000),
                available=Decimal(9000),
            ),
        ),
        equity=Decimal(10000),
        margin_used=Decimal(1000),
        margin_available=Decimal(9000),
        positions=(
            AccountPosition(
                position_id="position-1",
                symbol="EURUSD",
                side="LONG",
                quantity=Decimal(1),
                entry_price=Decimal("1.09"),
            ),
        ),
        orders=(
            AccountOrder(
                order_id="order-1",
                symbol="USDJPY",
                side="SELL",
                state="OPEN",
                quantity=Decimal(1),
                price=Decimal(100),
            ),
        ),
        connected=True,
        trading_allowed=True,
        source_id="broker-1",
        snapshot_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        request_id=REQUEST_ID,
    )
    return PortfolioState(
        account_snapshot=account,
        peak_equity=Decimal(11000),
        day_start_equity=Decimal(10200),
        inception_equity=Decimal(10500),
        symbol_prices={"EURUSD": Decimal("1.10"), "USDJPY": Decimal(100)},
        symbol_contract_sizes={"EURUSD": Decimal(100000), "USDJPY": Decimal(1000)},
        symbol_quote_currencies={"EURUSD": "USD", "USDJPY": "JPY"},
        fx_conversions=(_fx_evidence(),),
        return_timestamps=(
            NOW - timedelta(minutes=3),
            NOW - timedelta(minutes=2),
            NOW - timedelta(minutes=1),
        ),
        return_history={
            "EURUSD": (Decimal("0.01"), Decimal("-0.02"), Decimal("0.01")),
            "USDJPY": (Decimal("-0.01"), Decimal("0.01"), Decimal("0.02")),
        },
        correlations={"EURUSD|USDJPY": Decimal("0.20")},
        exposure_dimensions={
            "EURUSD": ("asset:fx", "region:global"),
            "USDJPY": ("asset:fx", "region:global"),
        },
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        provenance={"source": "data"},
        missing_fields=(),
        request_id="request-1",
        workflow_id="workflow-1",
    )


def test_snapshot_includes_pending_and_conversion_evidence() -> None:
    """Include full pending exposure and exact quote conversion evidence."""
    snapshot = build_portfolio_risk_snapshot(_state(), _config(), now=NOW)
    assert snapshot.gross_exposure == Decimal(111000)
    assert snapshot.net_exposure == Decimal(109000)
    assert snapshot.daily_loss == Decimal(200)
    assert snapshot.total_loss == Decimal(500)
    assert snapshot.exposure_by_dimension["currency:JPY"] == Decimal(1000)
    assert snapshot.evidence_refs["fx:JPY"] == REQUEST_ID
    assert snapshot.historical_var is not None
    assert snapshot.historical_cvar is not None
