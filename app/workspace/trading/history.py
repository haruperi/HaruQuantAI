"""Shared historical order and deal queries."""

# ruff: noqa: N802 -- MQL5 PascalCase API compatibility
from __future__ import annotations

from typing import Any

from app.core.host.logging import get_logger
from app.include import contracts

from .base import TradingClass

logger = get_logger(__name__)


class HistoryOrderProxy(TradingClass):
    """Canonical asynchronous HistoryOrderInfo API proxy."""

    CLASS_NAME = "HistoryOrderInfo"

    async def HistoryOrderInfo(self, *args: Any) -> contracts.OrderInfo:
        """Await the backend HistoryOrderInfo snapshot."""
        logger.debug("FR-TRADING-HISTORY: querying history order snapshot")
        return await self._snapshot(
            "HistoryOrderInfo", contracts.OrderInfo, "history order info", *args
        )

    async def __call__(self, *args: Any) -> contracts.OrderInfo:
        """Await the backend HistoryOrderInfo snapshot directly via call syntax."""
        return await self.HistoryOrderInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend historical order snapshot represented as a dictionary."""
        return await self._snapshot_dict(contracts.OrderInfo, "history order", *args)

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
    ) -> list[contracts.OrderInfo]:
        """Await the backend HistoryOrderInfo.HistoryOrdersGet operation."""
        logger.debug("FR-TRADING-HISTORY: querying history orders collection")
        return await self._collection(
            "HistoryOrdersGet", contracts.OrderInfo, *args, **kwargs
        )


class DealProxy(TradingClass):
    """Canonical asynchronous DealInfo API proxy."""

    CLASS_NAME = "DealInfo"

    async def DealInfo(self, *args: Any) -> contracts.DealInfo:
        """Await the backend DealInfo snapshot."""
        logger.debug("FR-TRADING-HISTORY: querying deal snapshot")
        return await self._snapshot("DealInfo", contracts.DealInfo, "deal info", *args)

    async def __call__(self, *args: Any) -> contracts.DealInfo:
        """Await the backend DealInfo snapshot directly via call syntax."""
        return await self.DealInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend historical deal snapshot represented as a dictionary."""
        return await self._snapshot_dict(contracts.DealInfo, "deal", *args)

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

    async def HistoryDealsGet(
        self, *args: Any, **kwargs: Any
    ) -> list[contracts.DealInfo]:
        """Await the backend DealInfo.HistoryDealsGet operation."""
        logger.debug("FR-TRADING-HISTORY: querying history deals collection")
        return await self._collection(
            "HistoryDealsGet", contracts.DealInfo, *args, **kwargs
        )
