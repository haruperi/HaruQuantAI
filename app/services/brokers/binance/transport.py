"""Bounded Binance Spot REST transport."""

# ruff: noqa: ANN401 - the optional SDK has a heterogeneous runtime payload surface.

import asyncio
import importlib
import time
from collections.abc import AsyncIterator, Callable
from typing import Any

from app.services.brokers.contracts import BrokerConnectionConfig, BrokerEnvironment
from app.services.brokers.runtime.circuit_breaker import _TransportCircuitBreaker
from app.utils import logger


class _BinanceTransport:
    """Own one python-binance client and close it deterministically."""

    def __init__(
        self,
        config: BrokerConnectionConfig,
        latency_sink: Callable[[float], None] | None = None,
    ) -> None:
        """Initialize the _BinanceTransport instance.

        Args:
            config: Immutable connection configuration for this session.
            latency_sink: Optional receiver for the measured milliseconds spent
                inside each provider REST call, used to separate provider
                latency from local adapter overhead.
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

    async def connect(self) -> bool:
        """Create a Spot client and verify ping plus server time.

        Returns:
            ``True`` after both probes succeed.
        """
        module = importlib.import_module("binance")
        credentials = self._config.credentials or {}
        api_key = credentials.get("api_key")
        api_secret = credentials.get("api_secret")
        self._client = await module.AsyncClient.create(
            api_key.get_secret_value() if api_key else None,
            api_secret.get_secret_value() if api_secret else None,
            testnet=self._config.environment == BrokerEnvironment.TESTNET,
        )
        await self.call("ping")
        await self.call("get_server_time")
        logger.bind(
            broker=self._config.broker_id.value,
            environment=self._config.environment.value,
            result="success",
        ).info("Binance transport client created and verified")
        return True

    async def call(self, name: str, **kwargs: object) -> Any:
        """Execute one bounded approved client call without replay.

        Returns:
            Exact provider SDK result.

        Raises:
            ConnectionError: If no client exists or the circuit is open.
            OSError: If provider transport fails.
            TimeoutError: If the configured request bound is exceeded.
        """
        if self._client is None:
            raise ConnectionError("Binance client is not connected")
        blocked = await self._circuit.before_call()
        if blocked is not None:
            raise ConnectionError(blocked.value)
        method = getattr(self._client, name)
        started = time.perf_counter()
        try:
            result = await asyncio.wait_for(
                method(**kwargs), timeout=self._config.request_timeout_sec
            )
        except (TimeoutError, OSError):
            from app.services.brokers.contracts import BrokerErrorCode

            await self._circuit.record_failure(BrokerErrorCode.BROKER_PROVIDER_ERROR)
            logger.bind(
                broker=self._config.broker_id.value,
                environment=self._config.environment.value,
                provider_call=name,
                result="error",
                provider_code=BrokerErrorCode.BROKER_PROVIDER_ERROR.value,
            ).warning("Binance transport call failed")
            raise
        finally:
            if self._latency_sink is not None:
                self._latency_sink((time.perf_counter() - started) * 1000.0)
        await self._circuit.record_success()
        return result

    async def stream(
        self, name: str, **kwargs: object
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield one documented Binance websocket stream until cancellation.

        Yields:
            Genuine provider websocket messages.

        Raises:
            ConnectionError: If the REST client session is not connected.
        """
        if self._client is None:
            raise ConnectionError("Binance client is not connected")
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
                yield value

    async def close(self) -> None:
        """Close all owned REST/WebSocket client resources."""
        if self._client is not None:
            await self._client.close_connection()
            self._client = None
            self._socket_manager = None
            logger.bind(
                broker=self._config.broker_id.value,
                environment=self._config.environment.value,
            ).info("Binance transport client resources released")
