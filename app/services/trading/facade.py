"""Canonical asynchronous trading facade.

Description:
    Compose eight stateful trading classes over a declared backend capability.
    Lifecycle, authorization and receipts belong to that backend; class locks
    serialize calls for each native or simulated object. Historical bars/ticks use
    shared read-only helpers alongside the eight classes.

Purpose:
    FEAT-TRADING-API: One strategy-facing API across live and local execution.

Key Capabilities:
    - FR-TRADING-COMPOSITION: Compose classes and delegate backend lifecycle.
      Associated: `Trading`
      Logging: DEBUG lifecycle attempts through the repository logger.
    - FR-TRADING-HISTORICAL-READS: Delegate bounded historical bars and ticks.
      Associated: `get_historical_bars()`, `get_ticks()`
      Logging: Shared helper logs every read attempt and validation step.

Python API Usage:
    Use Trading(backend) as an asynchronous context manager, then await methods.

CLI Usage:
    uv run pytest tests/unit/services/test_trading_api.py --no-cov
"""

from __future__ import annotations

from datetime import datetime
from types import TracebackType
from typing import Self

from app.host.logging import get_logger
from app.services.brokers.contracts import (
    BridgeEvent,
    MarketBar,
    MarketTick,
    Receipt,
    Timeframe,
    TradingBackend,
)

from .account_info import AccountInfo
from .deal_info import DealInfo
from .history_order_info import HistoryOrderInfo
from .market_data import get_historical_bars, get_ticks
from .order_info import OrderInfo
from .position_info import PositionInfo
from .symbol_info import SymbolInfo
from .terminal_info import TerminalInfo
from .trade import Trade

logger = get_logger(__name__)


class Trading:
    """The same eight-class composition for every async backend."""

    def __init__(self, backend: TradingBackend) -> None:
        logger.debug("FR-TRADING-COMPOSITION: composing trading classes")
        self.backend = backend
        self.trade = Trade(backend)
        self.account = AccountInfo(backend)
        self.symbol = SymbolInfo(backend)
        self.order = OrderInfo(backend)
        self.history_order = HistoryOrderInfo(backend)
        self.position = PositionInfo(backend)
        self.deal = DealInfo(backend)
        self.terminal = TerminalInfo(backend)

    async def start(self) -> None:
        """Start the selected backend."""
        logger.debug("FR-TRADING-COMPOSITION: starting backend")
        await self.backend.start()

    async def wait_connected(self, timeout: float | None = None) -> None:  # noqa: ASYNC109
        """Wait for backend readiness."""
        logger.debug("FR-TRADING-COMPOSITION: waiting for backend")
        await self.backend.wait_connected(timeout)

    def arm(self) -> None:
        """Permit mutation operations on the selected backend."""
        logger.debug("FR-TRADING-COMPOSITION: arming backend")
        self.backend.arm()

    def disarm(self) -> None:
        """Revoke mutation permission."""
        logger.debug("FR-TRADING-COMPOSITION: disarming backend")
        self.backend.disarm()

    async def close(self) -> None:
        """Close the selected backend."""
        logger.debug("FR-TRADING-COMPOSITION: closing backend")
        await self.backend.close()

    def last_command_id(self) -> str | None:
        """Read the current task's last backend command identifier."""
        logger.debug("FR-TRADING-COMPOSITION: reading command identity")
        return self.backend.last_command_id()

    def receipt(self, command_id: str) -> Receipt | None:
        """Read a backend command receipt."""
        logger.debug("FR-TRADING-COMPOSITION: reading receipt")
        return self.backend.receipt(command_id)

    async def next_event(self, timeout: float | None = None) -> BridgeEvent:  # noqa: ASYNC109 -- delegated deadline
        """Wait for a backend event within the requested timeout."""
        logger.debug("FR-TRADING-COMPOSITION: waiting for event")
        return await self.backend.next_event(timeout)

    async def await_request_event(
        self,
        request_id: int,
        timeout: float | None = None,  # noqa: ASYNC109 -- delegated deadline
    ) -> BridgeEvent:
        """Delegate supported request correlation, or surface capability failure."""
        logger.debug("FR-TRADING-COMPOSITION: waiting for correlated event")
        return await self.backend.await_request_event(request_id, timeout)

    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: Timeframe,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        *,
        start_pos: int | None = None,
        count: int | None = None,
        limit: int = 1000,
    ) -> list[MarketBar]:
        """Read bars using optional date/index/count selectors."""
        return await get_historical_bars(
            self.backend,
            symbol,
            timeframe,
            date_from,
            date_to,
            start_pos=start_pos,
            count=count,
            limit=limit,
        )

    async def get_ticks(
        self,
        symbol: str,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        *,
        count: int | None = None,
        limit: int = 1000,
    ) -> list[MarketTick]:
        """Read ticks using optional date/count selectors."""
        return await get_ticks(
            self.backend, symbol, date_from, date_to, count=count, limit=limit
        )

    async def __aenter__(self) -> Self:
        """Start the selected backend on context entry."""
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close the selected backend on context exit."""
        await self.close()
