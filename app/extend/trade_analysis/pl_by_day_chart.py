"""PLbyDayChart trade analysis chart snippet.

Description:
    Aggregates realized trade profit/loss by day of month (1-31).
    Matches StrategyQuant SQ.TradeAnalysis.PLbyDayChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-pl-by-day:
      Aggregates realized trade profit/loss by day of month (1-31).

Python API Usage:
    from app.extend.trade_analysis.pl_by_day_chart import (
        PLbyDayChart,
    )
    chart = PLbyDayChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart PLbyDayChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class PLbyDayChart(TradeAnalysisChart):
    """Profit/Loss by Day of Month chart matching StrategyQuant PLbyDayChart."""

    name: str = "Profit/Loss by Day of Month"
    chart_id: str = "PLbyDayChart"
    dimension: DimensionType = "DAY"
    metric: MetricType = "PL"
    source_ref: str = "PLbyDayChart.java"
