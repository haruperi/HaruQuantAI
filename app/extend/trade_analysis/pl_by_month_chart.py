"""PLbyMonthChart trade analysis chart snippet.

Description:
    Aggregates realized trade profit/loss across calendar months.
    Matches StrategyQuant SQ.TradeAnalysis.PLbyMonthChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-pl-by-month:
      Aggregates realized trade profit/loss across calendar months.

Python API Usage:
    from app.extend.trade_analysis.pl_by_month_chart import (
        PLbyMonthChart,
    )
    chart = PLbyMonthChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart PLbyMonthChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class PLbyMonthChart(TradeAnalysisChart):
    """Profit/Loss by Month chart matching StrategyQuant PLbyMonthChart."""

    name: str = "Profit/Loss by Month"
    chart_id: str = "PLbyMonthChart"
    dimension: DimensionType = "MONTH"
    metric: MetricType = "PL"
    source_ref: str = "PLbyMonthChart.java"
