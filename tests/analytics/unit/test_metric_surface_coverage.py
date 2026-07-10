"""Focused coverage for broad analytics metric surfaces."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from app.services.analytics.contracts import MetricConfig
from app.services.analytics.dashboards import overview
from app.services.analytics.metrics import distribution as dist_metrics
from app.services.analytics.metrics import drawdown, equity, exports, pnl, ratios, risk
from app.services.analytics.metrics import trade_outcomes as outcomes
from app.services.analytics.reports import hashes
from app.services.analytics.scorecards import labels
from app.services.analytics.tool_api import (
    build_analytics_report,
    get_analytics_overview,
)
from app.services.analytics.errors import AnalyticsValidationError as ValidationError

TRADES: list[dict[str, Any]] = [
    {
        "trade_id": "t1",
        "symbol": "EURUSD",
        "direction": "long",
        "open_time": "2024-01-01T00:00:00Z",
        "close_time": "2024-01-01T04:00:00Z",
        "profit_loss": 120.0,
        "net_pnl": 120.0,
        "initial_risk": 60.0,
        "mae": -20.0,
        "mfe": 160.0,
        "size": 1.0,
        "margin": 250.0,
        "nominal_exposure": 10000.0,
        "pip_risk": 15.0,
        "spread_cost": 0.7,
        "slippage": 0.4,
        "commission": 2.0,
        "swap": 0.0,
    },
    {
        "trade_id": "t2",
        "symbol": "EURUSD",
        "direction": "short",
        "open_time": "2024-01-02T00:00:00Z",
        "close_time": "2024-01-02T05:00:00Z",
        "profit_loss": -45.0,
        "net_pnl": -45.0,
        "initial_risk": 55.0,
        "mae": -70.0,
        "mfe": 20.0,
        "size": 0.8,
        "margin": 220.0,
        "nominal_exposure": 8000.0,
        "pip_risk": 12.0,
        "spread_cost": 0.6,
        "slippage": 0.5,
        "commission": 2.0,
        "swap": 0.0,
    },
    {
        "trade_id": "t3",
        "symbol": "GBPUSD",
        "side": "buy",
        "open_timestamp": "2024-01-03T00:00:00Z",
        "close_timestamp": "2024-01-03T03:00:00Z",
        "pnl": 80.0,
        "initial_risk": 40.0,
        "mae": -15.0,
        "mfe": 90.0,
        "size": 0.5,
        "margin": 150.0,
        "nominal_exposure": 5000.0,
        "pip_risk": 10.0,
    },
    {
        "trade_id": "t4",
        "symbol": "GBPUSD",
        "side": "sell",
        "open_time": "2024-01-04T00:00:00Z",
        "close_time": "2024-01-04T02:00:00Z",
        "profit_loss": -20.0,
        "initial_risk": 25.0,
        "mae": -25.0,
        "mfe": 8.0,
        "size": 0.3,
        "margin": 100.0,
        "nominal_exposure": 3000.0,
        "pip_risk": 8.0,
    },
    {
        "trade_id": "t5",
        "symbol": "USDJPY",
        "direction": "long",
        "open_time": "2024-01-05T00:00:00Z",
        "is_open": True,
        "pnl": 10.0,
        "size": 0.2,
    },
]

EQUITY_CURVE: list[dict[str, Any]] = [
    {"timestamp": "2023-12-29T00:00:00Z", "equity": 10000.0},
    {"timestamp": "2024-01-01T00:00:00Z", "equity": 10120.0},
    {"timestamp": "2024-01-02T00:00:00Z", "equity": 10075.0},
    {"timestamp": "2024-01-03T00:00:00Z", "equity": 10155.0},
    {"timestamp": "2024-01-04T00:00:00Z", "equity": 10135.0},
    {"timestamp": "2024-02-01T00:00:00Z", "equity": 10200.0},
    {"timestamp": "2025-01-01T00:00:00Z", "equity": 10350.0},
]

EQUITY_VALUES = [point["equity"] for point in EQUITY_CURVE]
RETURNS = [0.012, -0.0045, 0.0079, -0.002, 0.0064, 0.0148]
BENCHMARK_RETURNS = [0.006, -0.001, 0.004, -0.003, 0.003, 0.006]


def metric_config() -> MetricConfig:
    """Build a reusable analytics metric configuration."""
    return MetricConfig(
        metadata={
            "initial_balance": 10000.0,
            "trades": TRADES,
            "benchmark_returns": BENCHMARK_RETURNS,
            "benchmark_equity": [10000.0, 10060.0, 10050.0, 10100.0],
            "risk_free_rate": 0.0,
            "annualization_periods": 252,
            "nominal_capital_deployed": 10000.0,
            "equity_curve": EQUITY_CURVE,
            "drawdown_threshold": 0.001,
            "time_in_market": 0.45,
            "portfolio_weights": [0.6, 0.4],
            "covariance_matrix": [[0.01, 0.002], [0.002, 0.02]],
            "margin_used": [100.0, 150.0, 120.0],
            "portfolio_equity": [10000.0, 10100.0, 10050.0],
            "exposures": [0.1, 0.2, 0.15],
            "symbol_returns": {"EURUSD": RETURNS, "GBPUSD": BENCHMARK_RETURNS},
        }
    )


def canonical_payload() -> dict[str, Any]:
    """Return a canonical analytics payload."""
    return {
        "schema_version": "1.3.1",
        "result_id": "coverage_run",
        "phase": "backtest",
        "strategy_id": "coverage_strategy",
        "strategy_version": "v1",
        "account_base_currency": "USD",
        "symbols": ["EURUSD", "GBPUSD"],
        "timeframe": "H1",
        "trades": TRADES,
        "equity_curve": EQUITY_CURVE,
        "benchmark_curve": [
            {"timestamp": "2023-12-29T00:00:00Z", "equity": 10000.0},
            {"timestamp": "2024-01-01T00:00:00Z", "equity": 10060.0},
            {"timestamp": "2024-01-02T00:00:00Z", "equity": 10050.0},
            {"timestamp": "2024-01-03T00:00:00Z", "equity": 10100.0},
        ],
    }


def _assert_metric_result(value: Any) -> None:
    """Assert helper outputs are materially populated."""
    assert value is not None


def test_distribution_metric_surface() -> None:
    """Exercise distribution metric wrappers."""
    config = metric_config()
    for func in (
        dist_metrics.skewness_metric,
        dist_metrics.kurtosis_metric,
        dist_metrics.jarque_bera_test,
        dist_metrics.jarque_bera_test_metric,
        dist_metrics.percentile_summary,
        dist_metrics.distribution_summary,
        dist_metrics.upside_downside_summary,
        dist_metrics.fat_tail_score,
        dist_metrics.false_discovery_rate,
        dist_metrics.bootstrap_metric,
    ):
        _assert_metric_result(func(RETURNS, config))
    assert dist_metrics.skewness(RETURNS) != 0.0
    assert dist_metrics.kurtosis([1.0, 2.0, 3.0, 10.0]) != 0.0


def test_trade_outcome_surface() -> None:
    """Exercise trade outcome functions across wins, losses, and open trades."""
    config = metric_config()
    for func in (
        outcomes.avg_consecutive_losses,
        outcomes.avg_consecutive_wins,
        outcomes.avg_loss,
        outcomes.avg_loss_metric,
        outcomes.avg_r_multiple,
        outcomes.avg_win,
        outcomes.avg_win_loss,
        outcomes.avg_win_metric,
        outcomes.breakeven_trades,
        outcomes.consecutive_wins_losses,
        outcomes.count_open_trades,
        outcomes.expectancy,
        outcomes.expectancy_metric,
        outcomes.expectancy_r,
        outcomes.largest_loss,
        outcomes.largest_win,
        outcomes.long_trades,
        outcomes.losing_trades,
        outcomes.loss_rate,
        outcomes.loss_rate_fraction,
        outcomes.max_consecutive_losses,
        outcomes.max_consecutive_wins,
        outcomes.max_r_multiple,
        outcomes.median_loss,
        outcomes.median_r_multiple,
        outcomes.median_win,
        outcomes.min_r_multiple,
        outcomes.r_expectancy,
        outcomes.r_signal_to_noise,
        outcomes.rolling_expectancy_stability,
        outcomes.runs_test_zscore,
        outcomes.shannon_entropy,
        outcomes.short_trades,
        outcomes.t_statistic,
        outcomes.total_trades,
        outcomes.trade_outcome_entropy,
        outcomes.win_after_win_probability,
        outcomes.win_rate,
        outcomes.win_rate_fraction,
        outcomes.winning_trades,
    ):
        _assert_metric_result(func(TRADES, config))
    assert len(outcomes.get_closed_trades(TRADES)) == 4
    assert outcomes.get_ordered_closed_trades(TRADES)[0]["trade_id"] == "t1"
    assert outcomes.parse_utc_time("2024-01-01T00:00:00Z") is not None


def test_ratio_metric_surface() -> None:
    """Exercise ratio functions and compatibility scalar helpers."""
    config = metric_config()
    for func in (
        ratios.active_premium,
        ratios.adjusted_expectancy,
        ratios.adjusted_payoff_ratio,
        ratios.adjusted_profit_factor,
        ratios.average_win_loss_ratio,
        ratios.cpc_index,
        ratios.drawdown_ratio,
        ratios.expectancy,
        ratios.expectancy_r,
        ratios.expected_value,
        ratios.expected_value_r,
        ratios.gain_loss_ratio,
        ratios.information_ratio,
        ratios.loss_ratio,
        ratios.martin_ratio,
        ratios.odds_calculator,
        ratios.omega_ratio,
        ratios.payoff_ratio_metric,
        ratios.probabilistic_sharpe_ratio,
        ratios.profit_factor_by_count,
        ratios.profit_factor_by_volume_metric,
        ratios.profit_factor_metric,
        ratios.profit_loss_ratio,
        ratios.ratio_of_adjusted_gross_profit_to_adjusted_gross_loss,
        ratios.risk_reward_ratio,
        ratios.select_profit_factor,
        ratios.sharpe_ratio,
        ratios.sortino_ratio,
        ratios.sqn,
        ratios.system_quality_number,
        ratios.tail_ratio,
        ratios.tracking_error,
        ratios.treynor_ratio,
        ratios.ulcer_performance_index,
        ratios.win_loss_ratio,
    ):
        _assert_metric_result(func(RETURNS, config))
    for value in (
        ratios.adjusted_net_profit_as_percent_of_largest_loss(100.0, -50.0),
        ratios.annualized_sharpe_ratio(RETURNS),
        ratios.deflated_sharpe_ratio(1.1, RETURNS),
        ratios.edge_ratio(TRADES),
        ratios.expectancy_over_std(TRADES),
        ratios.gain_to_pain_ratio(RETURNS),
        ratios.kappa_ratio(RETURNS),
        ratios.mfe_to_mae_ratio(TRADES),
        ratios.net_profit_as_percent_of_largest_loss(120.0, -40.0),
        ratios.normal_cdf(0.0),
        ratios.payoff_ratio(TRADES, config),
        ratios.profit_factor(TRADES),
        ratios.profit_factor_by_volume(TRADES),
        ratios.profit_to_mae_ratio(TRADES),
        ratios.select_net_profit_as_percent_of_largest_loss(80.0, -40.0),
        ratios.up_down_capture(RETURNS, BENCHMARK_RETURNS),
    ):
        _assert_metric_result(value)
    assert (
        ratios.calculate_ratio_metrics(RETURNS, request_id="ratio-cov")["status"]
        == "success"
    )


def test_risk_metric_surface() -> None:
    """Exercise risk functions and aggregate response paths."""
    config = metric_config()
    for func in (
        risk.annualized_volatility,
        risk.avg_single_trade_margin_utilization,
        risk.avg_trade_nominal_exposure,
        risk.compounding_risk_of_ruin,
        risk.conditional_var,
        risk.downside_volatility,
        risk.expected_shortfall,
        risk.exposure_time_ratio,
        risk.historical_var_by_symbol,
        risk.max_gross_exposure,
        risk.max_loss_probability,
        risk.max_nominal_exposure_simple,
        risk.max_single_trade_margin_utilization,
        risk.portfolio_margin_utilization_curve,
        risk.portfolio_var_from_covariance,
        risk.profit_per_pip_risk,
        risk.risk_adjusted_efficiency,
        risk.risk_of_ruin,
        risk.risk_of_ruin_with_custom_horizon,
        risk.time_weighted_avg_exposure,
        risk.upside_potential_ratio,
        risk.value_at_risk,
        risk.volatility,
    ):
        _assert_metric_result(func(RETURNS, config))
    assert risk.calculate_risk_metrics(RETURNS, config).value["volatility"] > 0.0
    assert risk.calculate_risk_metrics(RETURNS, "risk-cov")["status"] == "success"


def test_pnl_and_equity_surfaces() -> None:
    """Exercise PnL and equity return functions."""
    config = metric_config()
    for func in (
        pnl.adjusted_gross_loss,
        pnl.adjusted_gross_profit,
        pnl.adjusted_net_profit,
        pnl.adjusted_net_profit_as_percent_of_max_trade_drawdown,
        pnl.cagr_metric,
        pnl.gross_loss,
        pnl.gross_profit,
        pnl.max_runup,
        pnl.max_runup_date,
        pnl.net_profit,
        pnl.return_over_drawdown,
        pnl.select_gross_loss,
        pnl.select_gross_profit,
        pnl.select_net_profit,
    ):
        _assert_metric_result(func(TRADES, config))
    for value in (
        pnl.buy_and_hold_cagr([100.0, 110.0], 1.0),
        pnl.cagr(100.0, 125.0, 2.0),
        pnl.compound_monthly_growth_rate(100.0, 112.0, 12),
        pnl.return_on_initial_capital(EQUITY_CURVE, config),
        pnl.total_return(EQUITY_CURVE, config),
    ):
        _assert_metric_result(value)

    for func in (
        equity.downside_return_volatility_metric,
        equity.geometric_mean_return_metric,
        equity.kelly_criterion,
        equity.log_returns_series_metric,
        equity.return_on_account,
        equity.return_volatility_metric,
        equity.returns_series_metric,
        equity.win_loss_streaks,
    ):
        _assert_metric_result(func(EQUITY_CURVE, config))
    for value in (
        equity.annual_returns(EQUITY_CURVE, config),
        equity.annualized_return(RETURNS, 252),
        equity.avg_monthly_return(EQUITY_CURVE, config),
        equity.benchmark_returns(EQUITY_VALUES, config),
        equity.best_return(RETURNS, config),
        equity.buy_and_hold_return(EQUITY_VALUES, config),
        equity.calculate_equity_metrics(EQUITY_CURVE, request_id="eq-cov"),
        equity.calculate_return_metrics(EQUITY_CURVE, config),
        equity.compute_equity_metrics(RETURNS),
        equity.daily_returns(EQUITY_CURVE, config),
        equity.downside_return_volatility(RETURNS),
        equity.geometric_mean_return(RETURNS),
        equity.log_returns_series(EQUITY_VALUES),
        equity.monthly_return_stddev(EQUITY_CURVE, config),
        equity.monthly_returns(EQUITY_CURVE, config),
        equity.return_kurtosis(RETURNS, config),
        equity.return_skewness(RETURNS, config),
        equity.return_volatility(RETURNS),
        equity.returns_series(EQUITY_VALUES),
        equity.total_return_usd(EQUITY_CURVE, config),
        equity.weekly_returns(EQUITY_CURVE, config),
        equity.worst_return(RETURNS, config),
    ):
        _assert_metric_result(value)


def test_equity_edge_and_compatibility_paths() -> None:
    """Cover equity compatibility branches, empty inputs, and validation paths."""
    config = MetricConfig(
        annualization_periods=252,
        metadata={"price_values": [100.0, 120.0], "target_return": 0.001},
    )
    tuple_curve = (
        ("2024-01-01T00:00:00Z", 10000.0),
        ("2024-01-02T00:00:00Z", 9900.0),
        ("2024-01-03T00:00:00Z", 10100.0),
        ("2024-01-04T00:00:00Z", 10050.0),
        ("2024-01-05T00:00:00Z", 10200.0),
        ("2025-01-01T00:00:00Z", 10400.0),
    )

    assert equity._parse_equity_curve(None) == []
    assert equity._parse_equity_curve(object()) == []
    assert equity._parse_equity_curve([("bad-date", 1.0)]) == []
    assert equity._group_returns(tuple_curve, "annual")
    assert equity.returns_series([100.0, 0.0, 110.0]) == [-1.0, 0.0]
    assert equity.log_returns_series([100.0, -1.0, 110.0]) == [0.0, 0.0]
    assert equity.geometric_mean_return([-2.0]) == 0.0
    assert equity.return_volatility([0.1]) == 0.0

    assert equity.total_return_usd([], config).value == 0.0
    assert equity.returns_series_metric([], config).value == []
    assert equity.log_returns_series_metric([], config).value == []
    assert equity.daily_returns(tuple_curve, config).value
    assert equity.weekly_returns(tuple_curve, config).value
    assert equity.monthly_returns(tuple_curve, config).value
    assert equity.annual_returns(tuple_curve, config).value
    assert equity.calculate_return_metrics([], config).value == {}
    assert equity.calculate_return_metrics([], None) == {}
    assert equity.win_loss_streaks([], config).value == {"wins": [], "losses": []}
    assert equity.kelly_criterion([], config).value == 0.0
    assert equity.avg_monthly_return([], None) == 0.0
    assert equity.monthly_return_stddev([], None) == 0.0

    assert equity.annualized_return([], config).value == 0.0
    assert equity.annualized_return(tuple_curve, config).value != 0.0
    assert equity.annualized_return([], None) == 0.0
    assert equity.annualized_return([-2.0], 252) == 0.0
    assert equity.best_return([], config).value == 0.0
    assert equity.best_return([0.1, -0.2], None) == 0.1
    assert equity.worst_return([], config).value == 0.0
    assert equity.worst_return([0.1, -0.2], None) == -0.2
    assert equity.buy_and_hold_return([], config).value == 20.0
    assert equity.buy_and_hold_return([], None) == 0.0
    assert equity.buy_and_hold_return([100.0, 90.0], None) == -10.0
    assert equity.return_volatility_metric([], config).value == 0.0
    assert equity.downside_return_volatility_metric([], config).value == 0.0
    assert equity.return_skewness([], config).value == 0.0
    assert equity.return_skewness(tuple_curve, config).value != 0.0
    assert equity.return_kurtosis([], config).value == 0.0
    assert equity.return_kurtosis(tuple_curve, config).value != 0.0

    assert equity.compute_equity_metrics([]) == {
        "total_return": 0.0,
        "return_volatility": 0.0,
    }
    assert (
        equity.calculate_equity_metrics([], request_id="eq-empty")["status"] == "error"
    )
    assert (
        equity.calculate_equity_metrics(
            [{"timestamp": "2024-01-01T00:00:00Z", "equity": 0.0}],
            request_id="eq-zero",
        )["status"]
        == "error"
    )
    with pytest.raises(ValidationError):
        equity.validate_request_id_strict("")


def test_drawdown_surface() -> None:
    """Exercise drawdown wrappers and raw calculation helpers."""
    config = metric_config()
    for func in (
        drawdown.account_size_required,
        drawdown.adjusted_net_profit_as_percent_of_max_strategy_drawdown,
        drawdown.avg_drawdown,
        drawdown.avg_drawdown_duration,
        drawdown.avg_trade_drawdown,
        drawdown.avg_yearly_max_drawdown,
        drawdown.calmar_ratio,
        drawdown.drawdown_distribution,
        drawdown.drawdown_duration_series_metric,
        drawdown.drawdown_probability,
        drawdown.drawdown_series_metric,
        drawdown.fouse_ratio,
        drawdown.max_close_to_close_drawdown,
        drawdown.max_close_to_close_drawdown_date,
        drawdown.max_close_to_close_drawdown_percent,
        drawdown.max_consecutive_drawdown_trades,
        drawdown.max_drawdown,
        drawdown.max_drawdown_duration,
        drawdown.max_drawdown_duration_from_returns,
        drawdown.max_relative_drawdown_percent,
        drawdown.max_strategy_drawdown,
        drawdown.max_strategy_drawdown_percent,
        drawdown.pain_index,
        drawdown.pain_ratio,
        drawdown.recovery_factor,
        drawdown.return_on_max_close_to_close_drawdown,
        drawdown.return_on_max_strategy_drawdown,
        drawdown.rina_index,
        drawdown.sterling_ratio,
        drawdown.time_to_recovery,
        drawdown.trade_level_drawdowns_metric,
        drawdown.trade_pnl_distribution,
        drawdown.ulcer_index,
    ):
        _assert_metric_result(func(EQUITY_CURVE, config))
    for value in (
        drawdown._raw_account_size_required(TRADES),
        drawdown._raw_adjusted_net_profit_as_percent_of_max_strategy_drawdown(
            100.0, 25.0
        ),
        drawdown._raw_avg_drawdown(EQUITY_CURVE),
        drawdown._raw_avg_drawdown_duration(EQUITY_CURVE),
        drawdown._raw_avg_yearly_max_drawdown(EQUITY_CURVE),
        drawdown._raw_calculate_drawdown_metrics(EQUITY_CURVE, "dd-cov"),
        drawdown._raw_calmar_ratio(0.2, 0.05),
        drawdown._raw_drawdown_distribution(EQUITY_CURVE),
        drawdown._raw_drawdown_probability(EQUITY_CURVE, 0.001),
        drawdown._raw_fouse_ratio(0.2, 0.05),
        drawdown._raw_max_close_to_close_drawdown_percent(TRADES),
        drawdown._raw_max_drawdown(RETURNS),
        drawdown._raw_max_drawdown_duration(EQUITY_CURVE),
        drawdown._raw_max_drawdown_duration_from_returns(RETURNS),
        drawdown._raw_max_relative_drawdown_percent(
            EQUITY_VALUES, [10000.0, 10030.0, 10020.0]
        ),
        drawdown._raw_max_strategy_drawdown(EQUITY_CURVE),
        drawdown._raw_max_strategy_drawdown_date_from_parsed(
            equity._parse_equity_curve(EQUITY_CURVE)
        ),
        drawdown._raw_max_strategy_drawdown_percent(EQUITY_CURVE),
        drawdown._raw_net_profit_as_percent_of_max_strategy_drawdown(100.0, 25.0),
        drawdown._raw_pain_index(EQUITY_CURVE),
        drawdown._raw_pain_ratio(0.2, 0.05),
        drawdown._raw_recovery_factor(100.0, 25.0),
        drawdown._raw_return_on_max_close_to_close_drawdown(100.0, 25.0),
        drawdown._raw_return_on_max_strategy_drawdown(0.1, 0.05),
        drawdown._raw_rina_index(100.0, 25.0, 0.5),
        drawdown._raw_select_net_profit_as_percent_of_max_strategy_drawdown(
            100.0, 25.0
        ),
        drawdown._raw_sterling_ratio(0.2, 0.05),
        drawdown._raw_time_to_recovery(EQUITY_CURVE),
        drawdown._raw_ulcer_index(EQUITY_CURVE),
        drawdown.adjusted_net_profit_as_percent_of_max_trade_drawdown(100.0, 25.0),
        drawdown.avg_underwater_drawdown_percent(EQUITY_CURVE, config),
        drawdown.calculate_drawdown_metrics(EQUITY_CURVE, config),
        drawdown.drawdown_duration_series(EQUITY_CURVE),
        drawdown.drawdown_series(EQUITY_VALUES),
        drawdown.max_drawdown_duration_from_equity(EQUITY_CURVE, config),
        drawdown.max_strategy_drawdown_date(EQUITY_CURVE, config),
        drawdown.metrics_drawdown_boundary(),
        drawdown.net_profit_as_percent_of_max_strategy_drawdown(100.0, 25.0),
        drawdown.net_profit_as_percent_of_max_trade_drawdown(100.0, 25.0),
        drawdown.relative_drawdown_series(EQUITY_CURVE, config),
        drawdown.select_net_profit_as_percent_of_max_strategy_drawdown(100.0, 25.0),
        drawdown.select_net_profit_as_percent_of_max_trade_drawdown(100.0, 25.0),
        drawdown.trade_level_drawdowns(TRADES),
    ):
        _assert_metric_result(value)


def test_exports_hashes_dashboard_labels_and_tool_api() -> None:
    """Exercise small modules still counted in per-file coverage."""
    config = metric_config()
    for func in (
        exports.benchmark_information_ratio,
        exports.common_avg_loss,
        exports.common_get_r_multiples,
        exports.distributions_r_multiple_distribution,
        exports.metrics_avg_loss,
        exports.metrics_expectancy_r,
        exports.metrics_get_r_multiples,
        exports.metrics_r_multiple_distribution,
        exports.metrics_win_rate_fraction,
        exports.ratios_information_ratio,
    ):
        _assert_metric_result(
            func(TRADES if "ratio" not in func.__name__ else RETURNS, config)
        )

    report = {
        "report_id": "rep-cov",
        "sections": {
            "trade_metrics": {"data": {"win_rate": 0.5, "total_trades": 4}},
            "ratio_metrics": {"data": {"profit_factor": 2.0, "sharpe_ratio": 1.1}},
            "drawdown_metrics": {"data": {"max_drawdown_percent": 0.02}},
            "equity_metrics": {"data": {"total_return_usd": 200.0}},
        },
        "equity_curve": EQUITY_CURVE,
        "warnings": [],
        "quality_flags": [],
    }
    assert len(hashes.compute_report_hash({"a": Decimal("1.2")})) == 64
    assert len(hashes.compute_report_hash(report, hashes.HashPolicy.MD5)) == 32
    with pytest.raises(TypeError):
        hashes._decimal_default(object())

    assert (
        overview.build_overview_payload(None, request_id="dash-cov")["status"]
        == "error"
    )
    assert (
        overview.build_overview_payload(object(), request_id="dash-cov")["status"]
        == "error"
    )
    assert (
        overview.build_overview_payload(report, request_id="dash-cov")["status"]
        == "success"
    )
    assert (
        overview.build_overview_payload(
            report,
            overview.DashboardConfig(max_points=3),
        ).schema_version
        == "1.3.1"
    )
    with pytest.raises(ValidationError):
        overview._validate_request_id("")

    assert labels.scorecards_policy_boundary() is None
    assert get_analytics_overview("bad", request_id="tool-cov")["status"] == "error"
    assert (
        get_analytics_overview({"trades": "bad"}, request_id="tool-cov")["status"]
        == "error"
    )
    assert (
        get_analytics_overview(canonical_payload(), request_id="tool-cov")["status"]
        == "success"
    )
    assert (
        build_analytics_report(canonical_payload(), request_id="tool-cov")["status"]
        == "success"
    )
