"""FEAT-BRK-12: exercise the cTrader market-data read surface.

Runs the genuine `CTraderBrokerAdapter` over an offline sender so real protobuf
decoding, symbol specification mapping, tick/trendbar translation, and provider
spread derivation execute without Spotware network traffic.
"""

import asyncio
from datetime import UTC, datetime

from _support import (
    OfflineCTraderTransport,
    available_capabilities,
    config,
    show,
    show_value,
    unavailable_capabilities,
)
from app.services.brokers import BrokerId, CTraderBrokerAdapter

_START = datetime(2023, 11, 14, tzinfo=UTC)
_END = datetime(2023, 11, 15, tzinfo=UTC)


async def example_market_data_reads() -> None:
    """Every accepted cTrader read maps genuine decoded provider truth."""
    transport = OfflineCTraderTransport()
    adapter = CTraderBrokerAdapter(
        config(BrokerId.CTRADER), available_capabilities(), transport=transport
    )
    await adapter.connect()

    symbols = await adapter.get_symbols(limit=5)
    show_value(
        "symbols",
        symbols,
        tuple(item.provider_symbol for item in symbols.data.items)
        if symbols.data
        else None,
    )

    info = await adapter.get_symbol_info("EURUSD")
    show_value(
        "symbol-info",
        info,
        f"digits={info.data.price_precision}" if info.data else None,
    )

    quote = await adapter.get_quote("EURUSD")
    show_value(
        "quote",
        quote,
        f"bid={quote.data.bid} ask={quote.data.ask}" if quote.data else None,
    )

    spread = await adapter.get_spread("EURUSD")
    show_value("spread", spread, spread.data)

    ticks = await adapter.get_ticks("EURUSD", _START, _END, limit=5)
    show_value(
        "ticks",
        ticks,
        f"count={ticks.data.returned_count}" if ticks.data else None,
    )

    bars = await adapter.get_historical_bars("EURUSD", "M1", _START, _END, limit=5)
    show_value(
        "bars",
        bars,
        f"close={bars.data.items[0].close} count={bars.data.returned_count}"
        if bars.data
        else None,
    )
    print("provider requests", len(transport.requests))


async def example_unsupported_timeframe_never_falls_back() -> None:
    """An unsupported timeframe fails explicitly and never becomes H1."""
    adapter = CTraderBrokerAdapter(
        config(BrokerId.CTRADER),
        available_capabilities(),
        transport=OfflineCTraderTransport(),
    )
    await adapter.connect()
    show(
        "unsupported-timeframe",
        await adapter.get_historical_bars("EURUSD", "M7", _START, _END, limit=1),
    )


async def example_reads_remain_gated() -> None:
    """A gated read returns unsupported without a provider request."""
    transport = OfflineCTraderTransport()
    adapter = CTraderBrokerAdapter(
        config(BrokerId.CTRADER), unavailable_capabilities(), transport=transport
    )
    show("gated-quote", await adapter.get_quote("EURUSD"))
    print("provider requests while gated", len(transport.requests))


async def main() -> None:
    """Exercise every FEAT-BRK-12 operation offline."""
    await example_market_data_reads()
    await example_unsupported_timeframe_never_falls_back()
    await example_reads_remain_gated()


if __name__ == "__main__":
    asyncio.run(main())
