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

from app.services.analytics import (
    AnalyticsRunConfig,
    ClosedTrade,
    RiskFreeRateEvidence,
    StatisticalValidationConfig,
    adapt_trading_result,
    align_benchmark_series,
    calculate_benchmark_evidence,
    calculate_cost_efficiency_evidence,
    calculate_distribution_evidence,
    calculate_drawdown_evidence,
    calculate_grouped_evidence,
    calculate_ratio_evidence,
    calculate_return_evidence,
    calculate_risk_evidence,
    calculate_trade_evidence,
    run_statistical_validation,
)
from tests.analytics._support import _configured_result

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


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
    _header("Demonstrate computing metric sections.")
    print("Analytics Example 3: Metric Calculation")

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
        f"Trade section key: {trade_evidence.section_key}, "
        f"status: {trade_evidence.status}"
    )

    return_evidence = calculate_return_evidence(result, config=config)
    print(
        f"Return section key: {return_evidence.section_key}, "
        f"status: {return_evidence.status}"
    )

    drawdown_evidence = calculate_drawdown_evidence(result, config=config)
    print(
        f"Drawdown section key: {drawdown_evidence.section_key}, "
        f"status: {drawdown_evidence.status}"
    )

    risk_evidence = calculate_risk_evidence(daily_returns, config=config)
    print(
        f"Risk section key: {risk_evidence.section_key}, status: {risk_evidence.status}"
    )

    ratio_evidence = calculate_ratio_evidence(result, daily_returns, config=config)
    print(
        f"Ratio section key: {ratio_evidence.section_key}, "
        f"status: {ratio_evidence.status}"
    )

    cost_evidence = calculate_cost_efficiency_evidence(result, config=config)
    print(
        f"Cost/Efficiency section key: {cost_evidence.section_key}, "
        f"status: {cost_evidence.status}"
    )

    dist_evidence = calculate_distribution_evidence(daily_returns, config=config)
    print(
        f"Distribution section key: {dist_evidence.section_key}, "
        f"status: {dist_evidence.status}"
    )
    grouped = calculate_grouped_evidence(result, config=config)
    print(f"Grouped section count: {len(grouped)}")
    statistical = run_statistical_validation(
        tuple(float(index - 15) for index in range(30)),
        config=config,
    )
    print(f"Statistical section status: {statistical.status}")
    benchmark_result, benchmark_config = _configured_result(benchmark=True)
    benchmark_points = benchmark_result.benchmark
    if benchmark_points is None:
        raise RuntimeError("benchmark usage evidence is missing")
    strategy_points = tuple(
        {"timestamp": point["timestamp"], "value": 0.01}
        for point in benchmark_result.daily_equity_curve
    )
    aligned = align_benchmark_series(
        strategy_points,
        benchmark_points["points"],
    )
    print(f"Aligned benchmark observations: {len(aligned[0])}")
    benchmark_evidence = calculate_benchmark_evidence(
        benchmark_result,
        config=benchmark_config,
    )
    print(f"Benchmark section status: {benchmark_evidence.status}")


def fr_anlt_028() -> None:
    """FR-ANLT-028.

    The system shall calculate closed-trade outcomes classified on
    `net_trade_pnl`, explicit-direction splits, cataloged R-multiples under the
    ordered `declared_stop` then `realized_mae` basis with the applied basis
    labelled per trade, merged-overlap market presence, streaks, and source
    context without treating open/placeholders as realized trades.
    """
    _header(
        "FR-ANLT-028. The system shall calculate closed-trade outcomes classified on `net_trade_pnl`, explicit-direction splits, cataloged R-multiples under the ordered `declared_stop` then `realized_mae` basis with the applied basis labelled per trade, merged-overlap market presence, streaks, and source context without treating open/placeholders as realized trades."
    )
    example_metrics()


def fr_anlt_029() -> None:
    """FR-ANLT-029.

    The system shall calculate monetary PnL in `Decimal` and deterministic sorted
    equity/return evidence with explicit frequency, scale, UTC, and undefined
    behavior.
    """
    _header(
        "FR-ANLT-029. The system shall calculate monetary PnL in `Decimal` and deterministic sorted equity/return evidence with explicit frequency, scale, UTC, and undefined behavior."
    )
    example_metrics()


def fr_anlt_030() -> None:
    """FR-ANLT-030.

    The system shall calculate core drawdown depth, duration, recovery, ulcer, and
    pain evidence from approved curves while returning undefined ratios as `None`
    with warnings.
    """
    _header(
        "FR-ANLT-030. The system shall calculate core drawdown depth, duration, recovery, ulcer, and pain evidence from approved curves while returning undefined ratios as `None` with warnings."
    )
    example_metrics()


