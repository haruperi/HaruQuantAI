"""Base forwarding proxy class with per-object identity and serialized calls.

Description:
    Provides TradingClass (BaseTradingClass), the foundational proxy base class
    managing backend identity, serialized command locks, wire argument encoding,
    and property value unwrapping for quantitative trading proxies.

Purpose:
    FEAT-TRADING-BASE: Base proxy class with per-object identity and locking.

Key Capabilities:
    - FR-TRADING-BASE-PROXY: Asynchronous command serialization and proxy identity.
      Associated: `TradingClass`, `BaseTradingClass`.
      Logging: DEBUG object creation and backend call invocation.

Python API Usage:
    ```python
    from app.services.trading.base import BaseTradingClass, TradingClass


    class CustomProxy(TradingClass):
        CLASS_NAME = "Custom"
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.trading.base
    ```
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any

from app.host.logging import get_logger
from app.services.libs.contracts import PropertyValue, TradingBackend

__all__ = [
    "BaseTradingClass",
    "TradingClass",
]

logger = get_logger(__name__)


class TradingClass:
    """Backend-neutral object identity and serialized async forwarding."""

    CLASS_NAME = "Base"
    TRADING_METHODS: frozenset[str] = frozenset()

    def __init__(
        self, backend: TradingBackend, *, object_id: str | None = None
    ) -> None:
        logger.debug("FR-TRADING-COMPOSITION: creating object")
        self.backend = backend
        self.object_id = object_id or f"{self.CLASS_NAME.lower()}-{uuid.uuid4().hex}"
        self._lock = asyncio.Lock()

    @property
    def last_command_id(self) -> str | None:
        """Return the last command in this task context."""
        return self.backend.last_command_id()

    async def _call(self, method: str, *args: Any) -> Any:
        logger.debug(
            "FR-TRADING-COMPOSITION: invoking backend",
            extra={"class_name": self.CLASS_NAME, "method_name": method},
        )
        wire_args: list[Any] = []
        for value in args:
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    raise ValueError("trading datetimes must include a timezone")
                wire_args.append(int(value.timestamp()))
            else:
                wire_args.append(value)
        async with self._lock:
            return await self.backend.call(
                object_id=self.object_id,
                class_name=self.CLASS_NAME,
                method_name=method,
                args=wire_args,
                requires_arm=method in self.TRADING_METHODS,
            )

    async def _property(self, method: str, *args: Any) -> PropertyValue:
        value = await self._call(method, *args)
        if isinstance(value, dict) and {"ok", "value"} <= value.keys():
            return PropertyValue(
                ok=bool(value["ok"]),
                value=value.get("value"),
                error=value.get("error"),
            )
        return PropertyValue(ok=True, value=value)


BaseTradingClass = TradingClass


def main() -> None:
    """Demonstrate TradingClass base proxy identity."""
    print(f"TradingClass default name: {TradingClass.CLASS_NAME}")
    print(f"BaseTradingClass alias identity: {BaseTradingClass is TradingClass}")


if __name__ == "__main__":
    main()
