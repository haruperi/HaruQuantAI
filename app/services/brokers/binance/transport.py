# mypy: ignore-errors
"""Bounded Binance direct-channel REST transport."""

# ruff: noqa: ANN401 - the optional SDK has a heterogeneous runtime payload surface.
from __future__ import annotations

import asyncio
import importlib
import logging
import time
from collections.abc import AsyncIterator, Callable
from typing import Any

from app.services.brokers.binance._legacy_types import (
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    _CircuitOpenError,
    _RateLimitedError,
    _TransportCircuitBreaker,
)
from app.services.brokers.binance.config import BinanceConfig

logger = logging.getLogger(__name__)


class _BinanceTransport:
    """Own one python-binance client and close it deterministically."""

    def __init__(
        self,
        config: BinanceConfig | BrokerConnectionConfig,
        latency_sink: Callable[[float], None] | None = None,
    ) -> None:
        """Initialize the _BinanceTransport instance.

        Args:
            config: Immutable connection configuration.
            latency_sink: Optional latency metrics callback.
        """
        self._config = config
        self._latency_sink = latency_sink
        self._client: Any = None
        self._socket_manager: Any = None
        self._circuit = _TransportCircuitBreaker(
            failure_threshold=config.circuit_failure_threshold,
            recovery_timeout_sec=config.circuit_recovery_timeout_sec,
            half_open_max_calls=config.circuit_half_open_max_calls,
        )
        self._used_weight = 0
        self._weight_limit = 6_000

    @property
    def is_connected(self) -> bool:
        """Return True if the client is connected."""
        return self._client is not None

    def _get_broker_and_env(self) -> tuple[str, str]:
        """Return string representations for broker identifier and environment."""
        if isinstance(self._config, BinanceConfig):
            return "binance_spot", str(self._config.environment)
        return str(self._config.broker_id), str(self._config.environment)

    async def connect(self) -> bool:
        """Create a Spot client and verify ping plus server time.

        Returns:
            True after successful connection.
        """
        module = importlib.import_module("binance")

        if isinstance(self._config, BinanceConfig):
            api_key = self._config.api_key
            api_secret = self._config.api_secret
            is_testnet = self._config.environment.upper() in ("TESTNET", "SANDBOX")
            timeout = self._config.connect_timeout_sec
        else:
            credentials = self._config.credentials or {}
            k_obj = credentials.get("api_key")
            s_obj = credentials.get("api_secret")
            api_key = (
                k_obj.get_secret_value()
                if k_obj is not None and hasattr(k_obj, "get_secret_value")
                else (str(k_obj) if k_obj is not None else None)
            )
            api_secret = (
                s_obj.get_secret_value()
                if s_obj is not None and hasattr(s_obj, "get_secret_value")
                else (str(s_obj) if s_obj is not None else None)
            )
            is_testnet = self._config.environment == BrokerEnvironment.TESTNET
            timeout = self._config.connect_timeout_sec

        self._client = await asyncio.wait_for(
            module.AsyncClient.create(
                api_key,
                api_secret,
                testnet=is_testnet,
            ),
            timeout=timeout,
        )
        await self.call("ping")
        await self.call("get_server_time")
        logger.info("Binance transport client created and verified")
        return True

    async def call(self, name: str, **kwargs: object) -> Any:
        """Execute one bounded approved client call without replay.

        Args:
            name: Provider client method name.
            **kwargs: Call parameters.

        Returns:
            Exact provider SDK result.

        Raises:
            ConnectionError: If no client exists.
            _CircuitOpenError: If the circuit is open.
            _RateLimitedError: If rate limited.
            OSError: On transport I/O error.
            TimeoutError: On call timeout.
        """
        if self._client is None:
            raise ConnectionError("Binance client is not connected")
        if self._used_weight >= self._weight_limit:
            raise _RateLimitedError("Binance request-weight limit exhausted")
        blocked = await self._circuit.before_call()
        if blocked is not None:
            raise _CircuitOpenError("Binance transport circuit is open")
        method = getattr(self._client, name)
        started = time.perf_counter()
        try:
            result = await asyncio.wait_for(
                method(**kwargs), timeout=self._config.request_timeout_sec
            )
        except TimeoutError, OSError, ConnectionError:
            await self._circuit.record_failure(BrokerErrorCode.BROKER_PROVIDER_ERROR)
            logger.warning("Binance transport call failed")
            raise
        finally:
            if self._latency_sink is not None:
                self._latency_sink((time.perf_counter() - started) * 1000.0)
        await self._circuit.record_success()
        response = getattr(self._client, "response", None)
        headers = getattr(response, "headers", {})
        used_weight = headers.get("X-MBX-USED-WEIGHT-1M") if headers else None
        if used_weight is not None:
            self._used_weight = int(used_weight)
        return result

    async def stream(
        self, name: str, **kwargs: object
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield one documented Binance websocket stream until cancellation.

        Args:
            name: Socket generator name.
            **kwargs: Stream parameters.

        Yields:
            Genuine provider websocket messages.

        Raises:
            ConnectionError: If not connected.
            _CircuitOpenError: If circuit is open.
        """
        if self._client is None:
            raise ConnectionError("Binance client is not connected")
        if await self._circuit.before_call() is not None:
            raise _CircuitOpenError("Binance stream circuit is open")
        if self._socket_manager is None:
            module = importlib.import_module("binance")
            self._socket_manager = module.BinanceSocketManager(self._client)
        factory = getattr(self._socket_manager, name)
        socket = factory(**kwargs)
        async with socket as receiver:
            while True:
                value = await asyncio.wait_for(
                    receiver.recv(), timeout=self._config.request_timeout_sec
                )
                await self._circuit.record_success()
                yield value

    async def close(self) -> None:
        """Close all owned REST/WebSocket client resources."""
        if self._client is not None:
            await self._client.close_connection()
            self._client = None
            self._socket_manager = None
            logger.info("Binance transport client resources released")
