"""Trade analysis charts extension package.

Description:
    Provides StrategyQuant-compatible trade analysis charts for post-backtest
    visual analytics across temporal, duration, direction, sequence, and exit
    reason dimensions matching SQ.TradeAnalysis snippets.

Purpose:
    FEAT-RETESTER-TRADE-ANALYSIS: Post-backtest trade pattern visual analytics.

Key Capabilities:
    - FR-trade-analysis-base: Base trade analysis chart contracts.
    - FR-trade-analysis-catalog: Registry and evaluation of all 27 charts.

Python API Usage:
    from app.extend.trade_analysis import (
        TradeAnalysisCatalog,
        PLbyHourChart,
        LongShortProfitLossChart,
    )

CLI Usage:
    python -m app.cli retest trade-analysis --chart PLbyHourChart
"""

from __future__ import annotations

from app.extend.trade_analysis.base import (
    TradeAnalysisChart,
    TradeAnalysisChartDescriptor,
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
from app.extend.trade_analysis.pl_by_month_chart import PLbyMonthChart
from app.extend.trade_analysis.pl_by_trade_duration_chart import (
    PLbyTradeDurationChart,
)
from app.extend.trade_analysis.pl_by_weekday_chart import PLbyWeekdayChart
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
from app.extend.trade_analysis.trades_by_hour_chart import TradesByHourChart
from app.extend.trade_analysis.trades_by_month_chart import TradesByMonthChart
from app.extend.trade_analysis.trades_by_weekday_chart import TradesByWeekdayChart
from app.extend.trade_analysis.trades_by_year_chart import TradesByYearChart
from app.extend.trade_analysis.win_loss_count_by_day_chart import (
    WinLossCountByDayChart,
)
from app.extend.trade_analysis.win_loss_count_by_hour_chart import (
    WinLossCountByHourChart,
)
from app.extend.trade_analysis.win_loss_count_by_month_chart import (
    WinLossCountByMonthChart,
)
from app.extend.trade_analysis.win_loss_count_by_weekday_chart import (
    WinLossCountByWeekdayChart,
)
from app.extend.trade_analysis.win_loss_pl_by_day_chart import WinLossPLByDayChart
from app.extend.trade_analysis.win_loss_pl_by_hour_chart import WinLossPLByHourChart
from app.extend.trade_analysis.win_loss_pl_by_month_chart import (
    WinLossPLByMonthChart,
)
from app.extend.trade_analysis.win_loss_pl_by_weekday_chart import (
    WinLossPLByWeekdayChart,
)

__all__ = [
    "CHART_CLASSES",
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
    "TradeAnalysisCatalog",
    "TradeAnalysisChart",
    "TradeAnalysisChartDescriptor",
    "TradeAnalysisPanePayload",
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
