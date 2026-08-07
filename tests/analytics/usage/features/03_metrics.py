"""Executable Analytics metrics usage example.

Demonstrates FEAT-ANLT-03 calculating trade, return, drawdown, risk, ratio, distribution,
statistical, and benchmark metric evidence.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.analytics import (
    AnalyticsRunConfig,
    ClosedTrade,
    RiskFreeRateEvidence,
    StatisticalValidationConfig,
    TradingResult,
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
from tests.analytics.usage._support import unwrap

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"SUCCESS: Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    return f"SUCCESS: Output Result -> {type_name} : {type_name}"


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


def _trading_result() -> TradingResult:
    """Build one adapted TradingResult for metric calculations."""
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
    return unwrap(
        adapt_trading_result(
            source,
            source_contract="simulation.result",
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=config,
        )
    )


def fr_anlt_028() -> None:
    """FR-ANLT-028: Stage 3 — Calculate closed-trade metric evidence."""
    _header("Stage 3: Trade Metrics - Calculate Trade Evidence (FR-ANLT-028)")
    result = _trading_result()
    trade_resp = calculate_trade_evidence(result, config=_config())
    trade_ev = unwrap(trade_resp)
    print(_format_result(trade_resp))
    print(f"Data -> section_key='{trade_ev.section_key}', status='{trade_ev.status}'")


def fr_anlt_029() -> None:
    """FR-ANLT-029: Stage 3 — Calculate return and PnL metric evidence."""
    _header("Stage 3: Return Metrics - Calculate Return Evidence (FR-ANLT-029)")
    result = _trading_result()
    ret_resp = calculate_return_evidence(result, config=_config())
    ret_ev = unwrap(ret_resp)
    print(_format_result(ret_resp))
    print(f"Data -> section_key='{ret_ev.section_key}', status='{ret_ev.status}'")


def fr_anlt_030() -> None:
    """FR-ANLT-030: Stage 3 — Calculate drawdown depth, duration, and recovery evidence."""
    _header("Stage 3: Drawdown Metrics - Calculate Drawdown Evidence (FR-ANLT-030)")
    result = _trading_result()
    dd_resp = calculate_drawdown_evidence(result, config=_config())
    dd_ev = unwrap(dd_resp)
    print(_format_result(dd_resp))
    print(f"Data -> section_key='{dd_ev.section_key}', status='{dd_ev.status}'")


def fr_anlt_031() -> None:
    """FR-ANLT-031: Stage 3 — Calculate annualized risk, historical VaR, and CVaR evidence."""
    _header("Stage 3: Risk Metrics - Calculate Risk Evidence (FR-ANLT-031)")
    daily_returns = (0.01, -0.005, 0.008)
    risk_resp = calculate_risk_evidence(daily_returns, config=_config())
    risk_ev = unwrap(risk_resp)
    print(_format_result(risk_resp))
    print(f"Data -> section_key='{risk_ev.section_key}', status='{risk_ev.status}'")


def fr_anlt_032() -> None:
    """FR-ANLT-032: Stage 3 — Calculate core ratio metric evidence with risk-free rate."""
    _header("Stage 3: Ratio Metrics - Calculate Ratio Evidence (FR-ANLT-032)")
    result = _trading_result()
    daily_returns = (0.01, -0.005, 0.008)
    ratio_resp = calculate_ratio_evidence(result, daily_returns, config=_config())
    ratio_ev = unwrap(ratio_resp)
    print(_format_result(ratio_resp))
    print(f"Data -> section_key='{ratio_ev.section_key}', status='{ratio_ev.status}'")


def fr_anlt_037() -> None:
    """FR-ANLT-037: Stage 3 — Calculate cost, efficiency, and excursion evidence."""
    _header(
        "Stage 3: Cost & Efficiency - Calculate Cost Efficiency Evidence (FR-ANLT-037)"
    )
    result = _trading_result()
    cost_resp = calculate_cost_efficiency_evidence(result, config=_config())
    cost_ev = unwrap(cost_resp)
    print(_format_result(cost_resp))
    print(f"Data -> section_key='{cost_ev.section_key}', status='{cost_ev.status}'")


def fr_anlt_035() -> None:
    """FR-ANLT-035: Stage 3 — Calculate distribution moments, percentiles, and tail evidence."""
    _header(
        "Stage 3: Distribution Metrics - Calculate Distribution Evidence (FR-ANLT-035)"
    )
    daily_returns = (0.01, -0.005, 0.008)
    dist_resp = calculate_distribution_evidence(daily_returns, config=_config())
    dist_ev = unwrap(dist_resp)
    print(_format_result(dist_resp))
    print(f"Data -> section_key='{dist_ev.section_key}', status='{dist_ev.status}'")


def fr_anlt_036() -> None:
    """FR-ANLT-036: Stage 3 — Run reproducible statistical validation and bootstrap diagnostics."""
    _header(
        "Stage 3: Statistical Diagnostics - Run Statistical Validation (FR-ANLT-036)"
    )
    observations = tuple(float(index - 15) for index in range(30))
    stat_resp = run_statistical_validation(observations, config=_config())
    stat_ev = unwrap(stat_resp)
    print(_format_result(stat_resp))
    print(f"Data -> section_key='{stat_ev.section_key}', status='{stat_ev.status}'")


def fr_anlt_033() -> None:
    """FR-ANLT-033: Stage 1 — Align strategy and benchmark time series."""
    _header("Stage 1: Benchmark Alignment - Align Benchmark Series (FR-ANLT-033)")
    benchmark_result, _ = _configured_result(benchmark=True)
    benchmark_points = benchmark_result.benchmark
    if benchmark_points is None:
        raise RuntimeError("benchmark usage evidence is missing")
    strategy_points = tuple(
        {"timestamp": point["timestamp"], "value": 0.01}
        for point in benchmark_result.daily_equity_curve
    )
    aligned_resp = align_benchmark_series(strategy_points, benchmark_points["points"])
    aligned = unwrap(aligned_resp)
    print(_format_result(aligned_resp))
    print(f"Data -> aligned_observations_count={len(aligned[0])}")


def fr_anlt_034() -> None:
    """FR-ANLT-034: Stage 3 — Calculate benchmark-relative performance evidence."""
    _header("Stage 3: Benchmark Relative - Calculate Benchmark Evidence (FR-ANLT-034)")
    benchmark_result, benchmark_config = _configured_result(benchmark=True)
    bm_resp = calculate_benchmark_evidence(benchmark_result, config=benchmark_config)
    bm_ev = unwrap(bm_resp)
    print(_format_result(bm_resp))
    print(f"Data -> section_key='{bm_ev.section_key}', status='{bm_ev.status}'")


def fr_anlt_038() -> None:
    """FR-ANLT-038: Stage 3 — Compose all approved metric groups into deterministic evidence sections."""
    _header("Stage 3: Metric Grouping - Calculate Grouped Evidence (FR-ANLT-038)")
    result = _trading_result()
    grouped_resp = calculate_grouped_evidence(result, config=_config())
    grouped = unwrap(grouped_resp)
    print(_format_result(grouped_resp))
    print(f"Data -> section_count={len(grouped)}")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-ANLT-03 — metrics/ — Internal Pure Analytical Evidence\n\n"
        "Purpose: Compute pure, deterministic trade, return, drawdown, risk, ratio, cost/efficiency, distribution, statistical, and benchmark metric evidence.\n\n"
        "Module flow:\n"
        "-> Stage 1: Strategy and benchmark series alignment and timestamp normalization\n"
        "-> Stage 2: Fail-closed sample size validation and undefined metric handling\n"
        "-> Stage 3: SectionEvidence construction across trade, return, drawdown, risk, ratio, cost, distribution, statistical, and benchmark groups"
    )

    # Stage 1: Alignment
    fr_anlt_033()

    # Stage 3: Pure analytical metric calculations
    fr_anlt_028()
    fr_anlt_029()
    fr_anlt_030()
    fr_anlt_031()
    fr_anlt_032()
    fr_anlt_037()
    fr_anlt_035()
    fr_anlt_036()
    fr_anlt_034()
    fr_anlt_038()


if __name__ == "__main__":
    main()
