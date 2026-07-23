"""Executable Analytics metrics usage example.

Demonstrates calculating trade, return, drawdown, risk, ratio, distribution,
and benchmark metric evidence.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.analytics.adapters.results import adapt_trading_result
from app.services.analytics.contracts import (
    AnalyticsRunConfig,
    ClosedTrade,
    RiskFreeRateEvidence,
    StatisticalValidationConfig,
)
from app.services.analytics.metrics.cost_efficiency import (
    calculate_cost_efficiency_evidence,
)
from app.services.analytics.metrics.distributions import (
    calculate_distribution_evidence,
)
from app.services.analytics.metrics.drawdowns import calculate_drawdown_evidence
from app.services.analytics.metrics.ratios import calculate_ratio_evidence
from app.services.analytics.metrics.returns import calculate_return_evidence
from app.services.analytics.metrics.risk import calculate_risk_evidence
from app.services.analytics.metrics.trades import calculate_trade_evidence

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _config() -> AnalyticsRunConfig:
    """Build usage configuration."""
    return AnalyticsRunConfig(
        max_warning_detail_bytes=1024,
        max_trades=100,
        max_equity_points=100,
        max_benchmark_points=100,
        max_statistical_observations=100,
        max_bootstrap_iterations=100,
        max_permutation_iterations=100,
        max_portfolio_components=10,
        max_response_bytes=100_000,
        risk_free_rate=RiskFreeRateEvidence(
            rate=Decimal("0.02"),
            unit="annual_decimal",
            source="usage-fixture",
            as_of=NOW,
        ),
        statistics=StatisticalValidationConfig(
            seed=1,
            bootstrap_iterations=10,
            permutation_iterations=10,
            confidence=0.95,
            alpha=0.05,
        ),
    )


def _trade() -> ClosedTrade:
    """Build a closed trade fixture."""
    return ClosedTrade(
        ticket="ticket-1",
        symbol="EURUSD",
        type="BUY",
        volume=Decimal(1),
        entry_time=NOW,
        entry_price=Decimal("1.10"),
        stop_loss=Decimal("1.09"),
        take_profit=Decimal("1.12"),
        exit_time=NOW,
        exit_price=Decimal("1.11"),
        comment="closed",
        commission=Decimal(-1),
        swap=Decimal(0),
        profit=Decimal(10),
        magic="strategy-1",
        mae=Decimal(-2),
        mfe=Decimal(12),
    )


def example_metrics() -> None:
    """Demonstrate computing metric sections."""
    print("=" * 80)
    print("Analytics Example 3: Metric Calculation")
    print("=" * 80)

    config = _config()
    trade = _trade()
    source = {
        "contract_version": "v1",
        "schema_id": "simulation.result.v1",
        "source_id": "run-1",
        "phase": "backtest",
        "window_start": NOW,
        "window_end": NOW,
        "strategy_id": "strategy-1",
        "strategy_version": "v1",
        "symbols": ("EURUSD",),
        "timeframe": "M1",
        "closed_trades": (dict(trade.__dict__),),
        "quality_metadata": {},
        "source_metadata": {},
    }
    result = adapt_trading_result(
        source,
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=config,
    )

    daily_returns = (0.01, -0.005, 0.008)

    trade_evidence = calculate_trade_evidence(result, config=config)
    print(
        f"Trade section key: {trade_evidence.section_key}, status: {trade_evidence.status}"
    )

    return_evidence = calculate_return_evidence(result, config=config)
    print(
        f"Return section key: {return_evidence.section_key}, status: {return_evidence.status}"
    )

    drawdown_evidence = calculate_drawdown_evidence(result, config=config)
    print(
        f"Drawdown section key: {drawdown_evidence.section_key}, status: {drawdown_evidence.status}"
    )

    risk_evidence = calculate_risk_evidence(daily_returns, config=config)
    print(
        f"Risk section key: {risk_evidence.section_key}, status: {risk_evidence.status}"
    )

    ratio_evidence = calculate_ratio_evidence(result, daily_returns, config=config)
    print(
        f"Ratio section key: {ratio_evidence.section_key}, status: {ratio_evidence.status}"
    )

    cost_evidence = calculate_cost_efficiency_evidence(result, config=config)
    print(
        f"Cost/Efficiency section key: {cost_evidence.section_key}, status: {cost_evidence.status}"
    )

    dist_evidence = calculate_distribution_evidence(daily_returns, config=config)
    print(
        f"Distribution section key: {dist_evidence.section_key}, status: {dist_evidence.status}"
    )


def main() -> None:
    """Run Analytics metrics usage example."""
    example_metrics()


if __name__ == "__main__":
    main()
