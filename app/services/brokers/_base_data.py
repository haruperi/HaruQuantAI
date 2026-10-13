"""Base asynchronous data broker backend conforming to TradingBackend.

Description:
    Provides a lightweight base class for read-only market data providers that conforms
    to the canonical `TradingBackend` protocol. Routes `MarketData.Bars` and
    `MarketData.Ticks` to typed provider retrieval hooks, returns `SymbolSnapshot`
    for symbol queries, and manages audit receipts without live trade mutation overhead.

Purpose:
    FEAT-BROKER-DATA-BASE: Uniform base backend for market data providers.

Key Capabilities:
    - FR-DATA-BACKEND-ROUTING: Route MarketData and SymbolInfo calls to subclass hooks.
      Associated: `DataBrokerBackend.call()`, `fetch_bars()`, `fetch_ticks()`
      Logging: DEBUG on call routing with operation name; no raw payloads.
    - FR-DATA-BACKEND-LIFECYCLE: Manage session start/stop and connection state.
      Associated: `DataBrokerBackend.start()`, `DataBrokerBackend.close()`
      Logging: INFO on session start/close.

Python API Usage:
    ```python
    from app.services.brokers._base_data import DataBrokerBackend


    class MyDataBroker(DataBrokerBackend):
        def __init__(self) -> None:
            super().__init__(name="MyDataBroker")
```

CLI Usage:
    `uv run pytest tests/unit/services/brokers/ --no-cov`
"""

from __future__ import annotations

import contextvars
import time
import uuid
from dataclasses import asdict, is_dataclass, replace
from types import TracebackType
from typing import Any, Self

from app.host.logging import get_logger
from app.services.brokers.contracts import (
    BridgeError,
    BridgeEvent,
    MarketBar,
    MarketTick,
    Receipt,
    ReceiptStatus,
    SymbolSnapshot,
    TerminalSnapshot,
)

logger = get_logger(__name__)


