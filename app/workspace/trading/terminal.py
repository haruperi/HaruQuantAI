"""Shared terminal information interface."""

# ruff: noqa: N802 -- MQL5 PascalCase API compatibility
from __future__ import annotations

from typing import Any

from app.host.logging import get_logger
from app.include import contracts

from .base import TradingClass

logger = get_logger(__name__)


class TerminalProxy(TradingClass):
    """Canonical asynchronous TerminalInfo API proxy."""

    CLASS_NAME = "TerminalInfo"

    async def TerminalInfo(self, *args: Any) -> contracts.TerminalInfo:
        """Await the backend TerminalInfo snapshot."""
        logger.debug("FR-TRADING-TERMINAL-SNAPSHOT: querying terminal snapshot")
        return await self._snapshot(
            "TerminalInfo", contracts.TerminalInfo, "terminal info", *args
        )

    async def __call__(self, *args: Any) -> contracts.TerminalInfo:
        """Await the backend TerminalInfo snapshot directly via call syntax."""
        return await self.TerminalInfo(*args)
