"""Read and query proxies for accounts, terminals, symbols, and orders.

Description:
    Provides canonical asynchronous query proxy classes matching MQL5 APIs
    (AccountInfo, TerminalInfo, SymbolInfo, PositionInfo, OrderInfo,
    HistoryOrderInfo, DealInfo), querying live and historical states through
    the TradingBackend protocol.

Purpose:
    FEAT-TRADING-PROXIES: Query proxies for trading state inspection.

Key Capabilities:
    - FR-TRADING-QUERY-PROXIES: State inspection and property resolution.
      Associated: `AccountInfo`, `TerminalInfo`, `SymbolInfo`, `PositionInfo`,
        `OrderInfo`, `HistoryOrderInfo`, `DealInfo`.
      Logging: DEBUG queries dispatched through BaseTradingClass.

Python API Usage:
    ```python
    from app.services.trading.proxies import AccountInfo, SymbolInfo

    account_info = AccountInfo(backend)
    symbol_info = SymbolInfo(backend)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.trading.proxies
    ```
"""

# ruff: noqa: N802 -- MQL5 PascalCase API compatibility
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.host.logging import get_logger

from .base import TradingClass
from .enums import BookType
from .snapshots import (
    AccountSnapshot,
    BookInfo,
    DealSnapshot,
    HistoryOrderSnapshot,
    OrderSnapshot,
    PositionSnapshot,
    SymbolSnapshot,
    TerminalSnapshot,
)

__all__ = [
    "AccountInfo",
    "DealInfo",
    "HistoryOrderInfo",
    "OrderInfo",
    "PositionInfo",
    "SymbolInfo",
    "TerminalInfo",
]

logger = get_logger(__name__)


