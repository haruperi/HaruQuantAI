"""Executable Risk regimes usage example.

Demonstrates risk regime assessment under enabled regime policy.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    MarketContextEvidence,
)
from app.services.risk import PortfolioRiskSnapshot, RiskConfig, assess_risk_regime

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _snapshot() -> PortfolioRiskSnapshot:
    """Build immutable snapshot input."""
    return PortfolioRiskSnapshot(
        snapshot_id="snapshot-1",
        account_id="account-1",
        base_currency="USD",
        equity=Decimal(10000),
        daily_loss=Decimal(0),
        total_loss=Decimal(0),
        gross_exposure=Decimal(0),
        net_exposure=Decimal(0),
        drawdown=Decimal(0),
        margin_utilization=Decimal(0),
        effective_leverage=Decimal(0),
        historical_var=None,
        historical_cvar=None,
        volatility=None,
        portfolio_correlation=Decimal(0),
        exposure_by_dimension={},
        contributions={},
        limit_statuses={},
        assumptions=(),
        coverage={"account": "complete"},
        gaps=(),
        regime=None,
        as_of=NOW,
        config_hash="a" * 64,
        evidence_refs={"account": "account-evidence-1"},
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
    )


def _market() -> MarketContextEvidence:
    """Build market context evidence."""
    return MarketContextEvidence(
        symbol="EURUSD",
        session_state="active",
        calendar_state="trading_hours",
        spread=Decimal("0.0001"),
        spread_unit="price",
        liquidity=Decimal(100),
        volatility=Decimal("0.01"),
        correlations={},
        crisis_flags=(),
        timezone="UTC",
        as_of=NOW,
        expires_at=NOW + timedelta(seconds=60),
        provenance={"source": "data"},
        missing_fields=(),
        request_id="req-cccccccc-cccc-4ccc-8ccc-cccccccccccc",
    )


def fr_risk_031() -> None:
    """FR-RISK-031: Classify volatility, liquidity, correlation, drawdown,
    crisis, news, and session regimes; record deterministic
    transitions/evidence; return only equal-or-stricter modifiers; fail closed
    on required missing/unknown live evidence."""
    print("=" * 80)
    print("Risk Example 9: Regime Assessment")
    print("=" * 80)

    config = RiskConfig(
        profile="research",
        execution_route="none",
        policy_version="policy-1",
        base_currency="USD",
        pending_order_exposure_policy="block",
        evidence_max_age_seconds={"portfolio": 60, "market": 30},
        regime_assessment_enabled=True,
        approval_token_ttl_seconds=Decimal(60),
        approval_signing_key_ref="secrets/risk-key",
        decision_ttl_seconds=Decimal(30),
        kill_switch_activation_permissions=("risk.kill.activate",),
        kill_switch_clearance_permissions=("risk.kill.clear",),
        report_timeout_seconds=Decimal(5),
    )

    assessment = assess_risk_regime(_snapshot(), _market(), config, now=NOW)
    print(
        f"Assessed volatility state: {assessment.states.get('volatility')}, "
        f"modifiers: {assessment.modifiers}"
    )


def main() -> None:
    """Run the FR-RISK-031 regime demonstration."""
    fr_risk_031()


if __name__ == "__main__":
    main()
