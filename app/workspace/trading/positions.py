"""Shared position selection and collection queries."""

# ruff: noqa: N802 -- MQL5 PascalCase API compatibility
from __future__ import annotations

from typing import Any

from app.core.host.logging import get_logger
from app.include import contracts

from .base import TradingClass

logger = get_logger(__name__)


class PositionProxy(TradingClass):
    """Canonical asynchronous PositionInfo API proxy."""

    CLASS_NAME = "PositionInfo"

    async def PositionInfo(self, *args: Any) -> contracts.PositionInfo:
        """Await the backend PositionInfo snapshot."""
        logger.debug("FR-TRADING-POSITIONS: querying position snapshot")
        return await self._snapshot(
            "PositionInfo", contracts.PositionInfo, "position info", *args
        )

    async def __call__(self, *args: Any) -> contracts.PositionInfo:
        """Await the backend PositionInfo snapshot directly via call syntax."""
        return await self.PositionInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend position snapshot represented as a dictionary."""
        return await self._snapshot_dict(contracts.PositionInfo, "position", *args)

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

    async def PositionsGet(
        self, *args: Any, **kwargs: Any
    ) -> list[contracts.PositionInfo]:
        """Await the backend PositionInfo.PositionsGet operation."""
        logger.debug("FR-TRADING-POSITIONS: querying positions collection")
        return await self._collection(
            "PositionsGet", contracts.PositionInfo, *args, **kwargs
        )
