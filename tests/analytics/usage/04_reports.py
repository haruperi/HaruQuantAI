"""Executable Analytics reports usage example.

Demonstrates performance report building, comparison, hashing, and serialization.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.analytics.contracts import (
    AnalyticsRunConfig,
    ClosedTrade,
    RiskFreeRateEvidence,
    StatisticalValidationConfig,
)
from app.services.analytics.reports.builder import build_performance_report
from app.services.analytics.reports.comparison import compare_performance_reports
from app.services.analytics.reports.serialization import serialize_report
from app.utils import generate_id

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


def _trade(profit: Decimal = Decimal(10)) -> ClosedTrade:
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
        profit=profit,
        magic="strategy-1",
        mae=Decimal(-2),
        mfe=Decimal(12),
    )


def example_reports() -> None:
    """Demonstrate Analytics reporting capabilities."""
    print("=" * 80)
    print("Analytics Example 4: Performance Report Building and Comparison")
    print("=" * 80)

    config = _config()
    trade1 = _trade(Decimal(10))
    trade2 = _trade(Decimal(20))

    source1 = {
        "contract_version": "v1",
        "schema_id": "simulation.result.v1",
        "source_id": "sim-run-1",
        "phase": "backtest",
        "window_start": NOW,
        "window_end": NOW,
        "strategy_id": "strategy-1",
        "strategy_version": "v1",
        "symbols": ("EURUSD",),
        "timeframe": "M1",
        "closed_trades": (dict(trade1.__dict__),),
        "quality_metadata": {},
        "source_metadata": {},
    }

    source2 = {
        "contract_version": "v1",
        "schema_id": "simulation.result.v1",
        "source_id": "sim-run-2",
        "phase": "backtest",
        "window_start": NOW,
        "window_end": NOW,
        "strategy_id": "strategy-1",
        "strategy_version": "v1",
        "symbols": ("EURUSD",),
        "timeframe": "M1",
        "closed_trades": (dict(trade2.__dict__),),
        "quality_metadata": {},
        "source_metadata": {},
    }

    # 1. Build performance reports
    report1 = build_performance_report(
        source1,
        source_contract="simulation.result",
        request_id=generate_id("req"),
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=config,
    )
    print(f"Report 1 ID: {report1.report_id}, sections count: {len(report1.sections)}")

    report2 = build_performance_report(
        source2,
        source_contract="simulation.result",
        request_id=generate_id("req"),
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=config,
    )
    print(f"Report 2 ID: {report2.report_id}, sections count: {len(report2.sections)}")

    # 2. Compare reports
    comparison = compare_performance_reports(report1, report2)
    print(
        f"Report comparison section: {comparison.section_key}, status: {comparison.status}"
    )

    # 3. Serialize report
    serialized_json = serialize_report(report1, format_name="json", config=config)
    print(f"Serialized report JSON length: {len(serialized_json)} chars")


def main() -> None:
    """Run Analytics reports usage example."""
    example_reports()


if __name__ == "__main__":
    main()
