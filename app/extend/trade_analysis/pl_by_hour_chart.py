"""PLbyHourChart trade analysis chart snippet.

Description:
    Aggregates realized trade profit/loss across hours of the day.
    Matches StrategyQuant SQ.TradeAnalysis.PLbyHourChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-pl-by-hour:
      Aggregates realized trade profit/loss across hours of the day.

Python API Usage:
    from app.extend.trade_analysis.pl_by_hour_chart import (
        PLbyHourChart,
    )
    chart = PLbyHourChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart PLbyHourChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class PLbyHourChart(TradeAnalysisChart):
    """Profit/Loss by Hour chart matching StrategyQuant PLbyHourChart."""

    name: str = "Profit/Loss by Hour"
    chart_id: str = "PLbyHourChart"
    dimension: DimensionType = "HOUR"
    metric: MetricType = "PL"
    source_ref: str = "PLbyHourChart.java"
