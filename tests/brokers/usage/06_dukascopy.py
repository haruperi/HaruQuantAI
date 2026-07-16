"""Demonstrate the Dukascopy adapter against the real datafeed.dukascopy.com.

No credentials are required, but this attempts a genuine bounded HTTP/LZMA
fetch of one real hourly tick file — no fixture. This host is slow or
unreachable from some networks; if the real request fails, this script
prints the real error rather than fabricating a successful result.
"""

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
)
from app.services.brokers.dukascopy.adapter import DukascopyBrokerAdapter


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


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.DUKASCOPY,
        environment=BrokerEnvironment.SANDBOX,
        provider_enabled=True,
        connect_timeout_sec=20,
        request_timeout_sec=20,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=4,
        circuit_failure_threshold=3,
        circuit_recovery_timeout_sec=5,
        circuit_half_open_max_calls=1,
    )


def example_connect_and_read_real_ticks() -> None:
    """Attempt a genuine bounded EURUSD tick-file fetch."""
    print("\n1. Real Dukascopy connect + bounded tick read")
    adapter = DukascopyBrokerAdapter(_config(), _capabilities())

    async def exercise() -> None:
        connected = await adapter.connect()
        print("connect():", connected.status, connected.error)
        if not connected.is_success:
            print(
                "Real Dukascopy probe failed (host unreachable/slow from this "
                "network) — reporting the real outcome, not fabricating success."
            )
            return
        hour = datetime.now(UTC) - timedelta(hours=3)
        ticks = await adapter.get_ticks("EURUSD", start=hour, limit=5)
        if ticks.data is None:
            raise AssertionError("connect succeeded but tick read returned no data")
        print(f"Real EURUSD ticks retrieved: {len(ticks.data.items)}")
        for tick in ticks.data.items[:3]:
            print("  bid=", tick.bid, "ask=", tick.ask, "at=", tick.event_timestamp)

    asyncio.run(exercise())


if __name__ == "__main__":
    example_connect_and_read_real_ticks()
