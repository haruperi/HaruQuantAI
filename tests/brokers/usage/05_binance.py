"""Demonstrate the Binance Spot adapter against the real Binance testnet.

No ``BINANCE_*`` credentials are configured in this repository's ``.env``,
but Binance's public market-data endpoints (exchange info, klines) do not
require authentication, so this script performs a genuine unauthenticated
connection to the real testnet REST API rather than a fixture.
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
from app.services.brokers.binance.adapter import BinanceBrokerAdapter


def _capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    return {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability="AVAILABLE",
            access_mode="READ",
            requirement="NONE",
            verification_status="TESTED_SANDBOX",
            execution_model="REAL_TESTNET_USAGE_EXAMPLE",
        )
        for operation in BrokerCapabilityId
    }


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.BINANCE_SPOT,
        environment=BrokerEnvironment.TESTNET,
        provider_enabled=True,
        connect_timeout_sec=15,
        request_timeout_sec=15,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=8,
        circuit_failure_threshold=3,
        circuit_recovery_timeout_sec=5,
        circuit_half_open_max_calls=1,
    )


def example_spot_adapter_connects_to_real_testnet() -> None:
    """Connect to the real Binance testnet and read genuine exchange data."""
    print("\n1. Real Binance Spot testnet connection")
    adapter = BinanceBrokerAdapter(_config(), _capabilities())

    async def exercise() -> None:
        connected = await adapter.connect()
        print("connect():", connected.status, connected.error)
        if not connected.is_success:
            raise AssertionError("real Binance testnet connect failed")

        symbols = await adapter.get_symbols(query="BTCUSDT", limit=5)
        if symbols.data is None or not symbols.data.items:
            raise AssertionError("no real symbols returned")
        print("Symbol:", symbols.data.items[0].provider_symbol)

        bars = await adapter.get_historical_bars("BTCUSDT", "1h", limit=3)
        if bars.data is None or not bars.data.items:
            raise AssertionError("no real klines returned")
        last_bar = bars.data.items[-1]
        print(
            "Last real BTCUSDT 1h bar:",
            "open=",
            last_bar.open,
            "close=",
            last_bar.close,
            "closing_timestamp=",
            last_bar.closing_timestamp,
        )
        await adapter.disconnect()

    asyncio.run(exercise())


if __name__ == "__main__":
    example_spot_adapter_connects_to_real_testnet()
