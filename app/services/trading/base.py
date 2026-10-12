"""Backend-neutral serialized trading operation forwarding.

Description:
    Serializes calls for each object and adapts property results. The backend
    is an async protocol; public trading classes never import concrete brokers.

Purpose:
    FEAT-TRADING-API: Forward native method calls through the shared broker
    transport while preserving per-object state and execution authorization.

Key Capabilities:
    - FR-TRADING-CALL-FORWARDING: Serialize calls and delegate wire transport.
      Associated: `TradingClass._call()`, `TradingClass._property()`
      Logging: DEBUG object creation and invocation metadata, excluding arguments;
        backend logging records native encoding or local dispatch attempts.

Python API Usage:
    Use the concrete proxies exposed by MetaTrader; TradingClass supplies their
    shared forwarding implementation and property conversion.

CLI Usage:
    uv run pytest tests/unit/services/test_metatrader_bridge_protocol.py --no-cov
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any

from app.host.logging import get_logger
from app.services.brokers.contracts import PropertyValue, TradingBackend

logger = get_logger(__name__)


class TradingClass:
    """Backend-neutral object identity and serialized async forwarding."""

    CLASS_NAME = "Base"
    TRADING_METHODS: frozenset[str] = frozenset()

    def __init__(
        self, backend: TradingBackend, *, object_id: str | None = None
    ) -> None:
        logger.debug("FR-TRADING-CALL-FORWARDING: creating object")
        self.backend = backend
        self.object_id = object_id or f"{self.CLASS_NAME.lower()}-{uuid.uuid4().hex}"
        self._lock = asyncio.Lock()

    @property
    def last_command_id(self) -> str | None:
        """Return the last command in this task context."""
        return self.backend.last_command_id()

    async def _call(self, method: str, *args: Any) -> Any:
        logger.debug(
            "FR-TRADING-CALL-FORWARDING: invoking backend",
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
