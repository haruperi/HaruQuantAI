"""Executable Analytics dashboards usage example.

Demonstrates building bounded DashboardPayload presentation projections.
"""

import sys
from datetime import UTC, datetime, timedelta
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
from app.services.analytics.dashboards import (
    build_dashboard_payload,
    truncate_series,
)
from app.services.analytics.reports.builder import build_performance_report
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


def example_dashboards() -> None:
    """Demonstrate Analytics dashboard projections."""
    print("=" * 80)
    print("Analytics Example 5: Dashboard Payloads and Series Truncation")
    print("=" * 80)

    # 1. Truncate series
    points = tuple(
        {"timestamp": NOW + timedelta(minutes=i), "value": float(i % 5)}
        for i in range(20)
    )
    selected, metadata = truncate_series(points, max_points=6)
    print(
        f"Original points: {len(points)}, Truncated points: {len(selected)}, Truncated flag: {metadata['truncated']}"
    )

    # 2. Build dashboard payload from performance report
    config = _config()
    trade = _trade()
    source = {
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
        "closed_trades": (dict(trade.__dict__),),
        "quality_metadata": {},
        "source_metadata": {},
    }
    report = build_performance_report(
        source,
        source_contract="simulation.result",
        request_id=generate_id("req"),
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=config,
    )

    payload = build_dashboard_payload(report)
    print(f"Dashboard Payload schema: {payload.schema_id}")
    print(f"Non-binding: {payload.non_binding}")


def main() -> None:
    """Run Analytics dashboards usage example."""
    example_dashboards()


if __name__ == "__main__":
    main()
