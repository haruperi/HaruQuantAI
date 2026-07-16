"""Serialized non-blocking MetaTrader 5 terminal transport."""

# ruff: noqa: ANN401 - the optional SDK has heterogeneous documented return types.

from __future__ import annotations

import asyncio
import importlib
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.brokers.contracts import BrokerConnectionConfig
from app.services.brokers.runtime.circuit_breaker import _TransportCircuitBreaker
from app.utils import logger


class _MT5Transport:
    """Own one serialized terminal/account session."""

    def __init__(self, config: BrokerConnectionConfig) -> None:
        self._config = config
        self._sdk: Any = None
        self._lock = asyncio.Lock()
        self._circuit = _TransportCircuitBreaker(
            failure_threshold=config.circuit_failure_threshold,
            recovery_timeout_sec=config.circuit_recovery_timeout_sec,
            half_open_max_calls=config.circuit_half_open_max_calls,
        )

    async def connect(self) -> bool:
        """Initialize and authenticate one configured terminal session."""
        self._sdk = importlib.import_module("MetaTrader5")
        credentials = self._config.credentials or {}
        kwargs: dict[str, object] = {}
        path = credentials.get("terminal_path")
        if path is not None:
            kwargs["path"] = path.get_secret_value()
        login = credentials.get("login")
        password = credentials.get("password")
        server = credentials.get("server")
        if login is not None:
            kwargs["login"] = int(login.get_secret_value())
        if password is not None:
            kwargs["password"] = password.get_secret_value()
        if server is not None:
            kwargs["server"] = server.get_secret_value()
        result = await self._run(self._sdk.initialize, **kwargs)
        logger.bind(
            broker=self._config.broker_id.value,
            environment=self._config.environment.value,
            result="success" if result else "error",
        ).info("MT5 terminal transport initialize/authenticate completed")
        return bool(result)

    async def call(self, name: str, *args: object, **kwargs: object) -> Any:
        """Call one documented SDK operation through the serialized worker."""
        if self._sdk is None:
            raise ConnectionError("MT5 session is not initialized")
        function: Callable[..., Any] = getattr(self._sdk, name)
        return await self._run(function, *args, **kwargs)

    async def _run(
        self, function: Callable[..., Any], *args: object, **kwargs: object
    ) -> Any:
        async with self._lock:
            return await asyncio.wait_for(
                asyncio.to_thread(function, *args, **kwargs),
                timeout=self._config.request_timeout_sec,
            )

    async def close(self) -> None:
        """Release the exact owned terminal handle deterministically."""
        if self._sdk is not None:
            await self._run(self._sdk.shutdown)
            self._sdk = None
            logger.bind(
                broker=self._config.broker_id.value,
                environment=self._config.environment.value,
            ).info("MT5 terminal transport handle released")
