"""FEAT-BRK-05: exercise the Dukascopy lifecycle and tick-read surface.

Runs the genuine `DukascopyBrokerAdapter` over an offline transport serving
recorded BI5 hour files, so real instrument validation, BI5 decoding, and
canonical tick mapping execute without provider network traffic.
"""

import asyncio
from datetime import UTC, datetime

from _support import (
    OfflineDukascopyTransport,
    available_capabilities,
    config,
    show,
    show_value,
    unavailable_capabilities,
)
from app.services.brokers import BrokerId, DukascopyBrokerAdapter


async def example_verified_lifecycle_and_tick_reads() -> None:
    """Connect, list provider-native symbols, and read genuine mapped ticks."""
    transport = OfflineDukascopyTransport()
    adapter = DukascopyBrokerAdapter(
        config(BrokerId.DUKASCOPY), available_capabilities(), transport=transport
    )
    show("connect", await adapter.connect())

    symbols = await adapter.get_symbols(limit=5)
    show_value(
        "symbols",
        symbols,
        tuple(item.provider_symbol for item in symbols.data.items)
        if symbols.data
        else None,
    )

    ticks = await adapter.get_ticks(
        "EURUSD",
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 1, 1, tzinfo=UTC),
        limit=3,
    )
    show_value(
        "ticks",
        ticks,
        f"count={ticks.data.returned_count} first_bid={ticks.data.items[0].bid}"
        if ticks.data
        else None,
    )

    show("disconnect", await adapter.disconnect())
    print("hour files requested", len(transport.requested))


async def example_undeclared_symbol_is_rejected() -> None:
    """Only exact declared provider-native instruments are accepted."""
    adapter = DukascopyBrokerAdapter(
        config(BrokerId.DUKASCOPY),
        available_capabilities(),
        transport=OfflineDukascopyTransport(),
    )
    show(
        "undeclared-symbol",
        await adapter.get_ticks(
            "NOT_A_SYMBOL",
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 1, 1, tzinfo=UTC),
            limit=1,
        ),
    )


async def example_unreleased_capability_fails_closed() -> None:
    """A gated capability returns unsupported without a provider call."""
    transport = OfflineDukascopyTransport()
    adapter = DukascopyBrokerAdapter(
        config(BrokerId.DUKASCOPY), unavailable_capabilities(), transport=transport
    )
    show("gated-symbols", await adapter.get_symbols(limit=1))
    print("hour files while gated", len(transport.requested))


async def main() -> None:
    """Exercise every FEAT-BRK-05 operation offline."""
    await example_verified_lifecycle_and_tick_reads()
    await example_undeclared_symbol_is_rejected()
    await example_unreleased_capability_fails_closed()


if __name__ == "__main__":
    asyncio.run(main())
