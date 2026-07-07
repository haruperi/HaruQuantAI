# ruff: noqa: E501, E402
"""Unified usage examples for the Analytics service.

The examples use deterministic in-memory payloads only. They do not call
brokers, the network, databases, live trading, or UI/API layers.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.services.analytics.adapters.canonicalize import (
    TradingResultAdapter,
    to_trading_result,
)
from app.services.analytics.adapters.journal_adapters import (
    SimulationJournal,
    from_simulation_journal,
)
from app.services.analytics.adapters.protocols import validate_adapter_contract
from app.services.analytics.benchmarks.metrics import (
    alpha,
    batting_average,
    beta,
    calculate_benchmark_metrics,
    information_ratio,
    tracking_error,
    up_down_capture,
)
from app.services.analytics.boundaries import (
    AnalyticsLimits,
    RedactionPolicy,
    WorkloadShape,
    enforce_limits,
    float64,
    redact,
    request_id,
    validate_request,
)
from app.services.analytics.contracts import (
    METRIC_DEFINITION_CATALOG,
    SCHEMA_COMPATIBILITY_MATRIX,
    MetricConfig,
    PrecisionPolicy,
    canonical_json,
    get_metric_definition,
    to_json_safe,
    validate_metric_catalog,
    validate_schema_version,
)
from app.services.analytics.contracts.warnings import (
    build_quality_flag,
    build_warning,
    redact_sensitive_info,
)
from app.services.analytics.dashboards.overview import (
    DashboardConfig,
    build_overview_payload,
)
from app.services.analytics.dashboards.truncation import (
    TruncationPolicy,
    truncate_series,
)
from app.services.analytics.metrics.aggregate import (
    breakeven_epsilon,
    calculate_analytics_for_subset,
    calculate_trade_metrics,
    metrics_aggregate_boundary,
)
from app.services.analytics.metrics.aggregate import (
    compute_equity_metrics as aggregate_compute_equity_metrics,
)
from app.services.analytics.metrics.costs import (
    calculate_commission_impact,
    calculate_slippage_impact,
    calculate_spread_cost_impact,
)
from app.services.analytics.metrics.curves import (
    balance_curve_from_closed_trades,
    equity_curve,
    equity_curve_metric,
)
from app.services.analytics.metrics.drawdown import (
    calculate_drawdown_metrics,
    drawdown_distribution,
    drawdown_probability,
    drawdown_series,
    metrics_drawdown_boundary,
    recovery_factor,
    ulcer_index,
)
from app.services.analytics.metrics.efficiency import (
    calculate_efficiency_metrics,
    capital_efficiency,
    exit_efficiency,
    get_mae_mfe_r,
    loss_containment_efficiency,
    metrics_efficiency_boundary,
    return_per_trade_hour,
)
from app.services.analytics.metrics.equity import (
    annualized_return,
    benchmark_returns,
    calculate_equity_metrics,
    calculate_return_metrics,
    daily_returns,
    downside_return_volatility,
    return_on_account,
    return_volatility,
    total_return_usd,
    win_loss_streaks,
)
from app.services.analytics.metrics.pnl import (
    cagr,
    gross_loss,
    gross_profit,
    max_runup,
    net_profit,
    return_on_initial_capital,
    total_return,
)
from app.services.analytics.metrics.position_exposure import (
    commission_paid,
    max_gross_size_held,
    max_net_size_held,
    open_position_pnl,
    percent_time_in_market,
    slippage_paid,
    swap_paid,
    time_in_market_duration,
)
from app.services.analytics.metrics.r_multiples import (
    avg_return_per_risk_unit,
    compute_r_trade_metrics,
    get_r_multiples,
)
from app.services.analytics.metrics.ratios import (
    annualized_sharpe_ratio,
    calculate_ratio_metrics,
    deflated_sharpe_ratio,
    omega_ratio,
    profit_factor,
    sharpe_ratio,
    sortino_ratio,
)
from app.services.analytics.metrics.risk import (
    annualized_volatility,
    calculate_risk_metrics,
    conditional_var,
    expected_shortfall,
    value_at_risk,
    volatility,
)
from app.services.analytics.metrics.time_analysis import (
    avg_time_in_trade,
    calculate_long_short_split,
    calculate_period_analysis,
    calculate_session_performance,
    trading_period_duration,
)
from app.services.analytics.metrics.trade_outcomes import (
    classify_trades,
    expectancy,
    expectancy_r,
    get_closed_trades,
    largest_loss,
    largest_win,
    max_consecutive_losses,
    max_consecutive_wins,
    total_trades,
    win_rate,
)
from app.services.analytics.registry.analytics_registry import (
    clear_active_requests,
    get_active_requests,
)
from app.services.analytics.registry.analytics_registry import (
    request_id as registry_request_id,
)
from app.services.analytics.reports import (
    build_analytics_report,
    build_backtest_report,
    calculate_prop_firm_compliance,
    calculate_statistical_validation,
    compare_analytics_reports,
    compute_report_hash,
    format_summary_as_rows,
    serialize_report,
)
from app.services.analytics.reports.formatters import ReportFormat
from app.services.analytics.reports.hashes import HashPolicy
from app.services.analytics.reports.sections import evaluate_section
from app.services.analytics.scorecards.quality import (
    StrategyQualityConfig,
    evaluate_strategy_quality,
    sqn,
)
from app.services.analytics.scorecards.quality import (
    sample_size_warning as scorecard_sample_size_warning,
)
from app.services.analytics.statistics.distributions import (
    calculate_distribution_metrics,
    detect_outliers,
    distribution_fit_quality,
    higher_moments,
    histogram_data,
    jarque_bera_test,
    percentile_summary,
    statistics_distribution_boundary,
)
from app.services.analytics.statistics.multiple_testing import (
    benjamini_hochberg_correction,
    bonferroni_correction,
    probability_of_backtest_overfitting,
    stability_score,
    whites_reality_check,
)
from app.services.analytics.statistics.resampling import (
    bootstrap_confidence_intervals,
    bootstrap_probability_above_threshold,
    permutation_test,
    statistics_resampling_boundary,
)


def print_header(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 100}")
    print(f"--- {title} ---")
    print(f"{'=' * 100}")


def print_kv(label: str, value: Any) -> None:
    """Print a compact label/value row."""
    print(f"  {label:30}: {value}")


def sample_trades() -> list[dict[str, Any]]:
    """Return deterministic closed and open trade records."""
    return [
        {
            "trade_id": "t1",
            "symbol": "EURUSD",
            "direction": "long",
            "open_time": "2026-01-01T00:00:00Z",
            "close_time": "2026-01-01T04:00:00Z",
            "profit_loss": 100.0,
            "net_pnl": 100.0,
            "initial_risk": 50.0,
            "mae": -20.0,
            "mfe": 140.0,
            "size": 1.0,
            "open_price": 1.1000,
            "margin": 200.0,
            "spread_cost": 0.7,
            "slippage": 1.5,
            "commission": 2.0,
            "swap": 0.5,
        },
        {
            "trade_id": "t2",
            "symbol": "EURUSD",
            "direction": "short",
            "open_time": "2026-01-02T00:00:00Z",
            "close_time": "2026-01-02T04:00:00Z",
            "profit_loss": -40.0,
            "net_pnl": -40.0,
            "initial_risk": 50.0,
            "mae": -50.0,
            "mfe": 10.0,
            "size": 1.2,
            "open_price": 1.1050,
            "margin": 250.0,
            "spread_cost": 0.6,
            "slippage": 0.5,
            "commission": 2.0,
            "swap": 0.0,
        },
        {
            "trade_id": "t3",
            "symbol": "EURUSD",
            "direction": "long",
            "open_time": "2026-01-03T00:00:00Z",
            "is_open": True,
            "pnl": 12.5,
            "size": 0.5,
        },
    ]


def closed_trades() -> list[dict[str, Any]]:
    """Return closed sample trades only."""
    return list(get_closed_trades(sample_trades()))


def sample_equity_curve() -> list[dict[str, Any]]:
    """Return deterministic equity curve points."""
    return [
        {"timestamp": "2026-01-01T00:00:00Z", "equity": 10000.0},
        {"timestamp": "2026-01-01T04:00:00Z", "equity": 10100.0},
        {"timestamp": "2026-01-02T04:00:00Z", "equity": 10060.0},
        {"timestamp": "2026-01-03T04:00:00Z", "equity": 10140.0},
    ]


def sample_returns() -> list[float]:
    """Return deterministic return observations."""
    return [0.01, -0.00396039603960396, 0.007952286282306]


def sample_trading_result() -> dict[str, Any]:
    """Return canonical analytics input payload."""
    return {
        "schema_version": "1.3.1",
        "result_id": "usage_analytics_run",
        "phase": "backtest",
        "strategy_id": "usage_strategy",
        "strategy_version": "v1",
        "account_base_currency": "USD",
        "symbols": ["EURUSD"],
        "timeframe": "H1",
        "trades": closed_trades(),
        "equity_curve": sample_equity_curve(),
        "benchmark_curve": [
            {"timestamp": "2026-01-01T00:00:00Z", "equity": 10000.0},
            {"timestamp": "2026-01-01T04:00:00Z", "equity": 10050.0},
            {"timestamp": "2026-01-02T04:00:00Z", "equity": 10030.0},
            {"timestamp": "2026-01-03T04:00:00Z", "equity": 10090.0},
        ],
    }


def example_01_contracts_and_registry() -> None:
    """Show contracts, schema validation, catalogs, warnings, serialization, registry."""
    print_header("1. Contracts & Registry")
    config = MetricConfig()

    print_kv("1.1 schema status", validate_schema_version("1.3.1", SCHEMA_COMPATIBILITY_MATRIX))
    print_kv("1.2 catalog count", validate_metric_catalog()["metric_count"])
    print_kv("1.2 metric formula", get_metric_definition("r_multiple").formula)

    warning = build_warning(
        "LOW_SAMPLE_SIZE",
        source_context="usage_example",
        detail={"trade_count": 2, "min_trades": 30},
    )
    flag = build_quality_flag(
        "LOW_PROFIT_FACTOR",
        detail={"profit_factor": 1.1, "threshold": 1.2},
    )
    print_kv("1.3 warning", warning.code)
    print_kv("1.3 quality flag", flag.code)
    print_kv("1.3 redacted", redact_sensitive_info({"api_key": "secret-token"}))

    safe_payload = to_json_safe({"cash": Decimal("12.34")}, PrecisionPolicy())
    print_kv("1.4 json safe", safe_payload)
    print_kv("1.4 canonical json", canonical_json(safe_payload))

    clear_active_requests()
    print_kv("1.5 registry request", registry_request_id("usage-req", config).value)
    print_kv("1.5 active requests", sorted(get_active_requests()))
    print_kv("1.5 catalog has tools", len(METRIC_DEFINITION_CATALOG) > 0)


def example_02_adapters() -> None:
    """Show protocols, canonicalization, and journal adapters."""
    print_header("2. Adapters")
    validate_adapter_contract(TradingResultAdapter)
    print_kv("2.1 protocol", "TradingResultAdapter valid")

    canonical = TradingResultAdapter.to_canonical(sample_trading_result())
    result = to_trading_result(canonical)
    print_kv("2.2 canonical phase", canonical["phase"])
    print_kv("2.2 dataclass result", result.result_id)

    journal = SimulationJournal(
        run_id="sim_usage",
        config_hash="cfg_hash",
        journal_ref="journal_usage",
        events=tuple(closed_trades()),
        equity_curve=tuple(sample_equity_curve()),
        strategy_id="usage_strategy",
        dataset_hash="dataset_hash",
        cost_model="fixed_costs",
        fill_model="bar_close",
        risk_policy_version="risk_v1",
    )
    journal_result = from_simulation_journal(journal)
    print_kv("2.3 journal result", journal_result.result_id)


def example_03_position_exposure() -> None:
    """Show position and exposure calculations."""
    print_header("3. Position Exposure")
    trades = sample_trades()
    print_kv("max gross size", max_gross_size_held(trades, MetricConfig()).value)
    print_kv("max net size", max_net_size_held(trades, MetricConfig()).value)
    print_kv("time in market hours", time_in_market_duration(closed_trades()))
    print_kv("percent time in market", percent_time_in_market(closed_trades(), 24.0))
    print_kv("open pnl", open_position_pnl(trades, MetricConfig()).value)
    print_kv("costs", {"slippage": slippage_paid(trades, MetricConfig()).value, "commission": commission_paid(trades, MetricConfig()).value, "swap": swap_paid(trades, MetricConfig()).value})


def example_04_trade_outcomes() -> None:
    """Show closed-trade outcomes and streak metrics."""
    print_header("4. Trade Outcomes")
    trades = closed_trades()
    print_kv("closed trades", len(trades))
    classes = classify_trades(trades, MetricConfig())
    print_kv("classes", {key: len(value) for key, value in classes.items()})
    print_kv("total trades", total_trades(trades, MetricConfig()).value)
    print_kv("win rate", win_rate(trades, MetricConfig()).value)
    print_kv("expectancy", expectancy(trades, MetricConfig()).value)
    print_kv("largest win/loss", (largest_win(trades, MetricConfig()).value, largest_loss(trades, MetricConfig()).value))
    print_kv("streaks", (max_consecutive_wins(trades, MetricConfig()).value, max_consecutive_losses(trades, MetricConfig()).value))


def example_05_r_multiples() -> None:
    """Show R-multiple analytics."""
    print_header("5. R-Multiples")
    trades = closed_trades()
    r_values, warnings = get_r_multiples(trades, MetricConfig())
    print_kv("r multiples", r_values)
    print_kv("r warnings", warnings)
    print_kv("avg R", avg_return_per_risk_unit(trades, MetricConfig()).value)
    print_kv("R stats", compute_r_trade_metrics(trades, MetricConfig()).value)
    print_kv("expectancy R", expectancy_r(trades, MetricConfig()).value)


def example_06_costs() -> None:
    """Show spread, slippage, and commission cost impact."""
    print_header("6. Costs")
    trades = closed_trades()
    config = MetricConfig()
    print_kv("spread impact", calculate_spread_cost_impact(trades, config).value)
    print_kv("slippage impact", calculate_slippage_impact(trades, config).value)
    print_kv("commission impact", calculate_commission_impact(trades, config).value)


def example_07_efficiency() -> None:
    """Show efficiency metrics."""
    print_header("7. Efficiency")
    trades = closed_trades()
    config = MetricConfig()
    print_kv("boundary", metrics_efficiency_boundary())
    print_kv("return per trade hour", return_per_trade_hour(trades, config).value)
    config = MetricConfig(metadata={"nominal_capital_deployed": 10000.0})
    print_kv("capital efficiency", capital_efficiency(trades, config).value)
    print_kv("loss containment", loss_containment_efficiency(trades, config).value)
    print_kv("exit efficiency", exit_efficiency(trades, config).value)
    print_kv("MAE/MFE R", get_mae_mfe_r(trades, config))
    print_kv("aggregate", calculate_efficiency_metrics(trades, config).value)


def example_08_time_analysis() -> None:
    """Show period, session, and duration analytics."""
    print_header("8. Time Analysis")
    trades = closed_trades()
    config = MetricConfig()
    print_kv("period PnL", calculate_period_analysis(trades, config).value)
    print_kv("long/short", calculate_long_short_split(trades, config).value)
    print_kv("sessions", calculate_session_performance(trades, config).value)
    print_kv("avg time in trade", avg_time_in_trade(trades, config).value)
    print_kv("period duration", trading_period_duration(trades, config).value)


def example_09_pnl() -> None:
    """Show PnL and growth metrics."""
    print_header("9. PnL")
    trades = closed_trades()
    equity = sample_equity_curve()
    print_kv("net/gross", {"net": net_profit(trades, MetricConfig()).value, "gross_profit": gross_profit(trades, MetricConfig()).value, "gross_loss": gross_loss(trades, MetricConfig()).value})
    print_kv("total return", total_return(equity))
    print_kv("return on initial", return_on_initial_capital(equity))
    print_kv("CAGR", cagr(10000.0, 10140.0, 1.0))
    print_kv(
        "max runup",
        max_runup(
            trades,
            MetricConfig(metadata={"initial_balance": 10000.0}),
        ).value,
    )


def example_10_curves() -> None:
    """Show balance and equity curve construction."""
    print_header("10. Curves")
    trades = closed_trades()
    config = MetricConfig(metadata={"initial_balance": 10000.0})
    print_kv("balance curve", balance_curve_from_closed_trades(trades, 10000.0))
    print_kv("balance metric", equity_curve_metric(trades, config).value)
    print_kv("equity alias", equity_curve(trades, 10000.0, "USD"))


def example_11_equity_returns() -> None:
    """Show return analytics from the canonical equity module."""
    print_header("11. Equity Returns")
    equity = sample_equity_curve()
    returns = sample_returns()
    print_kv("total return USD", total_return_usd(equity))
    print_kv("daily returns", daily_returns(equity))
    print_kv("benchmark returns", benchmark_returns([10000.0, 10050.0, 10030.0]))
    print_kv("return metrics", calculate_return_metrics(equity))
    print_kv("equity tool", calculate_equity_metrics(equity, request_id="usage-equity")["status"])
    print_kv("annualized return", annualized_return(returns))
    print_kv("vol/downside", (return_volatility(returns), downside_return_volatility(returns)))
    print_kv("return on account", return_on_account(equity, MetricConfig()).value)
    print_kv("streaks", win_loss_streaks(equity, MetricConfig()).value)


def example_12_drawdown() -> None:
    """Show drawdown calculations."""
    print_header("12. Drawdown")
    equity = sample_equity_curve()
    equity_values = [point["equity"] for point in equity]
    print_kv("boundary", metrics_drawdown_boundary())
    print_kv("series", drawdown_series(equity_values))
    print_kv("distribution", drawdown_distribution(equity, MetricConfig()).value)
    print_kv("ulcer index", ulcer_index(equity, MetricConfig()).value)
    print_kv("recovery factor", recovery_factor(140.0, 40.0))
    print_kv(
        "probability",
        drawdown_probability(
            equity,
            MetricConfig(metadata={"drawdown_threshold": 0.01}),
        ).value,
    )
    print_kv("tool", calculate_drawdown_metrics(equity, request_id="usage-dd")["status"])


def example_13_risk() -> None:
    """Show risk and volatility metrics."""
    print_header("13. Risk")
    returns = sample_returns()
    print_kv("volatility", volatility(returns, MetricConfig()).value)
    print_kv("annualized volatility", annualized_volatility(returns, MetricConfig()).value)
    print_kv("VaR/CVaR", (value_at_risk(returns, MetricConfig()).value, conditional_var(returns, MetricConfig()).value))
    print_kv("expected shortfall", expected_shortfall(returns, MetricConfig()).value)
    print_kv("tool", calculate_risk_metrics(returns, "usage-risk")["status"])


def example_14_ratios() -> None:
    """Show performance ratio metrics."""
    print_header("14. Ratios")
    returns = sample_returns()
    trades = closed_trades()
    print_kv("sharpe", sharpe_ratio(returns, MetricConfig()).value)
    print_kv("annualized sharpe", annualized_sharpe_ratio(returns))
    print_kv("sortino/omega", (sortino_ratio(returns, MetricConfig()).value, omega_ratio(returns, MetricConfig()).value))
    print_kv("profit factor", profit_factor(trades))
    print_kv("deflated sharpe", deflated_sharpe_ratio(1.25, returns))
    print_kv("tool", calculate_ratio_metrics(returns, request_id="usage-ratio")["status"])


def example_15_aggregate() -> None:
    """Show aggregate metric composition."""
    print_header("15. Aggregate")
    trades = closed_trades()
    print_kv("boundary", metrics_aggregate_boundary())
    print_kv("breakeven epsilon", breakeven_epsilon(None, MetricConfig()).value)
    print_kv("trade metrics", calculate_trade_metrics(trades, "usage-aggregate")["data"])
    print_kv("subset", calculate_analytics_for_subset(trades, MetricConfig()).value)
    print_kv("equity aggregate", aggregate_compute_equity_metrics(sample_returns(), MetricConfig()).value)


def example_16_boundaries() -> None:
    """Show request validation, limits, redaction, and primitive casting."""
    print_header("16. Boundaries")
    payload = {"trades": closed_trades(), "equity_curve": sample_equity_curve()}
    limits = AnalyticsLimits(max_trades=10, max_equity_points=10)
    validate_request(payload, "usage-boundary", limits)
    enforce_limits(WorkloadShape(trades_count=2, equity_points_count=4), limits)
    print_kv("request_id", request_id("usage-boundary", MetricConfig()).value)
    print_kv("float64", float64("1.25", MetricConfig()).value)
    print_kv("redacted", redact({"password": "secret"}, RedactionPolicy.STANDARD))


def example_17_multiple_testing() -> None:
    """Show multiple testing and overfit diagnostics."""
    print_header("17. Multiple Testing")
    returns = sample_returns()
    print_kv("white reality check", whites_reality_check([returns], returns))
    print_kv("PBO", probability_of_backtest_overfitting([returns]))
    print_kv("bonferroni", bonferroni_correction([0.01, 0.04]))
    print_kv("BH", benjamini_hochberg_correction([0.04, 0.01]))
    print_kv("stability", stability_score([{"profit_factor": 1.5}, {"profit_factor": 1.4}]))


def example_18_distributions() -> None:
    """Show distribution diagnostics."""
    print_header("18. Distributions")
    returns = sample_returns()
    print_kv("boundary", statistics_distribution_boundary())
    print_kv("moments", higher_moments(returns))
    print_kv("percentiles", percentile_summary(returns))
    print_kv("Jarque-Bera", jarque_bera_test(returns))
    print_kv("fit quality", distribution_fit_quality(returns))
    print_kv("histogram", histogram_data(returns, bins=3))
    print_kv("outliers", detect_outliers([1.0, 2.0, 3.0, 100.0]))
    print_kv("tool", calculate_distribution_metrics(returns, request_id="usage-dist")["status"])


def example_19_resampling() -> None:
    """Show bootstrap and permutation resampling."""
    print_header("19. Resampling")
    returns = sample_returns()
    print_kv("boundary", statistics_resampling_boundary())
    print_kv("bootstrap CI", bootstrap_confidence_intervals(returns, iterations=50, seed=7))
    print_kv("permutation p", permutation_test(returns, [0.0, 0.001, -0.001], iterations=50, seed=7))
    print_kv("prob above 0", bootstrap_probability_above_threshold(returns, threshold=0.0, seed=7, request_id="usage-boot")["data"])


def example_20_benchmark() -> None:
    """Show benchmark-relative metrics."""
    print_header("20. Benchmark")
    returns = sample_returns()
    benchmark = [0.005, -0.002, 0.006]
    print_kv("beta", beta(returns, benchmark))
    print_kv("alpha", alpha(returns, benchmark))
    print_kv("tracking error", tracking_error(returns, benchmark))
    print_kv("information ratio", information_ratio(returns, benchmark))
    print_kv("batting average", batting_average(returns, benchmark))
    print_kv("capture", up_down_capture(returns, benchmark))
    print_kv("tool", calculate_benchmark_metrics(returns, benchmark, request_id="usage-bench")["status"])


def example_21_scorecards() -> None:
    """Show non-binding strategy quality scorecards."""
    print_header("21. Scorecards")
    report = {
        "sections": {
            "trade_metrics": {"win_rate": 0.5, "total_trades": 2},
            "ratio_metrics": {"profit_factor": 2.5, "sharpe_ratio": 1.1, "sqn": 2.1},
            "drawdown_metrics": {"max_drawdown_percent": 4.0},
        }
    }
    print_kv("sqn", sqn(report).score)
    print_kv("sample warning", scorecard_sample_size_warning(report, StrategyQualityConfig()).warnings)
    print_kv("quality tool", evaluate_strategy_quality(report, request_id="usage-score")["data"])


def example_22_reports() -> None:
    """Show report builders, formatters, hashing, comparisons, and compliance evidence."""
    print_header("22. Reports")
    trading_result = sample_trading_result()
    report_response = build_analytics_report(trading_result, request_id="usage-report")
    report = report_response["data"]
    print_kv("report status", report_response["status"])
    print_kv("section eval", evaluate_section("benchmark_metrics", "skipped")["partial_report_status"])
    print_kv("backtest report", build_backtest_report(trading_result)["report_status"])
    print_kv("summary rows", format_summary_as_rows(report))
    print_kv("stats validation", calculate_statistical_validation(sample_returns(), request_id="usage-stat")["status"])
    print_kv("comparison", compare_analytics_reports(report, report, request_id="usage-compare")["data"])
    print_kv("compliance", calculate_prop_firm_compliance(report, request_id="usage-comply")["data"])
    print_kv("hash", compute_report_hash(report, HashPolicy.SHA256)[:12])
    print_kv("markdown", serialize_report(report, ReportFormat.MARKDOWN).content.splitlines()[0])


def example_23_dashboards() -> None:
    """Show dashboard projection and deterministic truncation."""
    print_header("23. Dashboards")
    report_response = build_analytics_report(sample_trading_result(), request_id="usage-dashboard-report")
    report = report_response["data"]
    report["equity_curve"] = sample_equity_curve()
    payload = build_overview_payload(report, request_id="usage-dashboard")
    typed_payload = build_overview_payload(report, config=DashboardConfig(max_points=2))
    truncated = truncate_series(
        [{"time": str(i), "equity": float(i)} for i in range(10)],
        TruncationPolicy(max_points=4),
    )
    print_kv("dashboard status", payload["status"])
    print_kv("summary cards", payload["data"]["summary_cards"])
    print_kv("typed payload", typed_payload.schema_version)
    print_kv("truncated", {"original": truncated.original_count, "returned": truncated.returned_count})


if __name__ == "__main__":
    example_01_contracts_and_registry()
    example_02_adapters()
    example_03_position_exposure()
    example_04_trade_outcomes()
    example_05_r_multiples()
    example_06_costs()
    example_07_efficiency()
    example_08_time_analysis()
    example_09_pnl()
    example_10_curves()
    example_11_equity_returns()
    example_12_drawdown()
    example_13_risk()
    example_14_ratios()
    example_15_aggregate()
    example_16_boundaries()
    example_17_multiple_testing()
    example_18_distributions()
    example_19_resampling()
    example_20_benchmark()
    example_21_scorecards()
    example_22_reports()
    example_23_dashboards()
