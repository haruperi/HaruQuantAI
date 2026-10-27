"""Trading facade composition, lifecycle, receipts, and events."""

from __future__ import annotations

from types import TracebackType
from typing import Self

from app.host.logging import get_logger
from app.include.contracts import (
    BridgeEvent,
    Receipt,
    TradingBackend,
)

from .account import AccountProxy
from .exits import ExitManager
from .history import DealProxy, HistoryOrderProxy
from .orders import OrderProxy
from .positions import PositionProxy
from .symbol import SymbolProxy
from .terminal import TerminalProxy
from .trade import Trade

logger = get_logger(__name__)


class Trading:
    """The unified eight-class composition for every async trading backend."""

    def __init__(self, backend: TradingBackend) -> None:
        logger.debug("FR-TRADING-COMPOSITION: composing trading classes")
        self.backend = backend
        self.account = AccountProxy(backend)
        self.symbol = SymbolProxy(backend)
        self.order = OrderProxy(backend)
        self.position = PositionProxy(backend, symbol=self.symbol, account=self.account)
        self.deal = DealProxy(backend)
        self.history_order = HistoryOrderProxy(
            backend, deal=self.deal, symbol=self.symbol
        )
        self.terminal = TerminalProxy(backend)
        self.trade = Trade(
            backend, position=self.position, order=self.order, symbol=self.symbol
        )
        self.exits = ExitManager(self.trade, self.position, self.symbol)

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

    async def next_event(self, timeout: float | None = None) -> BridgeEvent:  # noqa: ASYNC109
        """Wait for a backend event within the requested timeout."""
        logger.debug("FR-TRADING-COMPOSITION: waiting for event")
        return await self.backend.next_event(timeout)

    async def await_request_event(
        self,
        request_id: int,
        timeout: float | None = None,  # noqa: ASYNC109
    ) -> BridgeEvent:
        """Delegate supported request correlation, or surface capability failure."""
        logger.debug("FR-TRADING-COMPOSITION: waiting for correlated event")
        return await self.backend.await_request_event(request_id, timeout)

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
