"""CustomAnalysis extension cohort package matching donor Snippets/SQ/CustomAnalysis.

Description:
    Exposes CustomAnalysisMethod base architecture along with donor snippet
    implementations CorrelationFilter and OutlierTrade, alongside legacy
    utility analyzers for backward compatibility.
"""

from __future__ import annotations

from app.extend.custom_analysis.analyzers import (
    CorrelationFilterAnalyzer,
    OutlierTradeAnalyzer,
    OutlierTradeReport,
    TradeRecord,
)
from app.extend.custom_analysis.base import (
    TYPE_BOTH,
    TYPE_FILTER_STRATEGY,
    TYPE_PROCESS_DATABANK,
    CustomAnalysisMethod,
    CustomAnalysisOrder,
    OrdersList,
    ResultsGroup,
)
from app.extend.custom_analysis.correlation_filter import CorrelationFilter
from app.extend.custom_analysis.outlier_trade import OutlierTrade

__all__ = [
    "TYPE_BOTH",
    "TYPE_FILTER_STRATEGY",
    "TYPE_PROCESS_DATABANK",
    "CorrelationFilter",
    "CorrelationFilterAnalyzer",
    "CustomAnalysisMethod",
    "CustomAnalysisOrder",
    "OrdersList",
    "OutlierTrade",
    "OutlierTradeAnalyzer",
    "OutlierTradeReport",
    "ResultsGroup",
    "TradeRecord",
]
