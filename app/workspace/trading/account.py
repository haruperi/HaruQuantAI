"""Shared account snapshots and trading calculations.

Description:
    Provides asynchronous AccountProxy querying account balances, equity, margin,
    leverage, and currency parameters from the active backend.
Purpose:
    FEAT-LIVE-TRADING-FACADE: Centralize live trading facade and account queries.
Key Capabilities:
    - FR-trading-account-snapshot: Await strongly-typed AccountInfo snapshot.
    - FR-trading-account-checks: Await margin, free margin, order profit, and max lots.
Python API Usage:
    from app.workspace.trading.account import AccountProxy
CLI Usage:
    uv run python -m pytest tests/workspace/trading -q
"""

# ruff: noqa: N802 -- MQL5 PascalCase API compatibility
from __future__ import annotations

from typing import Any

from app.core.host.logging import get_logger
from app.core.trading.connection import contracts

from .base import TradingClass

logger = get_logger(__name__)


class AccountProxy(TradingClass):
    """Canonical asynchronous AccountInfo API proxy."""

    CLASS_NAME = "AccountInfo"

    async def AccountInfo(self, *args: Any) -> contracts.AccountInfo:
        """Await the backend AccountInfo snapshot."""
        logger.debug("FR-trading-account-snapshot: querying account snapshot")
        return await self._snapshot(
            "AccountInfo", contracts.AccountInfo, "account info", *args
        )

    async def __call__(self, *args: Any) -> contracts.AccountInfo:
        """Await the backend AccountInfo snapshot directly via call syntax."""
        return await self.AccountInfo(*args)

    async def OrderProfitCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.OrderProfitCheck operation."""
        logger.debug("FR-trading-account-checks: checking order profit")
        return await self._call("OrderProfitCheck", *args)

    async def MarginCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.MarginCheck operation."""
        logger.debug("FR-trading-account-checks: checking margin")
        return await self._call("MarginCheck", *args)

    async def FreeMarginCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.FreeMarginCheck operation."""
        logger.debug("FR-trading-account-checks: checking free margin")
        return await self._call("FreeMarginCheck", *args)

    async def MaxLotCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.MaxLotCheck operation."""
        logger.debug("FR-trading-account-checks: checking max lot")
        return await self._call("MaxLotCheck", *args)