class AccountInfo(TradingClass):
    """Canonical asynchronous AccountInfo API."""

    CLASS_NAME = "AccountInfo"

    async def AccountInfo(self, *args: Any) -> AccountSnapshot:
        """Await the backend AccountInfo snapshot."""
        logger.debug("FR-TRADING-ACCOUNT-SNAPSHOT: querying account snapshot")
        data = await self._call("AccountInfo", *args)
        if isinstance(data, AccountSnapshot):
            return data
        if isinstance(data, dict):
            return AccountSnapshot(**data)
        raise TypeError(f"unexpected account snapshot type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> AccountSnapshot:
        """Await the backend AccountInfo snapshot directly via call syntax."""
        return await self.AccountInfo(*args)

    async def OrderProfitCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.OrderProfitCheck operation."""
        return await self._call("OrderProfitCheck", *args)

    async def MarginCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.MarginCheck operation."""
        return await self._call("MarginCheck", *args)

    async def FreeMarginCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.FreeMarginCheck operation."""
        return await self._call("FreeMarginCheck", *args)

    async def MaxLotCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.MaxLotCheck operation."""
        return await self._call("MaxLotCheck", *args)


# ============================================================================
# TerminalInfo Proxy
# ============================================================================


class TerminalInfo(TradingClass):
    """Canonical asynchronous TerminalInfo API."""

    CLASS_NAME = "TerminalInfo"

    async def TerminalInfo(self, *args: Any) -> TerminalSnapshot:
        """Await the backend TerminalInfo snapshot."""
        logger.debug("FR-TRADING-TERMINAL-SNAPSHOT: querying terminal snapshot")
        data = await self._call("TerminalInfo", *args)
        if isinstance(data, TerminalSnapshot):
            return data
        if isinstance(data, dict):
            return TerminalSnapshot(**data)
        raise TypeError(f"unexpected terminal snapshot type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> TerminalSnapshot:
        """Await the backend TerminalInfo snapshot directly via call syntax."""
        return await self.TerminalInfo(*args)


# ============================================================================
# SymbolInfo Proxy
# ============================================================================


class SymbolInfo(TradingClass):
    """Canonical asynchronous SymbolInfo API."""

    CLASS_NAME = "SymbolInfo"

    async def SymbolInfo(self, *args: Any) -> SymbolSnapshot:
        """Await the backend SymbolInfo snapshot."""
        logger.debug("FR-TRADING-SYMBOL-SNAPSHOT: querying symbol snapshot")
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
        logger.debug("FR-TRADING-SYMBOL-SNAPSHOT: reading market depth")
        raw = await self._call("MarketBookGet", *args)
        if not raw:
            return ()
        entries: list[BookInfo] = []
        for item in raw:
            if isinstance(item, BookInfo):
                entries.append(item)
            elif isinstance(item, dict):
                raw_vol = item.get("volume_real")
                if raw_vol is None:
                    raw_vol = item.get("volume", 0.0)
                entries.append(
                    BookInfo(
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


# ============================================================================
# PositionInfo Proxy
# ============================================================================


class PositionInfo(TradingClass):
    """Canonical asynchronous PositionInfo API."""

    CLASS_NAME = "PositionInfo"

    async def PositionInfo(self, *args: Any) -> PositionSnapshot:
        """Await the backend PositionInfo snapshot."""
        logger.debug("FR-TRADING-POSITIONS: querying position snapshot")
        data = await self._call("PositionInfo", *args)
        if isinstance(data, PositionSnapshot):
            return data
        if isinstance(data, dict):
            return PositionSnapshot(**data)
        raise TypeError(f"unexpected position snapshot type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> PositionSnapshot:
        """Await the backend PositionInfo snapshot directly via call syntax."""
        return await self.PositionInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend position snapshot represented as a dictionary."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, PositionSnapshot):
            return asdict(data)
        raise TypeError(f"unexpected position dictionary type: {type(data).__name__}")

    async def Select(self, *args: Any) -> Any:
        """Await the backend PositionInfo.Select operation."""
        return await self._call("Select", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend PositionInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def SelectByMagic(self, *args: Any) -> Any:
        """Await the backend PositionInfo.SelectByMagic operation."""
        return await self._call("SelectByMagic", *args)

    async def SelectByTicket(self, *args: Any) -> Any:
        """Await the backend PositionInfo.SelectByTicket operation."""
        return await self._call("SelectByTicket", *args)

    async def StoreState(self, *args: Any) -> Any:
        """Await the backend PositionInfo.StoreState operation."""
        return await self._call("StoreState", *args)

    async def CheckState(self, *args: Any) -> Any:
        """Await the backend PositionInfo.CheckState operation."""
        return await self._call("CheckState", *args)

    async def PositionsTotal(self, *args: Any) -> Any:
        """Await the backend PositionInfo.PositionsTotal operation."""
        return await self._call("PositionsTotal", *args)

    async def PositionsGet(self, *args: Any, **kwargs: Any) -> list[PositionSnapshot]:
        """Await the backend PositionInfo.PositionsGet operation."""
        logger.debug("FR-TRADING-POSITIONS: querying positions collection")
        data = (
            await self._call("PositionsGet", kwargs)
            if kwargs
            else await self._call("PositionsGet", *args)
        )
        if isinstance(data, list):
            return [
                item if isinstance(item, PositionSnapshot) else PositionSnapshot(**item)
                for item in data
            ]
        raise TypeError(f"unexpected PositionsGet return type: {type(data).__name__}")


# ============================================================================
# OrderInfo Proxy
# ============================================================================


class OrderInfo(TradingClass):
    """Canonical asynchronous OrderInfo API."""

    CLASS_NAME = "OrderInfo"

    async def OrderInfo(self, *args: Any) -> OrderSnapshot:
        """Await the backend OrderInfo snapshot."""
        logger.debug("FR-TRADING-ORDERS: querying order snapshot")
        data = await self._call("OrderInfo", *args)
        if isinstance(data, OrderSnapshot):
            return data
        if isinstance(data, dict):
            return OrderSnapshot(**data)
        raise TypeError(f"unexpected order snapshot type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> OrderSnapshot:
        """Await the backend OrderInfo snapshot directly via call syntax."""
        return await self.OrderInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend order snapshot represented as a dictionary."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, OrderSnapshot):
            return asdict(data)
        raise TypeError(f"unexpected order dictionary type: {type(data).__name__}")

    async def Select(self, *args: Any) -> Any:
        """Await the backend OrderInfo.Select operation."""
        return await self._call("Select", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend OrderInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def StoreState(self, *args: Any) -> Any:
        """Await the backend OrderInfo.StoreState operation."""
        return await self._call("StoreState", *args)

    async def CheckState(self, *args: Any) -> Any:
        """Await the backend OrderInfo.CheckState operation."""
        return await self._call("CheckState", *args)

    async def OrdersTotal(self, *args: Any) -> Any:
        """Await the backend OrderInfo.OrdersTotal operation."""
        return await self._call("OrdersTotal", *args)

    async def OrdersGet(self, *args: Any, **kwargs: Any) -> list[OrderSnapshot]:
        """Await the backend OrderInfo.OrdersGet operation."""
        logger.debug("FR-TRADING-ORDERS: querying orders collection")
        data = (
            await self._call("OrdersGet", kwargs)
            if kwargs
            else await self._call("OrdersGet", *args)
        )
        if isinstance(data, list):
            return [
                item if isinstance(item, OrderSnapshot) else OrderSnapshot(**item)
                for item in data
            ]
        raise TypeError(f"unexpected OrdersGet return type: {type(data).__name__}")


# ============================================================================
# HistoryOrderInfo Proxy
# ============================================================================


class HistoryOrderInfo(TradingClass):
    """Canonical asynchronous HistoryOrderInfo API."""

    CLASS_NAME = "HistoryOrderInfo"

    async def HistoryOrderInfo(self, *args: Any) -> HistoryOrderSnapshot:
        """Await the backend HistoryOrderInfo snapshot."""
        logger.debug("FR-TRADING-HISTORY: querying history order snapshot")
        data = await self._call("HistoryOrderInfo", *args)
        if isinstance(data, HistoryOrderSnapshot):
            return data
        if isinstance(data, dict):
            return HistoryOrderSnapshot(**data)
        raise TypeError(
            f"unexpected history order snapshot type: {type(data).__name__}"
        )

    async def __call__(self, *args: Any) -> HistoryOrderSnapshot:
        """Await the backend HistoryOrderInfo snapshot directly via call syntax."""
        return await self.HistoryOrderInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend historical order snapshot represented as a dictionary."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, HistoryOrderSnapshot):
            return asdict(data)
        raise TypeError(
            f"unexpected history order dictionary type: {type(data).__name__}"
        )

    async def Ticket(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.Ticket operation."""
        return await self._call("Ticket", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def HistoryOrdersTotal(self, *args: Any, **kwargs: Any) -> Any:
        """Await the backend HistoryOrderInfo.HistoryOrdersTotal operation."""
        if kwargs:
            return await self._call("HistoryOrdersTotal", kwargs)
        return await self._call("HistoryOrdersTotal", *args)

    async def HistoryOrdersGet(
        self, *args: Any, **kwargs: Any
    ) -> list[HistoryOrderSnapshot]:
        """Await the backend HistoryOrderInfo.HistoryOrdersGet operation."""
        logger.debug("FR-TRADING-HISTORY: querying history orders collection")
        data = (
            await self._call("HistoryOrdersGet", kwargs)
            if kwargs
            else await self._call("HistoryOrdersGet", *args)
        )
        if isinstance(data, list):
            return [
                item
                if isinstance(item, HistoryOrderSnapshot)
                else HistoryOrderSnapshot(**item)
                for item in data
            ]
        raise TypeError(
            f"unexpected HistoryOrdersGet return type: {type(data).__name__}"
        )


# ============================================================================
# DealInfo Proxy
# ============================================================================


class DealInfo(TradingClass):
    """Canonical asynchronous DealInfo API."""

    CLASS_NAME = "DealInfo"

    async def DealInfo(self, *args: Any) -> DealSnapshot:
        """Await the backend DealInfo snapshot."""
        logger.debug("FR-TRADING-HISTORY: querying deal snapshot")
        data = await self._call("DealInfo", *args)
        if isinstance(data, DealSnapshot):
            return data
        if isinstance(data, dict):
            return DealSnapshot(**data)
        raise TypeError(f"unexpected deal snapshot type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> DealSnapshot:
        """Await the backend DealInfo snapshot directly via call syntax."""
        return await self.DealInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend historical deal snapshot represented as a dictionary."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, DealSnapshot):
            return asdict(data)
        raise TypeError(f"unexpected deal dictionary type: {type(data).__name__}")

    async def Ticket(self, *args: Any) -> Any:
        """Await the backend DealInfo.Ticket operation."""
        return await self._call("Ticket", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend DealInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def HistoryDealsTotal(self, *args: Any, **kwargs: Any) -> Any:
        """Await the backend DealInfo.HistoryDealsTotal operation."""
        if kwargs:
            return await self._call("HistoryDealsTotal", kwargs)
        return await self._call("HistoryDealsTotal", *args)

    async def HistoryDealsGet(self, *args: Any, **kwargs: Any) -> list[DealSnapshot]:
        """Await the backend DealInfo.HistoryDealsGet operation."""
        logger.debug("FR-TRADING-HISTORY: querying history deals collection")
        data = (
            await self._call("HistoryDealsGet", kwargs)
            if kwargs
            else await self._call("HistoryDealsGet", *args)
        )
        if isinstance(data, list):
            return [
                item if isinstance(item, DealSnapshot) else DealSnapshot(**item)
                for item in data
            ]
        raise TypeError(
            f"unexpected HistoryDealsGet return type: {type(data).__name__}"
        )


def main() -> None:
    """Demonstrate proxy class definitions."""
    proxies = [
        AccountInfo,
        TerminalInfo,
        SymbolInfo,
        PositionInfo,
        OrderInfo,
        HistoryOrderInfo,
        DealInfo,
    ]
    print(f"Initialized {len(proxies)} trading proxy classes.")


if __name__ == "__main__":
    main()