class DataBrokerBackend:
    """Base class for market data providers conforming to TradingBackend."""

    def __init__(self, name: str) -> None:
        """Initialize data broker backend."""
        self.name = name
        self.logger = get_logger(f"app.services.brokers.{name.lower()}")
        self._last_cmd: contextvars.ContextVar[str | None] = contextvars.ContextVar(
            f"{name}_last_cmd", default=None
        )
        self._receipts: dict[str, Receipt] = {}
        self._is_connected: bool = True

    async def start(self) -> None:
        """Start or initialize provider connection session."""
        self._is_connected = True

    async def wait_connected(self, timeout: float | None = None) -> None:  # noqa: ASYNC109 -- backend deadline
        """Confirm provider readiness."""
        del timeout
        self._is_connected = True

    async def close(self) -> None:
        """Close provider connection session."""
        self._is_connected = False

    def arm(self) -> None:
        """No-op for read-only data brokers."""

    def disarm(self) -> None:
        """No-op for read-only data brokers."""

    def last_command_id(self) -> str | None:
        """Return the ID of the most recent dispatched command."""
        return self._last_cmd.get()

    def receipt(self, command_id: str) -> Receipt | None:
        """Return the execution receipt for a previously dispatched command."""
        return self._receipts.get(command_id)

    async def next_event(self, timeout: float | None = None) -> BridgeEvent:  # noqa: ASYNC109 -- backend deadline
        """Data brokers do not emit transaction events."""
        del timeout
        raise NotImplementedError(
            f"{self.name} is a read-only market data broker and does not emit transaction events"
        )

    async def await_request_event(
        self,
        request_id: int,
        timeout: float | None = None,  # noqa: ASYNC109 -- backend deadline
    ) -> BridgeEvent:
        """Data brokers do not emit transaction events."""
        del request_id, timeout
        raise NotImplementedError(
            f"{self.name} is a read-only market data broker and does not emit transaction events"
        )

    async def __aenter__(self) -> Self:
        """Enter asynchronous context."""
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Exit asynchronous context."""
        del exc_type, exc, tb
        await self.close()

    async def call(
        self,
        *,
        object_id: str,
        class_name: str,
        method_name: str,
        args: list[Any],
        requires_arm: bool = False,
        timeout: float | None = None,  # noqa: ASYNC109 -- backend deadline
    ) -> Any:
        """Execute a canonical market data or metadata query."""
        del requires_arm, timeout
        cmd_id = f"cmd-{uuid.uuid4().hex[:12]}"
        self._last_cmd.set(cmd_id)
        now = time.time()
        receipt = Receipt(
            command_id=cmd_id,
            object_id=object_id,
            class_name=class_name,
            method_name=method_name,
            status=ReceiptStatus.CREATED,
            created_at=now,
        )
        self._receipts[cmd_id] = receipt

        try:
            val = self._dispatch(class_name, method_name, args)
            val_serialized: Any = (
                asdict(val) if is_dataclass(val) and not isinstance(val, type) else val
            )
            self._receipts[cmd_id] = replace(
                receipt,
                status=ReceiptStatus.RESOLVED,
                sent_at=now,
                acknowledged_at=now,
                resolved_at=now,
                value=val_serialized,
            )
            return val
        except Exception as exc:
            code = getattr(exc, "code", "DATA_BROKER_ERROR")
            self._receipts[cmd_id] = replace(
                receipt,
                status=ReceiptStatus.REJECTED,
                sent_at=now,
                acknowledged_at=now,
                resolved_at=now,
                error={"code": str(code), "message": str(exc)},
            )
            raise

    def _dispatch(self, class_name: str, method_name: str, args: list[Any]) -> Any:
        """Route call to subclass methods."""
        if class_name == "MarketData":
            if method_name == "Bars":
                return self._dispatch_bars(args)
            if method_name == "Ticks":
                return self._dispatch_ticks(args)
        if class_name == "SymbolInfo":
            if method_name in ("SymbolInfo", "info"):
                symbol = str(args[0]) if args else "EURUSD"
                return self.symbol_info(symbol)
            if method_name in ("SymbolsGet", "symbols"):
                return self.symbols_get()
        if class_name == "TerminalInfo" and method_name in ("TerminalInfo", "info"):
            return TerminalSnapshot(
                name=self.name,
                company=self.name,
                connected=self._is_connected,
                trade_allowed=False,
            )
        raise BridgeError(
            f"{self.name} does not support {class_name}.{method_name}",
            code="UNSUPPORTED_OPERATION",
        )

    def _dispatch_bars(self, args: list[Any]) -> list[dict[str, Any]] | list[MarketBar]:
        """Unpack canonical args and invoke fetch_bars."""
        symbol = str(args[0]) if len(args) > 0 else "EURUSD"
        timeframe = str(args[1]) if len(args) > 1 else "H1"
        mode = str(args[2]) if len(args) > 2 else "latest"
        start = int(args[3]) if len(args) > 3 else 0
        end = int(args[4]) if len(args) > 4 else 0
        count = int(args[5]) if len(args) > 5 else 0
        limit = int(args[6]) if len(args) > 6 else 1000
        return self.fetch_bars(
            symbol=symbol,
            timeframe=timeframe,
            mode=mode,
            start=start,
            end=end,
            count=count,
            limit=limit,
        )

    def _dispatch_ticks(
        self, args: list[Any]
    ) -> list[dict[str, Any]] | list[MarketTick]:
        """Unpack canonical args and invoke fetch_ticks."""
        symbol = str(args[0]) if len(args) > 0 else "EURUSD"
        mode = str(args[1]) if len(args) > 1 else "latest"
        start_ms = int(args[2]) if len(args) > 2 else 0
        end_ms = int(args[3]) if len(args) > 3 else 0
        count = int(args[4]) if len(args) > 4 else 0
        limit = int(args[5]) if len(args) > 5 else 1000
        return self.fetch_ticks(
            symbol=symbol,
            mode=mode,
            start_ms=start_ms,
            end_ms=end_ms,
            count=count,
            limit=limit,
        )

    def fetch_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        mode: str,
        start: int,
        end: int,
        count: int,
        limit: int,
    ) -> list[dict[str, Any]] | list[MarketBar]:
        """Subclass hook to fetch historical candlestick bars."""
        del symbol, timeframe, mode, start, end, count, limit
        raise BridgeError(
            f"{self.name} does not support historical bars",
            code="UNSUPPORTED_OPERATION",
        )

    def fetch_ticks(
        self,
        *,
        symbol: str,
        mode: str,
        start_ms: int,
        end_ms: int,
        count: int,
        limit: int,
    ) -> list[dict[str, Any]] | list[MarketTick]:
        """Subclass hook to fetch historical or live ticks."""
        del symbol, mode, start_ms, end_ms, count, limit
        raise BridgeError(
            f"{self.name} does not support tick history",
            code="UNSUPPORTED_OPERATION",
        )

    def symbol_info(self, symbol: str) -> SymbolSnapshot:
        """Subclass hook to query symbol properties as SymbolSnapshot."""
        return SymbolSnapshot(name=symbol)

    def symbols_get(self) -> list[str]:
        """Subclass hook to query available symbols."""
        return []
