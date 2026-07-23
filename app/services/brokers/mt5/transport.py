"""Serialized non-blocking MetaTrader 5 terminal transport."""

# ruff: noqa: ANN401 - the optional SDK has heterogeneous documented return types.

from __future__ import annotations

import asyncio
import importlib
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.brokers.contracts import BrokerConnectionConfig
from app.services.brokers.runtime.circuit_breaker import _TransportCircuitBreaker
from app.utils import logger


class _MT5Transport:
    """Own one serialized terminal/account session."""

    def __init__(
        self,
        config: BrokerConnectionConfig,
        latency_sink: Callable[[float], None] | None = None,
    ) -> None:
        """Initialize the _MT5Transport instance.

        Args:
            config: Immutable connection configuration for this session.
            latency_sink: Optional receiver for the measured milliseconds spent
                inside each provider SDK call, used to separate provider
                latency from local adapter overhead.
        """
        self._config = config
        self._latency_sink = latency_sink
        self._sdk: Any = None
        self._lock = asyncio.Lock()
        self._circuit = _TransportCircuitBreaker(
            failure_threshold=config.circuit_failure_threshold,
            recovery_timeout_sec=config.circuit_recovery_timeout_sec,
            half_open_max_calls=config.circuit_half_open_max_calls,
        )

    async def connect(self) -> bool:
        """Initialize and authenticate one configured terminal session.

        Returns:
            Whether MT5 initialized the configured terminal session.
        """
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
        """Call one documented SDK operation through the serialized worker.

        Returns:
            Exact provider SDK result.

        Raises:
            ConnectionError: If the MT5 SDK session is not initialized.
        """
        if self._sdk is None:
            raise ConnectionError("MT5 session is not initialized")
        function: Callable[..., Any] = getattr(self._sdk, name)
        return await self._run(function, *args, **kwargs)

    async def constant(self, name: str) -> object:
        """Return one documented SDK constant from the connected transport.

        Returns:
            The exact SDK constant value.

        Raises:
            ConnectionError: If the terminal session is not initialized.
        """
        if self._sdk is None:
            raise ConnectionError("MT5 session is not initialized")
        return getattr(self._sdk, name)

    async def _run(
        self, function: Callable[..., Any], *args: object, **kwargs: object
    ) -> Any:
        """Handle run.

        Args:
            function: Value supplied to the operation.
            args: Value supplied to the operation.
            kwargs: Value supplied to the operation.

        Returns:
            The operation result.
        """
        async with self._lock:
            started = time.perf_counter()
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(function, *args, **kwargs),
                    timeout=self._config.request_timeout_sec,
                )
            finally:
                if self._latency_sink is not None:
                    self._latency_sink((time.perf_counter() - started) * 1000.0)

    async def close(self) -> None:
        """Release the exact owned terminal handle deterministically."""
        if self._sdk is not None:
            await self._run(self._sdk.shutdown)
            self._sdk = None
            logger.bind(
                broker=self._config.broker_id.value,
                environment=self._config.environment.value,
            ).info("MT5 terminal transport handle released")
