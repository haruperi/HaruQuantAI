"""Executable Analytics adapters usage example.

Demonstrates result adapter canonicalization and closed-trade equity curve construction.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.analytics.adapters.results import (
    adapt_trading_result,
    build_closed_trade_equity_curve,
)
from app.services.analytics.contracts import (
    AnalyticsRunConfig,
    ClosedTrade,
    StatisticalValidationConfig,
)

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _config() -> AnalyticsRunConfig:
    """Build usage configuration for analytics adapters."""
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
        risk_free_rate=None,
        statistics=StatisticalValidationConfig(
            seed=1,
            bootstrap_iterations=10,
            permutation_iterations=10,
            confidence=0.95,
            alpha=0.05,
        ),
    )


def _trade() -> ClosedTrade:
    """Build one closed trade for adapter demonstration."""
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


def example_adapters() -> None:
    """Demonstrate analytics input adapters."""
    print("=" * 80)
    print("Analytics Example 2: Result Adapters")
    print("=" * 80)

    trade = _trade()
    config = _config()

    # 1. Closed-trade equity curve building
    curve, daily = build_closed_trade_equity_curve(
        (trade,), initial_balance=Decimal(1000), config=config
    )
    print(f"Equity curve points: {len(curve)}, Basis: {curve[0]['curve_basis']}")
    print(f"Daily equity curve points: {len(daily)}")

    # 2. Result adaptation from raw simulation result payload
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
    print(f"Adapted TradingResult contract_version: {result.contract_version}")
    print(f"TradingResult trade count: {len(result.trades)}")


def main() -> None:
    """Run Analytics adapters usage example."""
    example_adapters()


if __name__ == "__main__":
    main()
