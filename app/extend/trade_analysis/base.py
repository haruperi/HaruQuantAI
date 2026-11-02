"""Base class and common types for Trade Analysis charts.

Description:
    Provides TradeAnalysisChart base class matching StrategyQuant's
    com.strategyquant.tradinglib.TradeAnalysisChart, supporting temporal,
    duration, direction, sequence, and exit reason aggregation dimensions.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-base: Chart contract and data bucket aggregators.

Python API Usage:
    from app.extend.trade_analysis.base import TradeAnalysisChart

    class MyChart(TradeAnalysisChart):
        name = "My Custom Chart"
        chart_id = "MyChart"
        dimension = "HOUR"
        metric = "PL"

CLI Usage:
    python -m app.cli retest trade-analysis --chart MyChart
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.extend.what_if.base import WhatIfRecord

logger = get_logger(__name__)

DimensionType = Literal[
    "HOUR",
    "WEEKDAY",
    "DAY",
    "MONTH",
    "YEAR",
    "DURATION",
    "CLOSE_TYPE",
    "DIRECTION",
    "SEQUENCE",
]

MetricType = Literal["PL", "TRADE_COUNT", "WIN_LOSS_COUNT", "WIN_LOSS_PL"]

HOURS = [f"{h:02d}:00" for h in range(24)]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
DAYS_OF_MONTH = [str(d) for d in range(1, 32)]
DURATION_BUCKETS = ["<5m", "5-15m", "15-60m", "1-4h", "4-24h", ">24h"]
CLOSE_TYPES = [
    "SL",
    "PT",
    "Signal",
    "TrailingStop",
    "ExitAfterBars",
    "EndOfDay",
    "Other",
]
DIRECTIONS = ["Long", "Short"]

DURATION_5M_SEC = 300
DURATION_15M_SEC = 900
DURATION_1H_SEC = 3600
DURATION_4H_SEC = 14400
DURATION_24H_SEC = 86400


@dataclass(frozen=True, slots=True)
class TradeAnalysisChartDescriptor:
    """Descriptor defining dimensions and metrics for a trade analysis chart."""

    chart_id: str
    title: str
    dimension: DimensionType
    metric: MetricType
    source_ref: str


@dataclass(frozen=True, slots=True)
class TradeAnalysisPanePayload:
    """Aggregated chart categories and data series payload."""

    chart_id: str
    title: str
    dimension: str
    metric: str
    categories: tuple[str, ...]
    series: dict[str, tuple[float, ...]]

    def to_dict(self) -> dict[str, Any]:
        """Convert payload to dictionary."""
        return {
            "chart_id": self.chart_id,
            "title": self.title,
            "dimension": self.dimension,
            "metric": self.metric,
            "categories": list(self.categories),
            "series": {k: list(v) for k, v in self.series.items()},
        }


@dataclass(frozen=True, slots=True)
class TradeAnalysisChart:
    """Base class for all 27 StrategyQuant-compatible trade analysis charts."""

    name: str = "?"
    chart_id: str = "TradeAnalysisChart"
    dimension: DimensionType = "SEQUENCE"
    metric: MetricType = "PL"
    source_ref: str = "TradeAnalysisChart.java"

    def descriptor(self) -> TradeAnalysisChartDescriptor:
        """Return the metadata descriptor for this chart."""
        return TradeAnalysisChartDescriptor(
            chart_id=self.chart_id,
            title=self.name,
            dimension=self.dimension,
            metric=self.metric,
            source_ref=self.source_ref,
        )

    def draw(
        self,
        trades: Sequence[WhatIfRecord | Any] | None = None,
        _pl_type: int = 0,
        _trade_period: int = 0,
    ) -> TradeAnalysisPanePayload:
        """Donor Java draw method contract."""
        return self.evaluate(trades or ())

    def evaluate(
        self,
        trades: Sequence[WhatIfRecord | Any],
    ) -> TradeAnalysisPanePayload:
        """Evaluate trade analysis chart on trade records sequence."""
        filtered_trades = self._filter_trades(trades)
        categories = self._resolve_categories(filtered_trades)
        series = self.compute_data(filtered_trades, categories)

        logger.debug(
            "FR-trade-analysis-base: evaluated %s (%d categories)",
            self.chart_id,
            len(categories),
        )

        return TradeAnalysisPanePayload(
            chart_id=self.chart_id,
            title=self.name,
            dimension=self.dimension,
            metric=self.metric,
            categories=tuple(categories),
            series=series,
        )

    def compute_data(
        self,
        trades: Sequence[WhatIfRecord | Any],
        categories: list[str],
    ) -> dict[str, tuple[float, ...]]:
        """Compute series data values for the chart."""
        cat_indices = {cat: i for i, cat in enumerate(categories)}
        num_cats = len(categories)

        if self.metric == "WIN_LOSS_COUNT":
            return self._calculate_win_loss_count(trades, cat_indices, num_cats)
        if self.metric == "WIN_LOSS_PL":
            return self._calculate_win_loss_pl(trades, cat_indices, num_cats)
        if self.metric == "TRADE_COUNT":
            return self._calculate_trade_count(trades, cat_indices, num_cats)
        return self._calculate_pl(trades, cat_indices, num_cats)

    def _filter_trades(
        self, trades: Sequence[WhatIfRecord | Any]
    ) -> Sequence[WhatIfRecord | Any]:
        """Filter trades for direction-specific charts."""
        if self.chart_id == "PLLongChart":
            return [t for t in trades if getattr(t, "direction", 1) == 1]
        if self.chart_id == "PLShortChart":
            return [t for t in trades if getattr(t, "direction", 1) == -1]
        return trades

    def _resolve_categories(
        self,
        trades: Sequence[WhatIfRecord | Any],
    ) -> list[str]:
        """Resolve categorical x-axis labels."""
        dimension_map: dict[str, Sequence[str]] = {
            "HOUR": HOURS,
            "WEEKDAY": WEEKDAYS,
            "MONTH": MONTHS,
            "DAY": DAYS_OF_MONTH,
            "DURATION": DURATION_BUCKETS,
            "CLOSE_TYPE": CLOSE_TYPES,
            "DIRECTION": DIRECTIONS,
        }
        if self.dimension in dimension_map:
            return list(dimension_map[self.dimension])
        if self.dimension == "YEAR":
            return sorted(
                {
                    str(datetime.fromtimestamp(t.time_open_msc / 1000, tz=UTC).year)
                    for t in trades
                    if hasattr(t, "time_open_msc") and t.time_open_msc > 0
                }
            ) or ["2024", "2025"]
        return [f"#{i + 1}" for i in range(len(trades))] or ["#1"]

    def _resolve_category(self, trade: Any) -> str:
        open_msc = getattr(trade, "time_open_msc", 0)
        close_msc = getattr(trade, "time_close_msc", open_msc)
        dt = (
            datetime.fromtimestamp(open_msc / 1000, tz=UTC)
            if open_msc > 0
            else datetime.now(tz=UTC)
        )

        mapping: dict[DimensionType, str] = {
            "HOUR": f"{dt.hour:02d}:00",
            "WEEKDAY": WEEKDAYS[dt.weekday()],
            "MONTH": MONTHS[dt.month - 1],
            "DAY": str(dt.day),
            "YEAR": str(dt.year),
            "DURATION": self._get_duration_bucket(
                max(0.0, (close_msc - open_msc) / 1000.0)
            ),
            "CLOSE_TYPE": str(getattr(trade, "close_reason", "Signal") or "Signal"),
            "DIRECTION": "Long" if getattr(trade, "direction", 1) == 1 else "Short",
        }
        return mapping.get(self.dimension, "#1")

    @staticmethod
    def _get_duration_bucket(duration_sec: float) -> str:
        if duration_sec < DURATION_5M_SEC:
            return "<5m"
        if duration_sec < DURATION_15M_SEC:
            return "5-15m"
        if duration_sec < DURATION_1H_SEC:
            return "15-60m"
        if duration_sec < DURATION_4H_SEC:
            return "1-4h"
        if duration_sec < DURATION_24H_SEC:
            return "4-24h"
        return ">24h"

    def _calculate_win_loss_count(
        self,
        trades: Sequence[WhatIfRecord | Any],
        cat_indices: dict[str, int],
        num_cats: int,
    ) -> dict[str, tuple[float, ...]]:
        win_counts = [0.0] * num_cats
        loss_counts = [0.0] * num_cats
        for t in trades:
            if getattr(t, "kind", "trade") != "trade":
                continue
            p = getattr(t, "net_profit", getattr(t, "profit", 0.0))
            idx = cat_indices.get(self._resolve_category(t))
            if idx is not None:
                if p >= 0:
                    win_counts[idx] += 1.0
                else:
                    loss_counts[idx] += 1.0
        return {"Wins": tuple(win_counts), "Losses": tuple(loss_counts)}

    def _calculate_win_loss_pl(
        self,
        trades: Sequence[WhatIfRecord | Any],
        cat_indices: dict[str, int],
        num_cats: int,
    ) -> dict[str, tuple[float, ...]]:
        win_pl = [0.0] * num_cats
        loss_pl = [0.0] * num_cats
        for t in trades:
            if getattr(t, "kind", "trade") != "trade":
                continue
            p = getattr(t, "net_profit", getattr(t, "profit", 0.0))
            idx = cat_indices.get(self._resolve_category(t))
            if idx is not None:
                if p >= 0:
                    win_pl[idx] = round(win_pl[idx] + p, 2)
                else:
                    loss_pl[idx] = round(loss_pl[idx] + p, 2)
        return {"Profit": tuple(win_pl), "Loss": tuple(loss_pl)}

    def _calculate_trade_count(
        self,
        trades: Sequence[WhatIfRecord | Any],
        cat_indices: dict[str, int],
        num_cats: int,
    ) -> dict[str, tuple[float, ...]]:
        counts = [0.0] * num_cats
        for t in trades:
            idx = cat_indices.get(self._resolve_category(t))
            if idx is not None:
                counts[idx] += 1.0
        return {"Trades": tuple(counts)}

    def _calculate_pl(
        self,
        trades: Sequence[WhatIfRecord | Any],
        cat_indices: dict[str, int],
        num_cats: int,
    ) -> dict[str, tuple[float, ...]]:
        pl_values = [0.0] * num_cats
        cum_pl = 0.0
        is_growth = self.chart_id == "PLGrowthByDurationChart"

        for i, t in enumerate(trades):
            p = getattr(t, "net_profit", getattr(t, "profit", 0.0))
            idx = (
                i
                if self.dimension == "SEQUENCE" and i < num_cats
                else cat_indices.get(self._resolve_category(t))
            )
            if idx is not None:
                if is_growth:
                    cum_pl += p
                    pl_values[idx] = round(cum_pl, 2)
                else:
                    pl_values[idx] = round(pl_values[idx] + p, 2)
        return {"NetProfit": tuple(pl_values)}
