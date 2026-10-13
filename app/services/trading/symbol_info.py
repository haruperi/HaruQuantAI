# ruff: noqa: N802 -- public names preserve the eight-class compatibility API.
"""Shared SymbolInfo proxy for native and simulated broker operations.

Description:
    Forwards asynchronous symbol snapshot queries, symbol selection, market watch
    state, price normalization, and market depth subscriptions through TradingClass.
    Symbol property reads are consolidated into a single atomic SymbolInfo() call
    returning a strongly typed SymbolSnapshot dataclass to eliminate IPC latency
    and quote temporal skew.

Purpose:
    FEAT-BROKER-PROXIES: Expose explicit asynchronous broker class operations
    without duplicating transport or persistence ownership.

Key Capabilities:
    - FR-BROKER-PROXIES-SYMBOLINFO-SNAPSHOT: Query full symbol specification
      and quote snapshot.
      Associated: `SymbolInfo.SymbolInfo()`, `SymbolInfo.__call__()`,
        `SymbolInfo.as_dict()`
      Logging: DEBUG transport invocation metadata emitted via TradingClass;
        no secret or payload logging occurs here.
    - FR-BROKER-PROXIES-SYMBOLINFO-OPERATIONS: Manage symbol binding, market watch
      selection, price normalization, and order books.
      Associated: `SymbolInfo.Name()`, `SymbolInfo.Select()`, `SymbolInfo.Refresh()`,
        `SymbolInfo.RefreshRates()`, `SymbolInfo.IsSynchronized()`,
        `SymbolInfo.NormalizePrice()`, `SymbolInfo.SymbolsTotal()`,
        `SymbolInfo.SymbolsGet()`, `SymbolInfo.SymbolInfoTick()`,
        `SymbolInfo.SymbolSelect()`, `SymbolInfo.MarketBookAdd()`,
        `SymbolInfo.MarketBookGet()`, `SymbolInfo.MarketBookRelease()`
      Logging: DEBUG transport invocation metadata emitted via TradingClass._call().

Python API Usage:
    ```python
    from app.services.trading import Trading

    async with Trading(backend) as trading:
        await trading.symbol.Name("EURUSD")
        info = await trading.symbol.SymbolInfo()
        print(f"Bid: {info.bid}, Ask: {info.ask}, Digits: {info.digits}")
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_metatrader_bridge_protocol.py --no-cov
    ```
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.services.brokers.contracts import BookInfo, BookType, SymbolSnapshot

from .base import TradingClass


class SymbolInfo(TradingClass):
    """Canonical asynchronous SymbolInfo API."""

    CLASS_NAME = "SymbolInfo"

    async def SymbolInfo(self, *args: Any) -> SymbolSnapshot:
        """Await the backend SymbolInfo snapshot."""
        data = await self._call("SymbolInfo", *args)
        if isinstance(data, SymbolSnapshot):
            return data
        if isinstance(data, dict):
            return SymbolSnapshot(**data)
        raise TypeError(f"unexpected symbol snapshot type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> SymbolSnapshot:
        """Await the backend SymbolInfo snapshot directly via call syntax."""
        return await self.SymbolInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend symbol snapshot represented as a dictionary."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, SymbolSnapshot):
            return asdict(data)
        raise TypeError(f"unexpected symbol dictionary type: {type(data).__name__}")

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

    async def MarketBookGet(self, *args: Any) -> tuple[BookInfo, ...]:
        """Return a tuple of BookInfo featuring Market Depth entries for a symbol."""
        raw = await self._call("MarketBookGet", *args)
        if not raw:
            return ()
        entries: list[BookInfo] = []
        for item in raw:
            if isinstance(item, BookInfo):
                entries.append(item)
            elif isinstance(item, dict):
                entries.append(
                    BookInfo(
                        type=BookType(int(item.get("type", BookType.BOOK_TYPE_BUY))),
                        price=float(item.get("price", 0.0)),
                        volume=int(item.get("volume", 0)),
                        volume_real=float(
                            item.get("volume_real", item.get("volume", 0.0))
                        ),
                    )
                )
        return tuple(entries)

    async def MarketBookRelease(self, *args: Any) -> Any:
        """Cancel subscription of terminal to Market Depth change events."""
        return await self._call("MarketBookRelease", *args)
