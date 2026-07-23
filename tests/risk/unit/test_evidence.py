from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.data.evidence.account_contracts import (
    AccountBalance,
    AccountStateSnapshot,
)
from app.services.data.evidence.market_context_contracts import (
    MarketContextEvidence,
)
from app.services.risk.contracts import (
    PortfolioRiskSnapshot,
    PortfolioState,
    RiskDomainError,
    validate_market_context_evidence,
)

NOW = datetime(2026, 7, 19, tzinfo=UTC)
REQUEST_ID = "req-12345678-1234-4234-8234-123456789abc"


def _state() -> PortfolioState:
    """Build representative immutable portfolio evidence."""
    return PortfolioState(
        account_snapshot=AccountStateSnapshot(
            account_id="account-1",
            currency="USD",
            balances=(
                AccountBalance(
                    asset="USD", total=Decimal(10000), available=Decimal(9500)
                ),
            ),
            equity=Decimal(9500),
            margin_used=Decimal(500),
            margin_available=Decimal(9000),
            positions=(),
            orders=(),
            connected=True,
            trading_allowed=True,
            source_id="broker-1",
            snapshot_at=NOW,
            expires_at=NOW + timedelta(minutes=1),
            request_id=REQUEST_ID,
        ),
        peak_equity=Decimal(10500),
        day_start_equity=Decimal(10000),
        inception_equity=Decimal(10000),
        symbol_prices={"EURUSD": Decimal("1.10")},
        symbol_contract_sizes={"EURUSD": Decimal(100000)},
        symbol_quote_currencies={"EURUSD": "USD"},
        fx_conversions=(),
        return_timestamps=(NOW - timedelta(minutes=2), NOW - timedelta(minutes=1)),
        return_history={"EURUSD": (Decimal("0.01"), Decimal("-0.02"))},
        correlations={},
        exposure_dimensions={"EURUSD": ("asset:fx", "currency:USD")},
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        provenance={"source": "data"},
        missing_fields=("calendar",),
        request_id="request-1",
        workflow_id="workflow-1",
    )


def test_portfolio_state_preserves_missingness() -> None:
    """Preserve explicit missing-evidence markers."""
    state = _state()
    assert state.missing_fields == ("calendar",)
    with pytest.raises(TypeError):
        state.symbol_prices["EURUSD"] = Decimal(1)  # type: ignore[index]


def test_snapshot_serializes_decimal_exactly() -> None:
    """Serialize broker-critical Decimals as exact JSON strings."""
    snapshot = PortfolioRiskSnapshot(
        snapshot_id="snapshot-1",
        account_id="account-1",
        base_currency="USD",
        equity=Decimal("9500.10"),
        daily_loss=Decimal("499.90"),
        total_loss=Decimal("499.90"),
        gross_exposure=Decimal("100.20"),
        net_exposure=Decimal("50.10"),
        drawdown=Decimal("0.10"),
        margin_utilization=Decimal("0.05"),
        effective_leverage=Decimal("0.02"),
        historical_var=None,
        historical_cvar=None,
        volatility=None,
        portfolio_correlation=None,
        exposure_by_dimension={"symbol:EURUSD": Decimal("100.20")},
        contributions={},
        limit_statuses={},
        assumptions=("historical",),
        coverage={"returns": "partial"},
        gaps=("var",),
        regime=None,
        as_of=NOW,
        config_hash="a" * 64,
        evidence_refs={"state": "state-1"},
        request_id="request-1",
        workflow_id="workflow-1",
    )
    assert snapshot.model_dump(mode="json")["equity"] == "9500.10"


def test_market_context_uses_data_owned_contract() -> None:
    """Consume and freshness-check the Data-owned contract."""
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
        request_id=REQUEST_ID,
    )
    validate_market_context_evidence(evidence, now=NOW)
    with pytest.raises(RiskDomainError):
        validate_market_context_evidence(
            evidence,
            now=NOW + timedelta(minutes=2),
        )


"""Unit tests for Risk evidence and snapshot contracts."""
