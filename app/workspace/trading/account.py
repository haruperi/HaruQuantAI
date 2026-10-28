"""Shared account snapshots and trading calculations."""

# ruff: noqa: N802 -- MQL5 PascalCase API compatibility
from __future__ import annotations

from typing import Any

from app.host.logging import get_logger
from app.include import contracts

from .base import TradingClass

logger = get_logger(__name__)


class AccountProxy(TradingClass):
    """Canonical asynchronous AccountInfo API proxy."""

    CLASS_NAME = "AccountInfo"

    async def AccountInfo(self, *args: Any) -> contracts.AccountInfo:
        """Await the backend AccountInfo snapshot."""
        logger.debug("FR-TRADING-ACCOUNT-SNAPSHOT: querying account snapshot")
        return await self._snapshot(
            "AccountInfo", contracts.AccountInfo, "account info", *args
        )

    async def __call__(self, *args: Any) -> contracts.AccountInfo:
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
