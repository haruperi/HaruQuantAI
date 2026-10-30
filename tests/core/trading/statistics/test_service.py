"""Deterministic unit tests for StatisticsService performance computation."""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import pytest
from app.core.trading.backtest.contracts import TradeRecord
from app.core.trading.statistics import (
    BaseMetric,
    MetricResults,
    SampleSplit,
    StatisticsService,
)


def _make_trade(
    close_time: int,
    pnl: float,
    ticket: int = 1,
) -> dict[str, Any]:
    return {
        "ticket": ticket,
        "close_time": close_time,
        "net_pnl": pnl,
    }


def test_empty_trades_safe_boundaries() -> None:
    """Empty trades sequence safely returns zero values without ZeroDivisionError."""
    service = StatisticsService()
    results = service.compute([], initial_capital=100000.0)

    assert isinstance(results, MetricResults)
    metrics = results.all_trades
    assert metrics["net_profit"] == 0.0
    assert metrics["gross_profit"] == 0.0
    assert metrics["gross_loss"] == 0.0
    assert metrics["profit_factor"] == 0.0
    assert metrics["win_rate"] == 0.0
    assert metrics["trades_count"] == 0.0
    assert metrics["max_drawdown"] == 0.0
    assert metrics["max_drawdown_pct"] == 0.0
    assert metrics["sharpe_ratio"] == 0.0
    assert metrics["sortino_ratio"] == 0.0
    assert metrics["sqn"] == 0.0
    assert metrics["stability_r2"] == 0.0
    assert results.in_sample == {}
    assert results.out_of_sample == {}


def test_single_win() -> None:
    """Single winning trade produces exact profit factor inf and win rate 1.0."""
    service = StatisticsService()
    trades = [_make_trade(close_time=1000, pnl=500.0)]
    results = service.compute(trades, initial_capital=10000.0)

    m = results.all_trades
    assert m["net_profit"] == 500.0
    assert m["gross_profit"] == 500.0
    assert m["gross_loss"] == 0.0
    assert m["profit_factor"] == float("inf")
    assert m["win_rate"] == 1.0
    assert m["trades_count"] == 1.0
    assert m["winning_trades"] == 1.0
    assert m["losing_trades"] == 0.0
    assert m["max_drawdown"] == 0.0
    assert m["max_drawdown_pct"] == 0.0


def test_single_loss() -> None:
    """Single losing trade produces exact profit factor 0.0 and positive drawdown."""
    service = StatisticsService()
    trades = [_make_trade(close_time=1000, pnl=-300.0)]
    results = service.compute(trades, initial_capital=10000.0)

    m = results.all_trades
    assert m["net_profit"] == -300.0
    assert m["gross_profit"] == 0.0
    assert m["gross_loss"] == -300.0
    assert m["profit_factor"] == 0.0
    assert m["win_rate"] == 0.0
    assert m["trades_count"] == 1.0
    assert m["winning_trades"] == 0.0
    assert m["losing_trades"] == 1.0
    assert m["max_drawdown"] == 300.0
    assert m["max_drawdown_pct"] == pytest.approx(300.0 / 10000.0 * 100.0)


def test_known_drawdown_series() -> None:
    """Multi-trade series correctly tracks peak equity and maximum drawdown."""
    service = StatisticsService()
    # Initial: 100,000
    # 1: +1000 -> 101,000 (peak)
    # 2: -500  -> 100,500 (dd 500)
    # 3: -1000 -> 99,500  (dd 1500)
    # 4: +2000 -> 101,500 (new peak)
    # 5: -400  -> 101,100 (dd 400)
    trades = [
        _make_trade(100, 1000.0),
        _make_trade(200, -500.0),
        _make_trade(300, -1000.0),
        _make_trade(400, 2000.0),
        _make_trade(500, -400.0),
    ]
    results = service.compute(trades, initial_capital=100000.0)
    m = results.all_trades

    assert m["net_profit"] == 1100.0
    assert m["gross_profit"] == 3000.0
    assert m["gross_loss"] == -1900.0
    assert m["profit_factor"] == pytest.approx(3000.0 / 1900.0)
    assert m["win_rate"] == pytest.approx(2.0 / 5.0)
    assert m["max_drawdown"] == pytest.approx(1500.0)
    # Peak at trough was 101,000
    assert m["max_drawdown_pct"] == pytest.approx(1500.0 / 101000.0 * 100.0)


def test_close_time_stable_sorting() -> None:
    """Trades provided out of chronological order are sorted by close time."""
    service = StatisticsService()
    # Provide in reverse order
    trades = [
        _make_trade(close_time=300, pnl=500.0),  # 3rd
        _make_trade(close_time=100, pnl=1000.0),  # 1st
        _make_trade(close_time=200, pnl=-800.0),  # 2nd
    ]
    results = service.compute(trades, initial_capital=10000.0)
    m = results.all_trades

    # If evaluated in sorted order:
    # 100: +1000 -> 11,000
    # 200: -800  -> 10,200 (dd 800)
    # 300: +500  -> 10,700
    # Max DD = 800
    assert m["max_drawdown"] == pytest.approx(800.0)


