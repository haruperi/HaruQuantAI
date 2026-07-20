"""Bounded yfinance history transport without direct pandas imports."""

# ruff: noqa: ANN401 - yfinance returns a transitive table without a stable type.

from __future__ import annotations

import asyncio
import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.brokers.contracts import BrokerConnectionConfig
from app.services.brokers.runtime.circuit_breaker import _TransportCircuitBreaker
from app.utils import logger


class _YahooTransport:
    """Run one bounded yfinance history call off the event loop."""

    def __init__(self, config: BrokerConnectionConfig) -> None:
        """Initialize the _YahooTransport instance.

        Args:
            config: Value supplied to the operation.
        """
        self._config = config
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
            OSError: If provider transport fails.
            TimeoutError: If the configured request bound is exceeded.
        """
        blocked = await self._circuit.before_call()
        if blocked is not None:
            raise ConnectionError(blocked.value)

        def _history() -> Any:
            """Handle history.

            Returns:
                The operation result.
            """
            yfinance = importlib.import_module("yfinance")
            ticker = yfinance.Ticker(symbol)
            return ticker.history(interval=timeframe, start=start, end=end)

        try:
            value = await asyncio.wait_for(
                asyncio.to_thread(_history), timeout=self._config.request_timeout_sec
            )
        except (TimeoutError, OSError):
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
        await self._circuit.record_success()
        logger.bind(
            broker=self._config.broker_id.value,
            environment=self._config.environment.value,
            symbol=symbol,
            timeframe=timeframe,
            result="success",
        ).info("Yahoo history transport call completed")
        return value
