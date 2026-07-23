"""FEAT-BRK-13: exercise Dukascopy web-chart candle retrieval.

Runs the genuine `DukascopyBrokerAdapter` over offline transports serving recorded
BI5 connectivity evidence and web-chart BID candle rows.
"""

import asyncio
from datetime import UTC, datetime

from _support import (
    OfflineDukascopyCandleTransport,
    OfflineDukascopyTransport,
    available_capabilities,
    config,
    show,
    show_value,
    unavailable_capabilities,
)
from app.services.brokers import BrokerId, DukascopyBrokerAdapter

_START = datetime(2026, 1, 1, tzinfo=UTC)
_END = datetime(2026, 1, 1, 0, 5, tzinfo=UTC)


async def example_deterministic_candle_mapping() -> None:
    """Genuine provider candles map into bounded UTC bars with provenance."""
    transport = OfflineDukascopyTransport()
    candle_transport = OfflineDukascopyCandleTransport()
    adapter = DukascopyBrokerAdapter(
        config(BrokerId.DUKASCOPY),
        available_capabilities(),
        transport=transport,
        candle_transport=candle_transport,
    )
    await adapter.connect()

    bars = await adapter.get_historical_bars("EURUSD", "M1", _START, _END, limit=5)
    show_value(
        "bars",
        bars,
        f"count={bars.data.returned_count}" if bars.data else None,
    )
    if bars.data:
        for bar in bars.data.items:
            print(
                "  bar",
                bar.opening_timestamp.isoformat(),
                f"o={bar.open} h={bar.high} l={bar.low} c={bar.close}",
                f"closed={bar.is_closed}",
            )
        print("  provider provenance", dict(bars.data.provider_metadata))

    # Provider-candle mapping is deterministic for identical input rows.
    repeated = await adapter.get_historical_bars("EURUSD", "M1", _START, _END, limit=5)
    identical = (
        repeated.data is not None
        and bars.data is not None
        and all(
            left.open == right.open and left.close == right.close
            for left, right in zip(bars.data.items, repeated.data.items, strict=True)
        )
    )
    print("deterministic across repeated calls", identical)
    print("candle pages requested", len(candle_transport.requested))


async def example_unsupported_timeframe_is_explicit() -> None:
    """An unsupported provider timeframe fails closed, never silently."""
    adapter = DukascopyBrokerAdapter(
        config(BrokerId.DUKASCOPY),
        available_capabilities(),
        transport=OfflineDukascopyTransport(),
        candle_transport=OfflineDukascopyCandleTransport(),
    )
    await adapter.connect()
    show(
        "unsupported-timeframe",
        await adapter.get_historical_bars("EURUSD", "M7", _START, _END, limit=1),
    )


async def example_bars_remain_gated() -> None:
    """A gated candle read returns unsupported without retrieving any page."""
    transport = OfflineDukascopyTransport()
    candle_transport = OfflineDukascopyCandleTransport()
    adapter = DukascopyBrokerAdapter(
        config(BrokerId.DUKASCOPY),
        unavailable_capabilities(),
        transport=transport,
        candle_transport=candle_transport,
    )
    show(
        "gated-bars",
        await adapter.get_historical_bars("EURUSD", "M1", _START, _END, limit=1),
    )
    print("candle pages while gated", len(candle_transport.requested))


async def main() -> None:
    """Exercise every FEAT-BRK-13 operation offline."""
    await example_deterministic_candle_mapping()
    await example_unsupported_timeframe_is_explicit()
    await example_bars_remain_gated()


if __name__ == "__main__":
    asyncio.run(main())
