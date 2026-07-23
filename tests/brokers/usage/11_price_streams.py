"""FEAT-BRK-11: exercise bounded provider price-stream subscriptions.

Runs the genuine `BinanceBrokerAdapter` over an offline websocket transport, so
subscription creation, canonical event mapping, bounded FIFO delivery,
backpressure termination, and deterministic unsubscribe all execute for real.
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
from app.services.brokers import BinanceBrokerAdapter, BrokerError, BrokerId


async def example_bounded_quote_stream() -> None:
    """A subscription yields canonical quotes and is released deterministically."""
    transport = OfflineBinanceTransport(message_count=1)
    adapter = BinanceBrokerAdapter(
        config(BrokerId.BINANCE_SPOT), available_capabilities(), transport=transport
    )
    await adapter.connect()

    opened = await adapter.subscribe_quotes(("BTCUSDT",))
    handle = opened.data
    show_value(
        "subscribe",
        opened,
        f"buffer={handle.info.buffer_size} symbols={handle.info.symbols}"
        if handle
        else None,
    )
    if handle is None:
        return

    event = await asyncio.wait_for(anext(handle.events()), timeout=2)
    print("first event bid", getattr(event, "bid", None))

    listed = await adapter.list_subscriptions()
    show_value("list", listed, f"open={len(listed.data or ())}")
    show("unsubscribe", await adapter.unsubscribe(handle.info.subscription_id))


async def example_overflow_is_terminal_and_requires_resync() -> None:
    """Buffer overflow ends the stream explicitly; silent drops are forbidden."""
    transport = OfflineBinanceTransport(message_count=8)
    adapter = BinanceBrokerAdapter(
        config(BrokerId.BINANCE_SPOT), available_capabilities(), transport=transport
    )
    await adapter.connect()
    opened = await adapter.subscribe_quotes(("BTCUSDT",))
    handle = opened.data
    if handle is None:
        return

    for _ in range(40):
        await asyncio.sleep(0)
    terminal = None
    async for event in handle.events():
        if isinstance(event, BrokerError):
            terminal = event
            break
    print("terminal event", terminal.code.value if terminal else None)
    print("resynchronization required", handle.info.resynchronization_required)


async def example_unknown_subscription_is_isolated() -> None:
    """An unowned subscription identifier never disturbs an owned stream."""
    adapter = BinanceBrokerAdapter(
        config(BrokerId.BINANCE_SPOT),
        available_capabilities(),
        transport=OfflineBinanceTransport(),
    )
    await adapter.connect()
    await adapter.subscribe_quotes(("BTCUSDT",))
    show("unsubscribe-unknown", await adapter.unsubscribe("evt-does-not-exist"))
    listed = await adapter.list_subscriptions()
    print("still open", len(listed.data or ()))


async def example_streams_remain_gated() -> None:
    """A gated subscription returns unsupported without a provider stream."""
    transport = OfflineBinanceTransport()
    adapter = BinanceBrokerAdapter(
        config(BrokerId.BINANCE_SPOT), unavailable_capabilities(), transport=transport
    )
    show("gated-subscribe", await adapter.subscribe_quotes(("BTCUSDT",)))
    print("provider calls while gated", len(transport.calls))


async def main() -> None:
    """Exercise every FEAT-BRK-11 operation offline."""
    await example_bounded_quote_stream()
    await example_overflow_is_terminal_and_requires_resync()
    await example_unknown_subscription_is_isolated()
    await example_streams_remain_gated()


if __name__ == "__main__":
    asyncio.run(main())