def test_is_oos_date_split() -> None:
    """Date-based split partitions trades accurately into In-Sample and Out-of-Sample."""
    service = StatisticsService()
    split_date = datetime(2025, 6, 1, 0, 0, 0, tzinfo=UTC)
    split_ts = int(split_date.timestamp())

    trades = [
        _make_trade(close_time=split_ts - 200, pnl=400.0),  # IS
        _make_trade(close_time=split_ts - 100, pnl=600.0),  # IS
        _make_trade(close_time=split_ts, pnl=-200.0),  # IS (inclusive)
        _make_trade(close_time=split_ts + 100, pnl=1000.0),  # OOS
        _make_trade(close_time=split_ts + 200, pnl=-500.0),  # OOS
    ]

    split = SampleSplit(split_type="DATE", split_date=split_date)
    results = service.compute(trades, sample_split=split)

    assert results.all_trades["trades_count"] == 5.0
    assert results.all_trades["net_profit"] == 1300.0

    # IS partition (3 trades)
    assert results.in_sample["trades_count"] == 3.0
    assert results.in_sample["net_profit"] == 800.0
    assert results.in_sample["gross_profit"] == 1000.0
    assert results.in_sample["gross_loss"] == -200.0

    # OOS partition (2 trades)
    assert results.out_of_sample["trades_count"] == 2.0
    assert results.out_of_sample["net_profit"] == 500.0
    assert results.out_of_sample["gross_profit"] == 1000.0
    assert results.out_of_sample["gross_loss"] == -500.0


def test_is_oos_ratio_split() -> None:
    """Ratio-based split partitions trades by fractional cutoff."""
    service = StatisticsService()
    # 10 trades: 7 IS (70%), 3 OOS (30%)
    trades = [_make_trade(close_time=1000 + i * 10, pnl=100.0) for i in range(10)]

    split = SampleSplit(split_type="RATIO", in_sample_ratio=0.7)
    results = service.compute(trades, sample_split=split)

    assert results.all_trades["trades_count"] == 10.0
    assert results.in_sample["trades_count"] == 7.0
    assert results.in_sample["net_profit"] == 700.0
    assert results.out_of_sample["trades_count"] == 3.0
    assert results.out_of_sample["net_profit"] == 300.0


def test_sqn_and_stability_r2() -> None:
    """SQN formula and linear regression stability R^2 produce expected values."""
    service = StatisticsService()
    # 5 trades of identical +100 profit
    trades = [_make_trade(close_time=1000 + i * 10, pnl=100.0) for i in range(5)]
    results = service.compute(trades, initial_capital=10000.0)
    m = results.all_trades

    # When all trades have identical PnL, std = 0 -> SQN is defined as 0.0 (safe boundary)
    assert m["sqn"] == 0.0
    # Perfectly straight upward line -> R^2 should be 1.0
    assert m["stability_r2"] == pytest.approx(1.0)

    # Now trades with variance: [100, 200, 300]
    # mean = 200, var = ((100-200)^2 + 0 + (300-200)^2) / 2 = 10000 -> std = 100
    # SQN = sqrt(3) * (200 / 100) = 2 * sqrt(3)
    trades_var = [
        _make_trade(10, 100.0),
        _make_trade(20, 200.0),
        _make_trade(30, 300.0),
    ]
    res_var = service.compute(trades_var, initial_capital=10000.0)
    expected_sqn = math.sqrt(3) * 2.0
    assert res_var.all_trades["sqn"] == pytest.approx(expected_sqn)


def test_custom_metric_registration_and_dag() -> None:
    """Custom BaseMetric implementations are ordered and evaluated cleanly."""

    class CustomMetricA(BaseMetric):
        name = "MetricA"

        def compute(
            self, trades: Sequence[dict[str, Any]], initial_capital: float = 10000.0
        ) -> float:
            return float(len(trades) * 42.0)

    class CustomMetricB(BaseMetric):
        name = "MetricB"

        def compute(
            self, trades: Sequence[dict[str, Any]], initial_capital: float = 10000.0
        ) -> float:
            # Depends on MetricA conceptually
            return float(len(trades) * 100.0)

    service = StatisticsService()
    metric_a = CustomMetricA()
    metric_b = CustomMetricB()

    service.register_metric(metric_b, depends_on=["MetricA"])
    service.register_metric(metric_a)

    trades = [_make_trade(10, 50.0), _make_trade(20, -20.0)]
    results = service.compute(trades)

    assert results.all_trades["MetricA"] == 2.0 * 42.0
    assert results.all_trades["MetricB"] == 2.0 * 100.0

    # Unregister metric
    service.unregister_metric("MetricB")
    results2 = service.compute(trades)
    assert "MetricB" not in results2.all_trades
    assert "MetricA" in results2.all_trades


def test_domain_trade_record_compatibility() -> None:
    """TradeRecord domain objects pass seamlessly into compute()."""
    service = StatisticsService()
    trade = TradeRecord(
        ticket=101,
        symbol="EURUSD",
        direction=1,
        volume=1.0,
        open_time=1000,
        open_price=1.1000,
        close_time=1060,
        close_price=1.1050,
        net_pnl=50.0,
    )
    results = service.compute([trade], initial_capital=50000.0)
    assert results.all_trades["net_profit"] == 50.0
    assert results.all_trades["trades_count"] == 1.0
