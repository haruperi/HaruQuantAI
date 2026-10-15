"""Master unified Trading facade composing all proxy classes.

Description:
    Provides the Trading master facade class, coordinating the eight MQL5 async
    trading proxy classes (trade, account, symbol, order, history_order, position,
    deal, terminal) into a single cohesive interface.

Purpose:
    FEAT-TRADING-FACADE: Master trading facade class.

Key Capabilities:
    - FR-TRADING-MASTER-FACADE: Unified eight-class trading composition.
      Associated: `Trading`, `Trading.wait_connected()`, `Trading.close()`.
      Logging: DEBUG master facade composition and connection readiness.

Python API Usage:
    ```python
    from app.services.trading.facade import Trading

    async with Trading(backend) as trading:
        await trading.wait_connected()
        account = await trading.account.AccountInfo()
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.trading.facade
    ```
"""

from __future__ import annotations

from types import TracebackType
from typing import Self

from app.host.logging import get_logger

from .enums import BridgeEvent, Receipt, TradingBackend
from .proxies import (
    AccountInfo,
    DealInfo,
    HistoryOrderInfo,
    OrderInfo,
    PositionInfo,
    SymbolInfo,
    TerminalInfo,
)
from .trade import Trade

__all__ = [
    "Trading",
]

logger = get_logger(__name__)


class Trading:
    """The unified eight-class composition for every async trading backend."""

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


def main() -> None:
    """Demonstrate Trading facade definition."""
    print(f"Master composition Trading class: {Trading.__name__}")


if __name__ == "__main__":
    main()
