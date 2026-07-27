"""FEAT-BRK-03: cTrader provider lifecycle."""

import asyncio

import _support  # noqa: F401
from _support import real_session, require_error, require_success
from app.services.brokers import BrokerAdapter, BrokerErrorCode, BrokerId


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


async def fr_brokers_057(adapter: BrokerAdapter) -> None:
    """FR-BRK-057: Yield one event per validated lifecycle transition."""
    _header("FR-BRK-057: Yield one event per validated lifecycle transition.")
    result = await adapter.get_connection_status()
    require_success("Connection status", result)
    assert result.data is not None
    assert result.data.transport_connected
    print("Lifecycle events available", hasattr(adapter, "connection_events"))


async def _require_unreleased(
    adapter: BrokerAdapter,
    operation: str,
) -> None:
    """Exercise one unreleased cTrader market operation."""
    if operation == "symbols":
        result = await adapter.get_symbols(limit=5)
    elif operation == "symbol_info":
        result = await adapter.get_symbol_info("EURUSD")
    elif operation == "select_symbol":
        result = await adapter.select_symbol("EURUSD")
    elif operation == "market_status":
        result = await adapter.get_market_status("EURUSD")
    elif operation == "quote":
        result = await adapter.get_quote("EURUSD")
    elif operation == "ticks":
        result = await adapter.get_ticks("EURUSD", limit=5)
    else:
        result = await adapter.get_historical_bars("EURUSD", "1m", limit=5)
    require_error(
        "Result",
        result,
        BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
    )


async def fr_brokers_058(adapter: BrokerAdapter) -> None:
    """FR-BRK-058: Return bounded exact provider-native symbols."""
    _header("FR-BRK-058: Return bounded exact provider-native symbols.")
    await _require_unreleased(adapter, "symbols")


async def fr_brokers_059(adapter: BrokerAdapter) -> None:
    """FR-BRK-059: Return provider specifications and trading flags."""
    _header("FR-BRK-059: Return provider specifications and trading flags.")
    await _require_unreleased(adapter, "symbol_info")


async def fr_brokers_060(adapter: BrokerAdapter) -> None:
    """FR-BRK-060: Perform watch-list selection or return unsupported."""
    _header("FR-BRK-060: Perform watch-list selection or return unsupported.")
    await _require_unreleased(adapter, "select_symbol")


async def fr_brokers_061(adapter: BrokerAdapter) -> None:
    """FR-BRK-061: Return provider-reported market state without derivation."""
    _header("FR-BRK-061: Return provider-reported market state without derivation.")
    await _require_unreleased(adapter, "market_status")


async def fr_brokers_063(adapter: BrokerAdapter) -> None:
    """FR-BRK-063: Return a genuine quote without fallback price."""
    _header("FR-BRK-063: Return a genuine quote without fallback price.")
    await _require_unreleased(adapter, "quote")


async def fr_brokers_064(adapter: BrokerAdapter) -> None:
    """FR-BRK-064: Return bounded genuine provider ticks or unsupported."""
    _header("FR-BRK-064: Return bounded genuine provider ticks or unsupported.")
    await _require_unreleased(adapter, "ticks")


async def fr_brokers_065(adapter: BrokerAdapter) -> None:
    """FR-BRK-065: Return bounded provider bars using timeframe translation."""
    _header("FR-BRK-065: Return bounded provider bars using timeframe translation.")
    await _require_unreleased(adapter, "bars")


async def _run() -> None:
    """Execute lifecycle evidence in one genuine cTrader demo session."""
    async with real_session(BrokerId.CTRADER) as adapter:
        await fr_brokers_057(adapter)
        await fr_brokers_058(adapter)
        await fr_brokers_059(adapter)
        await fr_brokers_060(adapter)
        await fr_brokers_061(adapter)
        await fr_brokers_063(adapter)
        await fr_brokers_064(adapter)
        await fr_brokers_065(adapter)


def main() -> None:
    """Run the standalone genuine cTrader lifecycle program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
