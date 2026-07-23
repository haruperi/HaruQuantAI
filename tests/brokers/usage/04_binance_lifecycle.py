"""FEAT-BRK-04: exercise the Binance Spot lifecycle and market-data surface.

Runs the genuine `BinanceBrokerAdapter` over an offline REST transport, so the
real ping/server-time verification and Spot payload mapping execute without
network traffic or credentials.
"""

import asyncio

from _support import (
    OfflineBinanceTransport,
    available_capabilities,
    config,
    show,
    show_value,
    unavailable_capabilities,
)
from app.services.brokers import BinanceBrokerAdapter, BrokerId


async def example_verified_lifecycle_and_market_data() -> None:
    """Connect, read genuine mapped Spot observations, and disconnect."""
    transport = OfflineBinanceTransport()
    adapter = BinanceBrokerAdapter(
        config(BrokerId.BINANCE_SPOT), available_capabilities(), transport=transport
    )
    show("connect", await adapter.connect())

    server_time = await adapter.get_server_time()
    show_value(
        "server-time",
        server_time,
        server_time.data.provider_time.isoformat() if server_time.data else None,
    )

    quote = await adapter.get_quote("BTCUSDT")
    show_value(
        "quote",
        quote,
        f"bid={quote.data.bid} ask={quote.data.ask}" if quote.data else None,
    )

    spread = await adapter.get_spread("BTCUSDT")
    show_value("spread", spread, spread.data)

    bars = await adapter.get_historical_bars("BTCUSDT", "1m", limit=1)
    show_value(
        "bars",
        bars,
        f"close={bars.data.items[0].close} count={bars.data.returned_count}"
        if bars.data
        else None,
    )

    show("disconnect", await adapter.disconnect())
    print("provider calls", len(transport.calls))


async def example_unreleased_capability_fails_closed() -> None:
    """A gated capability returns unsupported without a provider call."""
    transport = OfflineBinanceTransport()
    adapter = BinanceBrokerAdapter(
        config(BrokerId.BINANCE_SPOT), unavailable_capabilities(), transport=transport
    )
    show("gated-quote", await adapter.get_quote("BTCUSDT"))
    print("provider calls while gated", len(transport.calls))


async def main() -> None:
    """Exercise every FEAT-BRK-04 operation offline."""
    await example_verified_lifecycle_and_market_data()
    await example_unreleased_capability_fails_closed()


if __name__ == "__main__":
    asyncio.run(main())
