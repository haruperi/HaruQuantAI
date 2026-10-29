"""Data domain contracts, market storage, and catalog subsystem."""

from __future__ import annotations

from app.core.data.catalog import DataBatch, DataCatalog, DatasetRef
from app.core.data.contracts import (
    AccountInfo,
    ChartDef,
    DataInfo,
    DealInfo,
    MarketBar,
    MarketTick,
    OrderInfo,
    PositionInfo,
    SymbolInfo,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
    TradingBackend,
    TradingSession,
)
from app.core.data.io import DataIO
from app.core.data.market_storage import (
    M1_SCHEMA,
    TICK_SCHEMA,
    catalog_paths,
    encode_frame,
    price_columns,
    safe_component,
    scan_catalog,
)

__all__ = [
    "M1_SCHEMA",
    "TICK_SCHEMA",
    "AccountInfo",
    "ChartDef",
    "DataBatch",
    "DataCatalog",
    "DataIO",
    "DataInfo",
    "DatasetRef",
    "DealInfo",
    "MarketBar",
    "MarketTick",
    "OrderInfo",
    "PositionInfo",
    "SymbolInfo",
    "TradeCheckResult",
    "TradeRequest",
    "TradeResult",
    "TradingBackend",
    "TradingSession",
    "catalog_paths",
    "encode_frame",
    "price_columns",
    "safe_component",
    "scan_catalog",
]
