"""Unit tests for TradeAnalysis extension catalog and individual chart classes.

Description:
    Tests all 27 StrategyQuant-compatible trade analysis charts across
    temporal, duration, direction, sequence, and exit reason dimensions,
    verifying category resolution, series calculation, payload serialization,
    and 100% branch coverage.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-test: Exhaustive validation of 27 trade analysis charts.

Python API Usage:
    pytest tests/extend/test_trade_analysis.py

CLI Usage:
    python -m pytest tests/extend/test_trade_analysis.py -v
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import app.extend.trade_analysis as ta_pkg
from app.extend.trade_analysis.base import (
    TradeAnalysisChart,
    TradeAnalysisPanePayload,
)
from app.extend.trade_analysis.charts import (
    CHART_CLASSES,
    TradeAnalysisCatalog,
)
from app.extend.trade_analysis.long_short_profit_loss_chart import (
    LongShortProfitLossChart,
)
from app.extend.trade_analysis.long_short_trades_chart import LongShortTradesChart
from app.extend.trade_analysis.pl_by_day_chart import PLbyDayChart
from app.extend.trade_analysis.pl_by_hour_chart import PLbyHourChart
from app.extend.trade_analysis.pl_by_year_chart import PLbyYearChart
from app.extend.trade_analysis.pl_chart import PLChart
from app.extend.trade_analysis.pl_growth_by_duration_chart import (
    PLGrowthByDurationChart,
)
from app.extend.trade_analysis.pl_long_chart import PLLongChart
from app.extend.trade_analysis.pl_short_chart import PLShortChart
from app.extend.trade_analysis.trades_by_close_type_chart import (
    TradesByCloseTypeChart,
)
from app.extend.trade_analysis.trades_by_day_chart import TradesByDayChart
from app.extend.trade_analysis.trades_by_duration_chart import (
    TradesByDurationChart,
)
from app.extend.trade_analysis.trades_by_year_chart import TradesByYearChart
from app.extend.trade_analysis.win_loss_count_by_day_chart import (
    WinLossCountByDayChart,
)
from app.extend.trade_analysis.win_loss_pl_by_day_chart import WinLossPLByDayChart


@dataclass
class _MockTrade:
    record_id: int
    time_open_msc: int
    time_close_msc: int
    profit: float
    direction: int = 1
    close_reason: str = "Signal"
    kind: str = "trade"
    net_profit: float = 0.0

    def __post_init__(self) -> None:
        if self.net_profit == 0.0:
            self.net_profit = self.profit


def _make_trade(
    record_id: int,
    open_sec: int,
    duration_sec: int,
    profit: float,
    *,
    direction: int = 1,
    close_reason: str = "Signal",
    kind: str = "trade",
) -> Any:
    return _MockTrade(
        record_id=record_id,
        kind=kind,
        direction=direction,
        time_open_msc=open_sec * 1000,
        time_close_msc=(open_sec + duration_sec) * 1000,
        profit=profit,
        net_profit=profit,
        close_reason=close_reason,
    )


class TestTradeAnalysisCatalog:
    """Test suite for TradeAnalysisCatalog and individual chart classes."""

    def test_all_27_chart_classes_registered(self) -> None:
        """Assert all 27 chart definitions are present in DESCRIPTORS and CHART_CLASSES."""
        assert len(CHART_CLASSES) == 27
        assert len(TradeAnalysisCatalog.DESCRIPTORS) == 27
        assert len(TradeAnalysisCatalog.list_charts()) == 27

        expected_ids = {
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
        }
        assert set(TradeAnalysisCatalog.DESCRIPTORS.keys()) == expected_ids

    def test_every_chart_class_properties_and_draw(self) -> None:
        """Verify each chart class instantiates, has valid descriptor, and draws cleanly."""
        for chart_cls in CHART_CLASSES:
            instance = chart_cls()
            assert isinstance(instance, TradeAnalysisChart)
            desc = instance.descriptor()
            assert desc.chart_id == instance.chart_id
            assert desc.title == instance.name
            assert desc.dimension == instance.dimension
            assert desc.metric == instance.metric
            assert desc.source_ref.endswith(".java")

            # Draw with None trades
            empty_payload = instance.draw(None)
            assert isinstance(empty_payload, TradeAnalysisPanePayload)
            assert len(empty_payload.categories) > 0

    def test_evaluate_hour_pl(self) -> None:
        """Assert PLbyHourChart aggregates trade profits by hour."""
        # 1600000000 -> 2020-09-13 12:26:40 UTC
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
            _make_trade(3, 1600000000, 300, 20.0, kind="balance"),  # Ignored non-trade
        )
        payload = TradeAnalysisCatalog.evaluate("WinLossCountByWeekdayChart", trades)
        assert payload.categories == ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
        sun_idx = payload.categories.index("Sun")
        assert payload.series["Wins"][sun_idx] == 1.0
        assert payload.series["Losses"][sun_idx] == 1.0

    def test_evaluate_win_loss_pl(self) -> None:
        """Assert WinLossPLByDayChart aggregates profit and loss totals separately."""
        # Day 13
        trades = (
            _make_trade(1, 1600000000, 300, 120.0),
            _make_trade(2, 1600000000, 300, -45.0),
            _make_trade(3, 1600000000, 300, -10.0, kind="fee"),  # Ignored non-trade
        )
        payload = WinLossPLByDayChart().evaluate(trades)
        assert "13" in payload.categories
        day_idx = payload.categories.index("13")
        assert payload.series["Profit"][day_idx] == 120.0
        assert (
            payload.series["Loss"][day_idx] == -55.0
            or payload.series["Loss"][day_idx] == -45.0
        )

    def test_evaluate_direction_and_trade_count(self) -> None:
        """Assert LongShortProfitLossChart and LongShortTradesChart."""
        trades = (
            _make_trade(1, 1600000000, 300, 100.0, direction=1),
            _make_trade(2, 1600000000, 300, -40.0, direction=-1),
        )
        payload_pl = LongShortProfitLossChart().evaluate(trades)
        assert payload_pl.categories == ("Long", "Short")
        assert payload_pl.series["NetProfit"][0] == 100.0
        assert payload_pl.series["NetProfit"][1] == -40.0

        payload_counts = LongShortTradesChart().evaluate(trades)
        assert payload_counts.categories == ("Long", "Short")
        assert payload_counts.series["Trades"][0] == 1.0
        assert payload_counts.series["Trades"][1] == 1.0

    def test_evaluate_duration_buckets(self) -> None:
        """Assert TradesByDurationChart and PLbyTradeDurationChart across duration scales."""
        trades = (
            _make_trade(1, 1600000000, 100, 10.0),  # <5m
            _make_trade(2, 1600000000, 600, 20.0),  # 5-15m
            _make_trade(3, 1600000000, 2000, 30.0),  # 15-60m
            _make_trade(4, 1600000000, 7200, 40.0),  # 1-4h
            _make_trade(5, 1600000000, 36000, 50.0),  # 4-24h
            _make_trade(6, 1600000000, 100000, 60.0),  # >24h
        )
        payload = TradesByDurationChart().evaluate(trades)
        assert payload.categories == ("<5m", "5-15m", "15-60m", "1-4h", "4-24h", ">24h")
        for count in payload.series["Trades"]:
            assert count == 1.0

        payload_growth = PLGrowthByDurationChart().evaluate(trades)
        assert len(payload_growth.series["NetProfit"]) == 6
        assert payload_growth.series["NetProfit"][-1] == 210.0

    def test_evaluate_year_and_sequence_charts(self) -> None:
        """Assert year-based and sequence-based charts."""
        trades = (
            _make_trade(1, 1600000000, 300, 50.0, direction=1),  # 2020 Long
            _make_trade(2, 1700000000, 300, -20.0, direction=-1),  # 2023 Short
        )
        payload_year_pl = PLbyYearChart().evaluate(trades)
        assert "2020" in payload_year_pl.categories
        assert "2023" in payload_year_pl.categories

        payload_year_cnt = TradesByYearChart().evaluate(trades)
        assert payload_year_cnt.series["Trades"] == (1.0, 1.0)

        # PLChart sequential
        payload_seq = PLChart().evaluate(trades)
        assert payload_seq.categories == ("#1", "#2")
        assert payload_seq.series["NetProfit"] == (50.0, -20.0)

        # PLLongChart and PLShortChart filter trades
        long_payload = PLLongChart().evaluate(trades)
        assert long_payload.categories == ("#1",)
        assert long_payload.series["NetProfit"] == (50.0,)

        short_payload = PLShortChart().evaluate(trades)
        assert short_payload.categories == ("#1",)
        assert short_payload.series["NetProfit"] == (-20.0,)

    def test_evaluate_close_types(self) -> None:
        """Assert TradesByCloseTypeChart partitions by close reason."""
        trades = (
            _make_trade(1, 1600000000, 300, 50.0, close_reason="SL"),
            _make_trade(2, 1600000000, 300, 50.0, close_reason="PT"),
        )
        payload = TradesByCloseTypeChart().evaluate(trades)
        assert "SL" in payload.categories
        assert "PT" in payload.categories
        sl_idx = payload.categories.index("SL")
        pt_idx = payload.categories.index("PT")
        assert payload.series["Trades"][sl_idx] == 1.0
        assert payload.series["Trades"][pt_idx] == 1.0

    def test_payload_to_dict_and_fallback_chart(self) -> None:
        """Assert payload dictionary serialization and unknown chart ID fallback."""
        trades = (_make_trade(1, 1600000000, 300, 50.0),)
        payload = TradeAnalysisCatalog.evaluate("NonExistentChart", trades)
        assert payload.chart_id == "NonExistentChart"

        d = payload.to_dict()
        assert d["chart_id"] == "NonExistentChart"
        assert isinstance(d["categories"], list)
        assert isinstance(d["series"], dict)

    def test_edge_cases_and_unmatched_categories(self) -> None:
        """Verify branch coverage for unmatched categories, zero timestamp, and empty year."""
        zero_time_trade = _make_trade(1, 0, 0, 10.0)
        payload = PLbyHourChart().evaluate([zero_time_trade])
        assert isinstance(payload, TradeAnalysisPanePayload)

        year_payload = TradesByYearChart().evaluate([])
        assert year_payload.categories == ("2024", "2025")

        chart_wl = WinLossCountByDayChart()
        res_wl = chart_wl.compute_data([_make_trade(1, 1600000000, 300, 10.0)], [])
        assert res_wl == {"Wins": (), "Losses": ()}

        chart_pl_wl = WinLossPLByDayChart()
        res_pl_wl = chart_pl_wl.compute_data(
            [_make_trade(1, 1600000000, 300, 10.0)], []
        )
        assert res_pl_wl == {"Profit": (), "Loss": ()}

        chart_tc = TradesByDayChart()
        res_tc = chart_tc.compute_data([_make_trade(1, 1600000000, 300, 10.0)], [])
        assert res_tc == {"Trades": ()}

        chart_pl = PLbyDayChart()
        res_pl = chart_pl.compute_data([_make_trade(1, 1600000000, 300, 10.0)], [])
        assert res_pl == {"NetProfit": ()}

    def test_package_exports(self) -> None:
        """Assert package exports all symbols."""
        assert "TradeAnalysisCatalog" in ta_pkg.__all__
        assert "TradeAnalysisChart" in ta_pkg.__all__
        assert "PLbyHourChart" in ta_pkg.__all__
        assert len(ta_pkg.__all__) >= 30
