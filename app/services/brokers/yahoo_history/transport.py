"""Bounded yfinance history transport without direct pandas imports."""

# ruff: noqa: ANN401 - yfinance returns a transitive table without a stable type.

from __future__ import annotations

import asyncio
import importlib
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.brokers.contracts import BrokerConnectionConfig
from app.services.brokers.adapter_runtime.circuit_breaker import (
    _TransportCircuitBreaker,
)
from app.services.brokers.contracts.protocols import _CircuitOpenError
from app.utils import logger


class _YahooTransport:
    """Run one bounded yfinance history call off the event loop."""

    def __init__(
        self,
        config: BrokerConnectionConfig,
        latency_sink: Callable[[float], None] | None = None,
    ) -> None:
        """Initialize the _YahooTransport instance.

        Args:
            config: Immutable connection configuration for this session.
            latency_sink: Optional receiver for the measured milliseconds spent
                inside each provider history call, used to separate provider
                latency from local adapter overhead.
        """
        self._config = config
        self._latency_sink = latency_sink
        self._circuit = _TransportCircuitBreaker(
            failure_threshold=config.circuit_failure_threshold,
            recovery_timeout_sec=config.circuit_recovery_timeout_sec,
            half_open_max_calls=config.circuit_half_open_max_calls,
        )

    async def history(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: object | None,
        end: object | None,
    ) -> Any:
        """Return the public table object produced by one yfinance call.

        Returns:
            Exact public table produced by yfinance.

        Raises:
            ConnectionError: If the transport circuit is open.
            _CircuitOpenError: If the circuit rejects the request.
            OSError: If provider transport fails.
            TimeoutError: If the configured request bound is exceeded.
        """
        blocked = await self._circuit.before_call()
        if blocked is not None:
            raise _CircuitOpenError(
                "BROKER_CIRCUIT_OPEN: Yahoo transport circuit is open"
            )

        def _history() -> Any:
            """Handle history.

            Returns:
                The operation result.
            """
            yfinance = importlib.import_module("yfinance")
            ticker = yfinance.Ticker(symbol)
            return ticker.history(
                interval=timeframe,
                start=start,
                end=end,
                timeout=self._config.request_timeout_sec,
            )

        started = time.perf_counter()
        try:
            value = await asyncio.wait_for(
                asyncio.to_thread(_history), timeout=self._config.request_timeout_sec
            )
        except TimeoutError, OSError:
            from app.services.brokers.contracts import BrokerErrorCode

            await self._circuit.record_failure(BrokerErrorCode.BROKER_PROVIDER_ERROR)
            logger.bind(
                broker=self._config.broker_id.value,
                environment=self._config.environment.value,
                symbol=symbol,
                timeframe=timeframe,
                result="error",
                provider_code=BrokerErrorCode.BROKER_PROVIDER_ERROR.value,
            ).warning("Yahoo history transport call failed")
            raise
        finally:
            if self._latency_sink is not None:
                self._latency_sink((time.perf_counter() - started) * 1000.0)
        await self._circuit.record_success()
        logger.bind(
            broker=self._config.broker_id.value,
            environment=self._config.environment.value,
            symbol=symbol,
            timeframe=timeframe,
            result="success",
        ).info("Yahoo history transport call completed")
        return value
