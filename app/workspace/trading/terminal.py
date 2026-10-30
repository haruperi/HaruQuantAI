"""Shared terminal information interface.

Description:
    Provides asynchronous TerminalProxy for querying terminal state,
    connection properties, broker build, and ping.
Purpose:
    FEAT-LIVE-TRADING-FACADE: Centralize live trading facade and terminal info.
Key Capabilities:
    - FR-trading-terminal-snapshot: Query TerminalInfo snapshot from the broker.
Python API Usage:
    from app.workspace.trading.terminal import TerminalProxy
CLI Usage:
    uv run python -m pytest tests/workspace/trading -q
"""

# ruff: noqa: N802 -- MQL5 PascalCase API compatibility
from __future__ import annotations

from typing import Any

from app.core.data import contracts
from app.core.host.logging import get_logger

from .base import TradingClass

logger = get_logger(__name__)


class TerminalProxy(TradingClass):
    """Canonical asynchronous TerminalInfo API proxy."""

    CLASS_NAME = "TerminalInfo"

    async def TerminalInfo(self, *args: Any) -> contracts.TerminalInfo:
        """Await the backend TerminalInfo snapshot."""
        logger.debug("FR-trading-terminal-snapshot: querying terminal snapshot")
        return await self._snapshot(
            "TerminalInfo", contracts.TerminalInfo, "terminal info", *args
        )

    async def __call__(self, *args: Any) -> contracts.TerminalInfo:
        """Await the backend TerminalInfo snapshot directly via call syntax."""
        return await self.TerminalInfo(*args)
