"""Base broker backend adapter and canonical bridge exceptions.

Description:
    Provides the foundational BaseBrokerBackend adapter class conforming to the
    unified TradingBackend protocol. Implements asynchronous request dispatch
    for common broker queries (symbol info, terminal status), per-command audit
    receipts, lifecycle hooks, and the canonical BridgeError exception.

Purpose:
    FEAT-BROKER-BASE: Foundational broker backend adapters and base protocols.

Key Capabilities:
    - FR-BROKER-BASE-ROUTING: Asynchronous dispatch routing for symbol info and
      terminal status queries with structured receipts.
      Associated: `BaseBrokerBackend.call()`, `BaseBrokerBackend.symbol_info()`,
        `BaseBrokerBackend.symbols_get()`.
      Logging: DEBUG execution lifecycle and receipt generation through logger.
    - FR-BROKER-BASE-LIFECYCLE: Connection session management, arming, and receipts.
      Associated: `BaseBrokerBackend.start()`, `BaseBrokerBackend.close()`,
        `BaseBrokerBackend.wait_connected()`, `BaseBrokerBackend.arm()`,
        `BaseBrokerBackend.disarm()`, `BaseBrokerBackend.receipt()`.
      Logging: DEBUG connection status changes.

Python API Usage:
    ```python
    from app.services.brokers.base import BaseBrokerBackend


    class CustomBroker(BaseBrokerBackend):
        def __init__(self) -> None:
            super().__init__("custom_broker")
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_broker_base.py --no-cov
    ```
"""

from __future__ import annotations

import contextvars
import time
import uuid
from dataclasses import asdict, is_dataclass, replace
from types import TracebackType
from typing import Any, Self

from app.host.logging import get_logger
from app.services.libs.trading import (
    BridgeEvent,
    Receipt,
    ReceiptStatus,
    SymbolSnapshot,
    TerminalSnapshot,
)

logger = get_logger(__name__)

__all__ = ["BaseBrokerBackend", "BridgeError"]


class BridgeError(RuntimeError):
    """Base runtime exception for broker and market data bridge operations."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "BRIDGE_ERROR",
        command_id: str | None = None,
        uncertain: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.command_id = command_id
        self.uncertain = uncertain


class BaseBrokerBackend:
    """Base class for broker providers conforming to TradingBackend."""

    def __init__(self, name: str) -> None:
        """Initialize base broker backend."""
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

    async def wait_connected(
        self,
        timeout: float | None = None,  # noqa: ASYNC109 -- backend deadline
    ) -> None:
        """Confirm provider readiness."""
        del timeout
        self._is_connected = True

    async def close(self) -> None:
        """Close provider connection session."""
        self._is_connected = False

    def arm(self) -> None:
        """Arm the broker for live trade actions."""

    def disarm(self) -> None:
        """Disarm the broker against trade actions."""

    def last_command_id(self) -> str | None:
        """Return the ID of the most recent dispatched command."""
        return self._last_cmd.get()

    def receipt(self, command_id: str) -> Receipt | None:
        """Return the execution receipt for a previously dispatched command."""
        return self._receipts.get(command_id)

    async def next_event(
        self,
        timeout: float | None = None,  # noqa: ASYNC109 -- backend deadline
    ) -> BridgeEvent:
        """Default event poll stub."""
        del timeout
        raise NotImplementedError(
            f"{self.name} does not emit asynchronous transaction events"
        )

    async def await_request_event(
        self,
        request_id: int,
        timeout: float | None = None,  # noqa: ASYNC109 -- backend deadline
    ) -> BridgeEvent:
        """Default event correlation stub."""
        del request_id, timeout
        raise NotImplementedError(
            f"{self.name} does not emit asynchronous transaction events"
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
        """Execute a canonical broker or metadata query."""
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
            code = getattr(exc, "code", "BROKER_ERROR")
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

    def symbol_info(self, symbol: str) -> SymbolSnapshot:
        """Subclass hook to query symbol properties as SymbolSnapshot."""
        return SymbolSnapshot(name=symbol)

    def symbols_get(self) -> list[str]:
        """Subclass hook to query available symbols."""
        return []
