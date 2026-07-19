"""Runnable usage example for the public portfolio Risk snapshot API."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.data.contracts import AccountBalance, AccountStateSnapshot
from app.services.risk.config import RiskConfig
from app.services.risk.contracts import PortfolioState
from app.services.risk.portfolio import build_portfolio_risk_snapshot

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def test_usage_snapshot_build() -> None:
    """Build a reproducible empty-portfolio snapshot from supplied evidence."""
    account = AccountStateSnapshot(
        account_id="account-1",
        currency="USD",
        balances=(
            AccountBalance(
                asset="USD",
                total=Decimal(10000),
                available=Decimal(10000),
            ),
        ),
        equity=Decimal(10000),
        margin_used=Decimal(0),
        margin_available=Decimal(10000),
        positions=(),
        orders=(),
        connected=True,
        trading_allowed=True,
        source_id="broker-1",
        snapshot_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        request_id="req-12345678-1234-4234-8234-123456789abc",
    )
    state = PortfolioState(
        account_snapshot=account,
        peak_equity=Decimal(10000),
        day_start_equity=Decimal(10000),
        inception_equity=Decimal(10000),
        symbol_prices={},
        symbol_contract_sizes={},
        symbol_quote_currencies={},
        fx_conversions=(),
        return_timestamps=(),
        return_history={},
        correlations={},
        exposure_dimensions={},
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        provenance={"source": "data"},
        missing_fields=("returns",),
        request_id="request-1",
        workflow_id="workflow-1",
    )
    config = RiskConfig(
        profile="research",
        execution_route="none",
        policy_version="policy-1",
        base_currency="USD",
        pending_order_exposure_policy="include_full_remaining_exposure",
        evidence_max_age_seconds={"portfolio": 60},
        clock_skew_tolerance_seconds=Decimal(0),
        var_min_observations=2,
        var_lookback=10,
        regime_assessment_enabled=False,
        approval_token_ttl_seconds=Decimal(60),
        approval_signing_key_ref="secrets/risk-key",
        decision_ttl_seconds=Decimal(30),
        kill_switch_activation_permissions=("risk.kill.activate",),
        kill_switch_clearance_permissions=("risk.kill.clear",),
        report_timeout_seconds=Decimal(5),
    )
    snapshot = build_portfolio_risk_snapshot(state, config, now=NOW)
    assert snapshot.gross_exposure == Decimal(0)
    assert snapshot.account_id == "account-1"
