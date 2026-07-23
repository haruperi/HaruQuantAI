"""Executable Risk limit-evaluation usage example.

Demonstrates deterministic portfolio limit evaluation over an immutable snapshot.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.evidence.market_context_contracts import MarketContextEvidence
from app.services.risk.config import RiskConfig
from app.services.risk.contracts import PortfolioRiskSnapshot
from app.services.risk.limits import (
    evaluate_market_context,
    evaluate_portfolio_limits,
)

NOW = datetime(2026, 7, 19, tzinfo=UTC)
MARKET_REQUEST_ID = "req-cccccccc-cccc-4ccc-8ccc-cccccccccccc"


def _snapshot() -> PortfolioRiskSnapshot:
    """Build immutable portfolio risk snapshot."""
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
        request_id="request-1",
        workflow_id="workflow-1",
    )


def _config() -> RiskConfig:
    """Build risk policy config."""
    return RiskConfig(
        profile="research",
        execution_route="none",
        policy_version="policy-1",
        base_currency="USD",
        pending_order_exposure_policy="block",
        evidence_max_age_seconds={"portfolio": 60, "market": 30},
        regime_assessment_enabled=False,
        approval_token_ttl_seconds=Decimal(60),
        approval_signing_key_ref="secrets/risk-key",
        decision_ttl_seconds=Decimal(30),
        kill_switch_activation_permissions=("risk.kill.activate",),
        kill_switch_clearance_permissions=("risk.kill.clear",),
        report_timeout_seconds=Decimal(5),
    )


def _market() -> MarketContextEvidence:
    """Build fresh complete Data-owned market-context evidence."""
    return MarketContextEvidence(
        symbol="EURUSD",
        session_state="open",
        calendar_state="clear",
        spread=Decimal(1),
        spread_unit="points",
        liquidity=Decimal(100),
        volatility=Decimal("0.01"),
        correlations={},
        crisis_flags=(),
        timezone="UTC",
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        provenance={"source": "example"},
        missing_fields=(),
        request_id=MARKET_REQUEST_ID,
    )


def example_limits() -> None:
    """Demonstrate evaluating portfolio and market-context limits."""
    print("=" * 80)
    print("Risk Example 6: Deterministic Limit Evaluation")
    print("=" * 80)

    snapshot = _snapshot()
    config = _config()

    portfolio_results = evaluate_portfolio_limits(snapshot, config, now=NOW)
    print(f"Evaluated portfolio limit results: {len(portfolio_results)}")
    print(f"Ordered portfolio statuses: {[r.status for r in portfolio_results]}")

    market_results = evaluate_market_context(_market(), config, now=NOW)
    print(f"Evaluated market-context results: {len(market_results)}")
    print(f"Ordered market statuses: {[r.status for r in market_results]}")


def main() -> None:
    """Run the Risk limit-evaluation usage example."""
    example_limits()


if __name__ == "__main__":
    main()
