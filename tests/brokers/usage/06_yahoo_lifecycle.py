"""FEAT-BRK-06: exercise the Yahoo lifecycle and historical-bar surface.

Runs the genuine `YahooBrokerAdapter` over an offline transport returning a
recorded public table, so the probe-symbol connect gate (`DEC-BRK-001`) and the
real bar mapping execute without provider network traffic.
"""

import asyncio

from _support import (
    OfflineYahooTransport,
    available_capabilities,
    config,
    show,
    show_value,
    unavailable_capabilities,
)
from app.services.brokers import (
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    YahooBrokerAdapter,
)


async def example_probe_verified_lifecycle_and_bars() -> None:
    """Connect with the configured probe symbol and read genuine mapped bars."""
    transport = OfflineYahooTransport()
    adapter = YahooBrokerAdapter(
        config(BrokerId.YAHOO), available_capabilities(), transport=transport
    )
    show("connect", await adapter.connect())

    bars = await adapter.get_historical_bars("AAPL", "1d", limit=1)
    bar = bars.data.items[0] if bars.data else None
    show_value(
        "bars",
        bars,
        f"open={bar.open} close={bar.close} "
        f"span={bar.closing_timestamp - bar.opening_timestamp}"
        if bar
        else None,
    )

    show("disconnect", await adapter.disconnect())
    print("probe/history symbols", transport.requested)


async def example_missing_probe_symbol_fails_closed() -> None:
    """Without an explicit probe symbol, connect never assumes a default."""
    transport = OfflineYahooTransport()
    unconfigured = BrokerConnectionConfig(
        broker_id=BrokerId.YAHOO,
        environment=BrokerEnvironment.SANDBOX,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=4,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
    )
    adapter = YahooBrokerAdapter(
        unconfigured, available_capabilities(), transport=transport
    )
    show("connect-without-probe", await adapter.connect())
    print("provider calls without a probe symbol", len(transport.requested))


async def example_unreleased_capability_fails_closed() -> None:
    """A gated capability returns unsupported without a provider call."""
    transport = OfflineYahooTransport()
    adapter = YahooBrokerAdapter(
        config(BrokerId.YAHOO), unavailable_capabilities(), transport=transport
    )
    show("gated-bars", await adapter.get_historical_bars("AAPL", "1d", limit=1))
    print("provider calls while gated", len(transport.requested))


async def main() -> None:
    """Exercise every FEAT-BRK-06 operation offline."""
    await example_probe_verified_lifecycle_and_bars()
    await example_missing_probe_symbol_fails_closed()
    await example_unreleased_capability_fails_closed()


if __name__ == "__main__":
    asyncio.run(main())
