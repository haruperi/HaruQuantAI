"""Shared symbol information, quotes, and market depth."""

# ruff: noqa: N802 -- MQL5 PascalCase API compatibility
from __future__ import annotations

from typing import Any

from app.core.host.logging import get_logger
from app.include import contracts
from app.include.enums import (
    BookType,
)

from .base import TradingClass

logger = get_logger(__name__)


class SymbolProxy(TradingClass):
    """Canonical asynchronous SymbolInfo API proxy."""

    CLASS_NAME = "SymbolInfo"

    async def SymbolInfo(self, *args: Any) -> contracts.SymbolInfo:
        """Await the backend SymbolInfo snapshot."""
        logger.debug("FR-TRADING-SYMBOL-SNAPSHOT: querying symbol snapshot")
        return await self._snapshot(
            "SymbolInfo", contracts.SymbolInfo, "symbol info", *args
        )

    async def __call__(self, *args: Any) -> contracts.SymbolInfo:
        """Await the backend SymbolInfo snapshot directly via call syntax."""
        return await self.SymbolInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend symbol snapshot represented as a dictionary."""
        return await self._snapshot_dict(contracts.SymbolInfo, "symbol", *args)

    async def Refresh(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Refresh operation."""
        return await self._call("Refresh", *args)

    async def RefreshRates(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.RefreshRates operation."""
        return await self._call("RefreshRates", *args)

    async def Name(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Name operation."""
        return await self._call("Name", *args)

    async def Select(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Select operation."""
        return await self._call("Select", *args)

    async def IsSynchronized(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.IsSynchronized operation."""
        return await self._call("IsSynchronized", *args)

    async def NormalizePrice(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.NormalizePrice operation."""
        return await self._call("NormalizePrice", *args)

    async def SymbolsTotal(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SymbolsTotal operation."""
        return await self._call("SymbolsTotal", *args)

    async def SymbolsGet(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SymbolsGet operation."""
        return await self._call("SymbolsGet", *args)

    async def SymbolInfoTick(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SymbolInfoTick operation."""
        return await self._call("SymbolInfoTick", *args)

    async def SymbolSelect(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SymbolSelect operation."""
        return await self._call("SymbolSelect", *args)

    async def MarketBookAdd(self, *args: Any) -> Any:
        """Subscribes the MetaTrader 5 terminal to Market Depth change events."""
        return await self._call("MarketBookAdd", *args)

    async def MarketBookGet(self, *args: Any) -> tuple[contracts.BookInfo, ...]:
        """Return a tuple of BookInfo featuring Market Depth entries for a symbol."""
        logger.debug("FR-TRADING-SYMBOL-SNAPSHOT: reading market depth")
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
        return await self._call("MarketBookRelease", *args)
