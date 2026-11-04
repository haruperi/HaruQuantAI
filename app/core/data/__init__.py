"""Data domain contracts, market storage, and catalog subsystem."""

from __future__ import annotations

from app.core.data.catalog import DataBatch, DataCatalog, DatasetRef
from app.core.data.charts import ChartDef
from app.core.data.contracts import (
    BookInfo,
    DataframeSeries,
    DataInfo,
    MarketBar,
    MarketTick,
    SymbolInfo,
    TradingSession,
)
from app.core.data.events import TickEvent
from app.core.data.io import DataIO
from app.core.data.series import DataSeries, TimeDataSeries
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
    "TickEvent",
    "TimeDataSeries",
    "BookInfo",
    "ChartDef",
    "DataBatch",
    "DataCatalog",
    "DataIO",
    "DataInfo",
    "DataSeries",
    "DataframeSeries",
    "DatasetRef",
    "MarketBar",
    "MarketTick",
    "SymbolInfo",
    "TradingSession",
    "catalog_paths",
    "encode_frame",
    "price_columns",
    "safe_component",
    "scan_catalog",
]
