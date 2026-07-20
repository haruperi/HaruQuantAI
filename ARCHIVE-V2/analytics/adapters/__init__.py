"""Analytics result and journal adapters package.

This package exposes tools, protocols, converters, and decorators to translate
various format execution structures to canonical TradingResult models.
"""

from __future__ import annotations

from typing import Any

from app.services.analytics.adapters.canonicalize import (
    LiveResult,
    PaperResult,
    PortfolioResult,
    TradingResultAdapter,
    to_canonical,
    to_trading_result,
)
from app.services.analytics.adapters.journal_adapters import (
    LiveTradeJournal,
    SimulationJournal,
    from_live_trade_journal,
    from_simulation_journal,
)
from app.services.analytics.adapters.protocols import (
    BacktestResultDict,
    LiveTradingResultDict,
    PaperTradingResultDict,
    TradingResultDict,
    validate_adapter_contract,
)

# Compatibility backward-compatible aliases
TradingResult = dict[str, Any]
BacktestResult = dict[str, Any]
PaperTradingResult = dict[str, Any]
LiveTradingResult = dict[str, Any]

__all__ = [
    "BacktestResult",
    "BacktestResultDict",
    "LiveResult",
    "LiveTradeJournal",
    "LiveTradingResult",
    "LiveTradingResultDict",
    "PaperResult",
    "PaperTradingResult",
    "PaperTradingResultDict",
    "PortfolioResult",
    "SimulationJournal",
    "TradingResult",
    "TradingResultAdapter",
    "TradingResultDict",
    "from_live_trade_journal",
    "from_simulation_journal",
    "to_canonical",
    "to_trading_result",
    "validate_adapter_contract",
]
