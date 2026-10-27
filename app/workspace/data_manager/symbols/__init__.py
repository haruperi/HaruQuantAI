"""Data Manager symbols catalog service package.

Description:
    Provides symbol / instrument definitions and specifications for the Data Manager
    workspace, reading catalog entries from and mutating the SQLite database
    (datamgr_symbols table). Exposes symbol specifications, lot sizes,
    trading hours, swap rates, margin rules, and commissions with full CRUD,
    cloning, and CSV import/export capabilities.
"""

from __future__ import annotations

from app.workspace.brokers.metatrader import create_mt5_client
from app.workspace.data_manager.cli_formatters import (
    SymbolsCLI,
    format_symbol_table,
)

from ._cli import (
    register_symbol_commands,
    run_symbol_command,
)
from ._helpers import (
    _MT5_UPDATE_LOCK,
    CSV_COLUMNS,
    CSV_FIELDNAMES,
    SymbolInfo,
    SymbolMargin,
    SymbolPrice,
    SymbolSessionWindow,
    SymbolSpread,
    SymbolState,
    SymbolSwap,
    SymbolTrade,
    SymbolVolume,
    persistence,
)
from .feature import Symbols
from .http import (
    register_symbol_routes,
    symbol_to_ui,
    symbol_updates,
)

__all__ = [
    "CSV_COLUMNS",
    "CSV_FIELDNAMES",
    "_MT5_UPDATE_LOCK",
    "SymbolInfo",
    "SymbolMargin",
    "SymbolPrice",
    "SymbolSessionWindow",
    "SymbolSpread",
    "SymbolState",
    "SymbolSwap",
    "SymbolTrade",
    "SymbolVolume",
    "Symbols",
    "SymbolsCLI",
    "create_mt5_client",
    "format_symbol_table",
    "persistence",
    "register_symbol_commands",
    "register_symbol_routes",
    "run_symbol_command",
    "symbol_to_ui",
    "symbol_updates",
]
