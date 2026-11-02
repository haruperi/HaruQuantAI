"""PLbyWeekdayChart trade analysis chart snippet.

Description:
    Aggregates realized trade profit/loss by day of week.
    Matches StrategyQuant SQ.TradeAnalysis.PLbyWeekdayChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-pl-by-weekday:
      Aggregates realized trade profit/loss by day of week.

Python API Usage:
    from app.extend.trade_analysis.pl_by_weekday_chart import (
        PLbyWeekdayChart,
    )
    chart = PLbyWeekdayChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart PLbyWeekdayChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class PLbyWeekdayChart(TradeAnalysisChart):
    """Profit/Loss by Weekday chart matching StrategyQuant PLbyWeekdayChart."""

    name: str = "Profit/Loss by Weekday"
    chart_id: str = "PLbyWeekdayChart"
    dimension: DimensionType = "WEEKDAY"
    metric: MetricType = "PL"
    source_ref: str = "PLbyWeekdayChart.java"
