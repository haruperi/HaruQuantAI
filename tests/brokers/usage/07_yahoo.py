"""Demonstrate the Yahoo adapter against the real Yahoo Finance service.

Performs genuine ``yfinance`` calls — no fixtures — for both the
no-probe-symbol connect path and the configured-probe-symbol path
(``DEC-BRK-001``), then reads real historical bars for a real symbol.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
)
from app.services.brokers.yahoo.adapter import YahooBrokerAdapter


def _capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    return {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability="AVAILABLE",
            access_mode="READ",
            requirement="NONE",
            verification_status="TESTED_SANDBOX",
            execution_model="REAL_USAGE_EXAMPLE",
        )
        for operation in BrokerCapabilityId
    }


def _config(*, probe_symbol: str | None) -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.YAHOO,
        environment=BrokerEnvironment.SANDBOX,
        provider_enabled=True,
        connect_timeout_sec=15,
        request_timeout_sec=15,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=8,
        circuit_failure_threshold=3,
        circuit_recovery_timeout_sec=5,
        circuit_half_open_max_calls=1,
        probe_symbol=probe_symbol,
    )


def example_connect_without_probe_symbol() -> None:
    """Connect with no probe symbol: transport/session verification only."""
    print("\n1. connect() without a probe symbol (transport-only verification)")
    adapter = YahooBrokerAdapter(_config(probe_symbol=None), _capabilities())

    async def exercise() -> None:
        result = await adapter.connect()
        print("connect():", result.status, result.error)
        if not result.is_success:
            raise AssertionError("connect without a probe symbol should succeed")

    asyncio.run(exercise())


def example_connect_with_real_probe_symbol() -> None:
    """Connect with a real probe symbol: a genuine one-row history call."""
    print("\n2. connect() with a real probe symbol (DEC-BRK-001)")
    adapter = YahooBrokerAdapter(_config(probe_symbol="AAPL"), _capabilities())

    async def exercise() -> None:
        result = await adapter.connect()
        print("connect() with probe_symbol='AAPL':", result.status, result.error)
        if not result.is_success:
            raise AssertionError("real Yahoo probe failed")

    asyncio.run(exercise())


def example_get_real_historical_bars() -> None:
    """Read genuine historical bars for a real symbol."""
    print("\n3. Reading real AAPL historical bars")
    adapter = YahooBrokerAdapter(_config(probe_symbol=None), _capabilities())

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_historical_bars("AAPL", "1d", limit=3)
        if result.data is None or not result.data.items:
            raise AssertionError("no real bars returned")
        last_bar = result.data.items[-1]
        print(
            "Last real AAPL daily bar:",
            "open=",
            last_bar.open,
            "close=",
            last_bar.close,
            "opening_timestamp=",
            last_bar.opening_timestamp,
            "closing_timestamp=",
            last_bar.closing_timestamp,
        )
        if last_bar.opening_timestamp >= last_bar.closing_timestamp:
            raise AssertionError("bar did not close after it opened")

    asyncio.run(exercise())


if __name__ == "__main__":
    example_connect_without_probe_symbol()
    example_connect_with_real_probe_symbol()
    example_get_real_historical_bars()