def fr_anlt_031() -> None:
    """FR-ANLT-031.

    The system shall calculate only approved annualized volatility, historical
    VaR, and conditional VaR evidence from the daily return resample, with
    cataloged sign, confidence, sample, and units. Expected shortfall is not
    calculated separately: it is mathematically identical to conditional VaR and
    the catalog permits one implementation.
    """
    _header(
        "FR-ANLT-031. The system shall calculate only approved annualized volatility, historical VaR, and conditional VaR evidence from the daily return resample, with cataloged sign, confidence, sample, and units. Expected shortfall is not calculated separately: it is mathematically identical to conditional VaR and the catalog permits one implementation."
    )
    example_metrics()


def fr_anlt_032() -> None:
    """FR-ANLT-032.

    The system shall calculate only approved core ratios and return
    zero-denominator/insufficient-sample results as `None` with warnings.
    Excess-return metrics require source-backed annual-decimal risk-free-rate
    evidence from the injected configuration.
    """
    _header(
        "FR-ANLT-032. The system shall calculate only approved core ratios and return zero-denominator/insufficient-sample results as `None` with warnings. Excess-return metrics require source-backed annual-decimal risk-free-rate evidence from the injected configuration."
    )
    example_metrics()


def fr_anlt_033() -> None:
    """FR-ANLT-033.

    The system shall normalize strategy/benchmark timestamps to UTC, restrict the
    comparison window, resolve duplicates under approved policy, and return
    deterministic aligned observations.
    """
    _header(
        "FR-ANLT-033. The system shall normalize strategy/benchmark timestamps to UTC, restrict the comparison window, resolve duplicates under approved policy, and return deterministic aligned observations."
    )
    example_metrics()


def fr_anlt_034() -> None:
    """FR-ANLT-034.

    The system shall calculate approved benchmark-relative evidence only after
    alignment and currency checks; non-overlap or zero variance is explicit
    skipped/undefined evidence. Alpha requires source-backed annual-decimal
    risk-free-rate evidence from the injected configuration.
    """
    _header(
        "FR-ANLT-034. The system shall calculate approved benchmark-relative evidence only after alignment and currency checks; non-overlap or zero variance is explicit skipped/undefined evidence. Alpha requires source-backed annual-decimal risk-free-rate evidence from the injected configuration."
    )
    example_metrics()


def fr_anlt_035() -> None:
    """FR-ANLT-035.

    The system shall use one cataloged implementation for approved moments,
    percentiles, tails, histogram, and outlier evidence, with constant/short
    samples handled explicitly.
    """
    _header(
        "FR-ANLT-035. The system shall use one cataloged implementation for approved moments, percentiles, tails, histogram, and outlier evidence, with constant/short samples handled explicitly."
    )
    example_metrics()


def fr_anlt_036() -> None:
    """FR-ANLT-036.

    The system shall compute real, bounded, seeded bootstrap, permutation,
    multiple-comparison, and sample diagnostics reproducibly and shall not return
    fixed placeholder evidence.
    """
    _header(
        "FR-ANLT-036. The system shall compute real, bounded, seeded bootstrap, permutation, multiple-comparison, and sample diagnostics reproducibly and shall not return fixed placeholder evidence."
    )
    example_metrics()


def fr_anlt_037() -> None:
    """FR-ANLT-037.

    The system shall calculate ledger cost drag, duration, MAE/MFE,
    `max_intratrade_excursion`, and selected efficiency evidence with documented
    sign conventions and no source mutation. Because `profit` is gross,
    `commission` and `swap` are real deductions: `gross_pnl_before_costs` is
    `sum(profit)`, `total_cost_drag` is their signed sum, and `net_pnl` is their
    combination.
    """
    _header(
        "FR-ANLT-037. The system shall calculate ledger cost drag, duration, MAE/MFE, `max_intratrade_excursion`, and selected efficiency evidence with documented sign conventions and no source mutation. Because `profit` is gross, `commission` and `swap` are real deductions: `gross_pnl_before_costs` is `sum(profit)`, `total_cost_drag` is their signed sum, and `net_pnl` is their combination."
    )
    example_metrics()


def fr_anlt_038() -> None:
    """FR-ANLT-038.

    The system shall execute approved metric groups in deterministic order using
    the injected bounded statistical and risk-free settings, preserve
    all/long/short/benchmark/cost/statistical source context, and expose the
    documented feature operation through the package root.
    """
    _header(
        "FR-ANLT-038. The system shall execute approved metric groups in deterministic order using the injected bounded statistical and risk-free settings, preserve all/long/short/benchmark/cost/statistical source context, and expose the documented feature operation through the package root."
    )
    example_metrics()


def main() -> None:
    """Run the bounded demonstration shared by every metric requirement."""
    example_metrics()


if __name__ == "__main__":
    main()
