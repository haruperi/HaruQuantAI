"""LongShortProfitLossChart trade analysis chart snippet.

Description:
    Computes profit and loss distribution between long and short trades.
    Matches StrategyQuant SQ.TradeAnalysis.LongShortProfitLossChart snippet.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-long-short-pl:
      Computes profit and loss distribution between long and short trades.

Python API Usage:
    from app.extend.trade_analysis.long_short_profit_loss_chart import (
        LongShortProfitLossChart,
    )
    chart = LongShortProfitLossChart()
    payload = chart.evaluate(trades)

CLI Usage:
    python -m app.cli retest trade-analysis --chart LongShortProfitLossChart
"""

from __future__ import annotations

from dataclasses import dataclass

from app.extend.trade_analysis.base import DimensionType, MetricType, TradeAnalysisChart


@dataclass(frozen=True, slots=True)
class LongShortProfitLossChart(TradeAnalysisChart):
    """Long vs Short P/L chart matching StrategyQuant LongShortProfitLossChart."""

    name: str = "Long vs Short P/L"
    chart_id: str = "LongShortProfitLossChart"
    dimension: DimensionType = "DIRECTION"
    metric: MetricType = "PL"
    source_ref: str = "LongShortProfitLossChart.java"
