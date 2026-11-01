"""Unit tests for EquityChartDailyChartService."""

from __future__ import annotations

from app.workspace.results.equity_chart_daily_chart import (
    DailyPlPoint,
    EquityChartDailyChartService,
)


class TestEquityChartDailyChartService:
    """Test suite for EquityChartDailyChartService."""

    def test_daily_chart_aggregation(self) -> None:
        """Verify grouping of trades into UTC day buckets and cumulative balance."""
        day_ms = 86_400_000
        trades = [
            {"close_time_ms": 1 * day_ms + 1000, "profit_loss": 100.0},
            {"close_time_ms": 1 * day_ms + 5000, "profit_loss": 50.0},
            {"close_time_ms": 2 * day_ms + 2000, "profit_loss": -75.0},
        ]
        series = EquityChartDailyChartService.build_series(10_000.0, trades)
        assert len(series) == 2

        d1 = series[0]
        assert d1.day_epoch_ms == 1 * day_ms
        assert d1.net_pl == 150.0
        assert d1.cumulative_balance == 10_150.0
        assert d1.trade_count == 2

        d2 = series[1]
        assert d2.day_epoch_ms == 2 * day_ms
        assert d2.net_pl == -75.0
        assert d2.cumulative_balance == 10_075.0
        assert d2.trade_count == 1

        d = d1.to_dict()
        assert d["trade_count"] == 2

    def test_daily_chart_empty_trades(self) -> None:
        """Verify empty series for empty trades list."""
        series = EquityChartDailyChartService.build_series(10_000.0, [])
        assert len(series) == 0

    def test_daily_pl_point_to_dict(self) -> None:
        """Verify DailyPlPoint serialization."""
        pt = DailyPlPoint(
            day_epoch_ms=86400000,
            net_pl=123.45,
            cumulative_balance=10123.45,
            trade_count=3,
        )
        d = pt.to_dict()
        assert d["day_epoch_ms"] == 86400000
        assert d["net_pl"] == 123.45
