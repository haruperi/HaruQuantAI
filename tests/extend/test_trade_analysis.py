"""Unit tests for TradeAnalysis extension catalog."""

from app.extend.trade_analysis.charts import TradeAnalysisCatalog
from app.extend.what_if.base import WhatIfRecord


def _make_trade(
    record_id: int, open_sec: int, duration_sec: int, profit: float, direction: int = 1
) -> WhatIfRecord:
    return WhatIfRecord(
        record_id=record_id,
        kind="trade",
        direction=direction,  # type: ignore[arg-type]
        time_open_msc=open_sec * 1000,
        time_close_msc=(open_sec + duration_sec) * 1000,
        volume=1.0,
        profit=profit,
    )


class TestTradeAnalysisCatalog:
    """Test suite for TradeAnalysisCatalog across 27 chart definitions."""

    def test_all_27_descriptors_registered(self) -> None:
        """Assert all 27 chart definitions are present in DESCRIPTORS."""
        assert len(TradeAnalysisCatalog.DESCRIPTORS) == 27
        expected_keys = [
            "LongShortProfitLossChart",
            "LongShortTradesChart",
            "PLChart",
            "PLGrowthByDurationChart",
            "PLLongChart",
            "PLShortChart",
            "PLbyDayChart",
            "PLbyHourChart",
            "PLbyMonthChart",
            "PLbyTradeDurationChart",
            "PLbyWeekdayChart",
            "PLbyYearChart",
            "TradesByCloseTypeChart",
            "TradesByDayChart",
            "TradesByDurationChart",
            "TradesByHourChart",
            "TradesByMonthChart",
            "TradesByWeekdayChart",
            "TradesByYearChart",
            "WinLossCountByDayChart",
            "WinLossCountByHourChart",
            "WinLossCountByMonthChart",
            "WinLossCountByWeekdayChart",
            "WinLossPLByDayChart",
            "WinLossPLByHourChart",
            "WinLossPLByMonthChart",
            "WinLossPLByWeekdayChart",
        ]
        for k in expected_keys:
            assert k in TradeAnalysisCatalog.DESCRIPTORS

    def test_evaluate_hour_pl(self) -> None:
        """Assert PLbyHourChart aggregates trade profits by hour."""
        # Open time 1600000000 -> 2020-09-13 12:26:40 UTC (hour 12)
        trades = (
            _make_trade(1, 1600000000, 300, 100.0),
            _make_trade(2, 1600000000, 600, 50.0),
        )
        payload = TradeAnalysisCatalog.evaluate("PLbyHourChart", trades)
        assert len(payload.categories) == 24
        assert "12:00" in payload.categories
        idx = payload.categories.index("12:00")
        assert payload.series["NetProfit"][idx] == 150.0

    def test_evaluate_win_loss_count(self) -> None:
        """Assert WinLossCountByWeekdayChart counts wins and losses by weekday."""
        # 1600000000 is Sunday (idx 6)
        trades = (
            _make_trade(1, 1600000000, 300, 100.0),
            _make_trade(2, 1600000000, 300, -50.0),
        )
        payload = TradeAnalysisCatalog.evaluate("WinLossCountByWeekdayChart", trades)
        assert payload.categories == ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
        sun_idx = payload.categories.index("Sun")
        assert payload.series["Wins"][sun_idx] == 1.0
        assert payload.series["Losses"][sun_idx] == 1.0

    def test_evaluate_direction(self) -> None:
        """Assert LongShortProfitLossChart partitions by direction."""
        trades = (
            _make_trade(1, 1600000000, 300, 100.0, direction=1),
            _make_trade(2, 1600000000, 300, -40.0, direction=-1),
        )
        payload = TradeAnalysisCatalog.evaluate("LongShortProfitLossChart", trades)
        assert payload.categories == ("Long", "Short")
        assert payload.series["NetProfit"][0] == 100.0
        assert payload.series["NetProfit"][1] == -40.0
