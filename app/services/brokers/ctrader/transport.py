"""cTrader request correlation and session transport boundary."""

# ruff: noqa: TRY004 - an unexpected provider response is invalid provider evidence.

from __future__ import annotations

import asyncio
import importlib
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.brokers.contracts import BrokerConnectionConfig
from app.utils import logger

type _Sender = Callable[[object], Awaitable[object]]


class _CTraderTransport:
    """Own one session and prevent same-type response cross-correlation."""

    def __init__(
        self,
        config: BrokerConnectionConfig,
        *,
        sender: _Sender | None = None,
    ) -> None:
        self._config = config
        self._sender = sender
        self._locks: dict[type[object], asyncio.Lock] = {}
        self._connected = False

    async def connect(self) -> bool:
        """Load the pinned SDK and establish only a configured session."""
        importlib.import_module("ctrader_open_api")
        if self._sender is None:
            logger.bind(
                broker=self._config.broker_id.value,
                environment=self._config.environment.value,
                result="error",
            ).warning("cTrader transport has no session sender; failing closed")
            return False
        self._connected = True
        logger.bind(
            broker=self._config.broker_id.value,
            environment=self._config.environment.value,
            result="success",
        ).info("cTrader transport session established")
        return True

    async def send(
        self,
        request: object,
        response_type: type[object],
        *,
        request_id: str | None = None,
    ) -> object:
        """Correlate by native ID or serialize the same response type."""
        if not self._connected or self._sender is None:
            raise ConnectionError("cTrader session is not connected")
        lock = self._locks.setdefault(response_type, asyncio.Lock())
        async with lock:
            response = await asyncio.wait_for(
                self._sender(request), timeout=self._config.request_timeout_sec
            )
            if not isinstance(response, response_type):
                raise ValueError("unexpected cTrader response type")
            native_id = getattr(response, "clientMsgId", None)
            if request_id is not None and native_id not in {None, request_id}:
                raise ValueError("cTrader native request ID mismatch")
            return response

    async def close(self) -> None:
        """Release the owned session state."""
        self._connected = False
        logger.bind(
            broker=self._config.broker_id.value,
            environment=self._config.environment.value,
        ).info("cTrader transport session released")
