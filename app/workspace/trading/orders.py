"""Shared working-order selection and collection queries."""

# ruff: noqa: N802 -- MQL5 PascalCase API compatibility
from __future__ import annotations

from typing import Any

from app.host.logging import get_logger
from app.include import contracts

from .base import TradeFilter, TradingClass

logger = get_logger(__name__)


class OrderProxy(TradingClass):
    """Canonical asynchronous OrderInfo API proxy."""

    CLASS_NAME = "OrderInfo"

    async def OrderInfo(self, *args: Any) -> contracts.OrderInfo:
        """Await the backend OrderInfo snapshot."""
        logger.debug("FR-TRADING-ORDERS: querying order snapshot")
        return await self._snapshot(
            "OrderInfo", contracts.OrderInfo, "order info", *args
        )

    async def __call__(self, *args: Any) -> contracts.OrderInfo:
        """Await the backend OrderInfo snapshot directly via call syntax."""
        return await self.OrderInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend order snapshot represented as a dictionary."""
        return await self._snapshot_dict(contracts.OrderInfo, "order", *args)

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

    async def OrdersGet(self, *args: Any, **kwargs: Any) -> list[contracts.OrderInfo]:
        """Await the backend OrderInfo.OrdersGet operation."""
        logger.debug("FR-TRADING-ORDERS: querying orders collection")
        return await self._collection("OrdersGet", contracts.OrderInfo, *args, **kwargs)

    async def pending_order_exists(self, scope: TradeFilter) -> bool:
        """Return whether any matching pending order exists."""
        return any(
            scope.matches(order)
            for order in await self.OrdersGet()
            if order.order_type in (2, 3, 4, 5, 6, 7)
        )

    async def pending_order_doesnt_exist(self, scope: TradeFilter) -> bool:
        """Return whether no matching pending order exists."""
        return not await self.pending_order_exists(scope)

    async def _order_value(self, scope: TradeFilter, field: str) -> float:
        for order in await self.OrdersGet():
            if order.order_type in (2, 3, 4, 5, 6, 7) and scope.matches(order):
                return float(getattr(order, field))
        return -1.0

    async def order_open_price(self, scope: TradeFilter) -> float:
        """Return the first matching pending entry price, or -1 when absent."""
        return await self._order_value(scope, "price_open")

    async def order_sl(self, scope: TradeFilter) -> float:
        """Return the first matching pending stop loss, or -1 when absent."""
        return await self._order_value(scope, "sl")

    async def order_pt(self, scope: TradeFilter) -> float:
        """Return the first matching pending target, or -1 when absent."""
        return await self._order_value(scope, "tp")
