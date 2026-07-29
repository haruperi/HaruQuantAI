"""FEAT-BRK-12: cTrader genuine market-data release evidence."""

import asyncio

import _support  # noqa: F401
from _support import real_session, require_error, require_success
from app.services.brokers.contracts import BrokerAdapter, BrokerErrorCode, BrokerId


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


async def _require_unreleased(adapter: BrokerAdapter, operation: str) -> None:
    """Require one cTrader market read to remain release-gated."""
    if operation == "symbols":
        result = await adapter.get_symbols(limit=5)
    elif operation == "symbol_info":
        result = await adapter.get_symbol_info("EURUSD")
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


async def fr_brokers_124(adapter: BrokerAdapter) -> None:
    """FR-BRK-124: Fetch exact provider-native symbols when released."""
    _header("FR-BRK-124: Fetch exact provider-native symbols when released.")
    await _require_unreleased(adapter, "symbols")


async def fr_brokers_125(adapter: BrokerAdapter) -> None:
    """FR-BRK-125: Fetch genuine cTrader symbol information when released."""
    _header("FR-BRK-125: Fetch genuine cTrader symbol information when released.")
    await _require_unreleased(adapter, "symbol_info")


async def fr_brokers_126(adapter: BrokerAdapter) -> None:
    """FR-BRK-126: Fetch a genuine cTrader quote when released."""
    _header("FR-BRK-126: Fetch a genuine cTrader quote when released.")
    await _require_unreleased(adapter, "quote")


async def fr_brokers_127(adapter: BrokerAdapter) -> None:
    """FR-BRK-127: Fetch bounded genuine cTrader ticks when released."""
    _header("FR-BRK-127: Fetch bounded genuine cTrader ticks when released.")
    await _require_unreleased(adapter, "ticks")


async def fr_brokers_128(adapter: BrokerAdapter) -> None:
    """FR-BRK-128: Fetch bounded genuine cTrader bars when released."""
    _header("FR-BRK-128: Fetch bounded genuine cTrader bars when released.")
    await _require_unreleased(adapter, "bars")


async def fr_brokers_062(adapter: BrokerAdapter) -> None:
    """FR-BRK-062: Return genuine provider-authored UTC trading windows."""
    _header("FR-BRK-062: Return genuine provider-authored UTC trading windows.")
    result = await adapter.get_trading_sessions("EURUSD")
    require_success("Result", result)
    assert result.data is not None
    print("Session count", len(result.data))


async def _run() -> None:
    """Execute cTrader market evidence in one genuine demo session."""
    async with real_session(BrokerId.CTRADER) as adapter:
        await fr_brokers_124(adapter)
        await fr_brokers_125(adapter)
        await fr_brokers_126(adapter)
        await fr_brokers_127(adapter)
        await fr_brokers_128(adapter)
        await fr_brokers_062(adapter)


def main() -> None:
    """Run the standalone genuine cTrader market-data program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
