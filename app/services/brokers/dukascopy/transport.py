"""Bounded standard-library Dukascopy tick-file transport."""

# ruff: noqa: S310 - URL is constructed from a fixed HTTPS provider base.

from __future__ import annotations

import asyncio
import lzma
import urllib.request
from datetime import datetime
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from app.services.brokers.contracts import BrokerConnectionConfig
from app.services.brokers.runtime.circuit_breaker import _TransportCircuitBreaker
from app.utils import logger


class _DukascopyTransport:
    """Retrieve one bounded provider hour file without retry fan-out."""

    _BASE_URL = "https://datafeed.dukascopy.com/datafeed"

    def __init__(self, config: BrokerConnectionConfig) -> None:
        self._config = config
        self._circuit = _TransportCircuitBreaker(
            failure_threshold=config.circuit_failure_threshold,
            recovery_timeout_sec=config.circuit_recovery_timeout_sec,
            half_open_max_calls=config.circuit_half_open_max_calls,
        )

    async def get_hour(self, symbol: str, hour: datetime) -> bytes:
        """Retrieve and decompress exactly one provider BI5 hour file."""
        blocked = await self._circuit.before_call()
        if blocked is not None:
            raise ConnectionError(blocked.value)
        url = (
            f"{self._BASE_URL}/{symbol}/{hour.year}/"
            f"{hour.month - 1:02d}/{hour.day:02d}/{hour.hour:02d}h_ticks.bi5"
        )

        def _read() -> bytes:
            request = urllib.request.Request(url, headers={"User-Agent": "HaruQuantAI"})
            with urllib.request.urlopen(
                request, timeout=self._config.request_timeout_sec
            ) as response:
                return cast("bytes", response.read())

        try:
            compressed = await asyncio.wait_for(
                asyncio.to_thread(_read), timeout=self._config.request_timeout_sec
            )
            payload = lzma.decompress(compressed)
        except (TimeoutError, OSError, lzma.LZMAError):
            from app.services.brokers.contracts import BrokerErrorCode

            await self._circuit.record_failure(BrokerErrorCode.BROKER_PROVIDER_ERROR)
            logger.bind(
                broker=self._config.broker_id.value,
                environment=self._config.environment.value,
                symbol=symbol,
                result="error",
                provider_code=BrokerErrorCode.BROKER_PROVIDER_ERROR.value,
            ).warning("Dukascopy hour-file transport call failed")
            raise
        await self._circuit.record_success()
        logger.bind(
            broker=self._config.broker_id.value,
            environment=self._config.environment.value,
            symbol=symbol,
            result="success",
        ).info("Dukascopy hour-file transport call completed")
        return payload
