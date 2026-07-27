"""Executable Risk limit-evaluation usage example.

Demonstrates deterministic portfolio limit evaluation over an immutable snapshot.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import MarketContextEvidence
from app.services.risk import (
    PortfolioRiskSnapshot,
    RiskConfig,
    evaluate_market_context,
    evaluate_portfolio_limits,
)

NOW = datetime(2026, 7, 19, tzinfo=UTC)
MARKET_REQUEST_ID = "req-cccccccc-cccc-4ccc-8ccc-cccccccccccc"


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


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
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
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
    _header("Demonstrate evaluating portfolio and market-context limits.")
    print("Risk Example 6: Deterministic Limit Evaluation")

    snapshot = _snapshot()
    config = _config()

    portfolio_results = evaluate_portfolio_limits(snapshot, config, now=NOW)
    print(f"Evaluated portfolio limit results: {len(portfolio_results)}")
    print(f"Ordered portfolio statuses: {[r.status for r in portfolio_results]}")

    market_results = evaluate_market_context(_market(), config, now=NOW)
    print(f"Evaluated market-context results: {len(market_results)}")
    print(f"Ordered market statuses: {[r.status for r in market_results]}")


_DEMONSTRATED = False


def _demonstrate_once() -> None:
    """Run the bounded limits demonstration once."""
    global _DEMONSTRATED  # noqa: PLW0603
    if not _DEMONSTRATED:
        example_limits()
        _DEMONSTRATED = True


def fr_risk_027() -> None:
    """FR-RISK-027: Evaluate daily/total loss, drawdown state, consistency,
    exposure/concentration, margin/leverage, historical tail risk, correlation,
    and freshness in deterministic precedence, returning primary and composite
    failures."""
    _header(
        "FR-RISK-027: Evaluate daily/total loss, drawdown state, consistency, exposure/concentration, margin/leverage, historical tail risk, correlation, and freshness in deterministic precedence, returning primary and composite failures."
    )
    _demonstrate_once()


def fr_risk_028() -> None:
    """FR-RISK-028: Evaluate supplied spread, liquidity availability, session,
    and normalized calendar state without external fetches, hidden unit
    conversion, or naive/aware datetime comparison. Slippage is excluded because
    `MarketContextEvidence v1` does not carry it and execution slippage is
    receiver-owned post-trade evidence."""
    _header(
        "FR-RISK-028: Evaluate supplied spread, liquidity availability, session, and normalized calendar state without external fetches, hidden unit conversion, or naive/aware datetime comparison. Slippage is excluded because `MarketContextEvidence v1` does not carry it and execution slippage is receiver-owned post-trade evidence."
    )
    _demonstrate_once()


def main() -> None:
    """Run every functional-requirement demonstration for Risk limits."""
    for demonstrate in (fr_risk_027, fr_risk_028):
        demonstrate()


if __name__ == "__main__":
    main()
