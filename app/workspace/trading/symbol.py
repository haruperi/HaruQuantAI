"""Shared symbol information, quotes, and market depth.

Description:
    Provides asynchronous SymbolProxy for querying symbol specifications,
    real-time quotes, symbol selection, and Market Depth snapshots.
Purpose:
    FEAT-LIVE-TRADING-FACADE: Centralize live trading facade and symbol queries.
Key Capabilities:
    - FR-trading-symbol-spec: Query SymbolInfo, rates, price normalization.
    - FR-trading-symbol-depth: MarketBook subscription and order book retrieval.
Python API Usage:
    from app.workspace.trading.symbol import SymbolProxy
CLI Usage:
    uv run python -m pytest tests/workspace/trading -q
"""

# ruff: noqa: N802 -- MQL5 PascalCase API compatibility
from __future__ import annotations

from typing import Any

from app.core.data import contracts
from app.core.enums import BookType
from app.core.host.logging import get_logger

from .base import TradingClass

logger = get_logger(__name__)


class SymbolProxy(TradingClass):
    """Canonical asynchronous SymbolInfo API proxy."""

    CLASS_NAME = "SymbolInfo"

    async def SymbolInfo(self, *args: Any) -> contracts.SymbolInfo:
        """Await the backend SymbolInfo snapshot."""
        logger.debug("FR-trading-symbol-spec: querying symbol snapshot")
        return await self._snapshot(
            "SymbolInfo", contracts.SymbolInfo, "symbol info", *args
        )

    async def __call__(self, *args: Any) -> contracts.SymbolInfo:
        """Await the backend SymbolInfo snapshot directly via call syntax."""
        return await self.SymbolInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend symbol snapshot represented as a dictionary."""
        logger.debug("FR-trading-symbol-spec: querying symbol as dict")
        return await self._snapshot_dict(contracts.SymbolInfo, "symbol", *args)

    async def Refresh(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Refresh operation."""
        logger.debug("FR-trading-symbol-spec: refreshing symbol")
        return await self._call("Refresh", *args)

    async def RefreshRates(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.RefreshRates operation."""
        logger.debug("FR-trading-symbol-spec: refreshing rates")
        return await self._call("RefreshRates", *args)

    async def Name(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Name operation."""
        logger.debug("FR-trading-symbol-spec: fetching symbol name")
        return await self._call("Name", *args)

    async def Select(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Select operation."""
        logger.debug("FR-trading-symbol-spec: selecting symbol")
        return await self._call("Select", *args)

    async def IsSynchronized(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.IsSynchronized operation."""
        logger.debug("FR-trading-symbol-spec: checking symbol synchronization")
        return await self._call("IsSynchronized", *args)

    async def NormalizePrice(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.NormalizePrice operation."""
        logger.debug("FR-trading-symbol-spec: normalizing price")
        return await self._call("NormalizePrice", *args)

    async def SymbolsTotal(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SymbolsTotal operation."""
        logger.debug("FR-trading-symbol-spec: querying symbols total")
        return await self._call("SymbolsTotal", *args)

    async def SymbolsGet(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SymbolsGet operation."""
        logger.debug("FR-trading-symbol-spec: querying symbols collection")
        return await self._call("SymbolsGet", *args)

    async def SymbolInfoTick(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SymbolInfoTick operation."""
        logger.debug("FR-trading-symbol-spec: querying symbol tick")
        return await self._call("SymbolInfoTick", *args)

    async def SymbolSelect(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SymbolSelect operation."""
        logger.debug("FR-trading-symbol-spec: selecting symbol")
        return await self._call("SymbolSelect", *args)

    async def MarketBookAdd(self, *args: Any) -> Any:
        """Subscribes the MetaTrader 5 terminal to Market Depth change events."""
        logger.debug("FR-trading-symbol-depth: subscribing market book")
        return await self._call("MarketBookAdd", *args)

    async def MarketBookGet(self, *args: Any) -> tuple[contracts.BookInfo, ...]:
        """Return a tuple of BookInfo featuring Market Depth entries for a symbol."""
        logger.debug("FR-trading-symbol-depth: reading market depth")
        raw = await self._call("MarketBookGet", *args)
        if not raw:
            return ()
        entries: list[contracts.BookInfo] = []
        for item in raw:
            if isinstance(item, contracts.BookInfo):
                entries.append(item)
            elif isinstance(item, dict):
                raw_vol = item.get("volume_real")
                if raw_vol is None:
                    raw_vol = item.get("volume", 0.0)
                entries.append(
                    contracts.BookInfo(
                        type=BookType(int(item.get("type", BookType.BOOK_TYPE_BUY))),
                        price=float(item.get("price", 0.0)),
                        volume=int(item.get("volume", 0)),
                        volume_real=float(raw_vol if raw_vol is not None else 0.0),
                    )
                )
        return tuple(entries)

    async def MarketBookRelease(self, *args: Any) -> Any:
        """Cancel subscription of terminal to Market Depth change events."""
        logger.debug("FR-trading-symbol-depth: releasing market book")
        return await self._call("MarketBookRelease", *args)
