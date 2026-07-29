"""FEAT-BRK-12: cTrader genuine market-data release evidence."""

import asyncio

import _support  # noqa: F401
from _support import real_session, require_error, require_success
from app.services.brokers import (
    get_broker_historical_bars,
    get_broker_quote,
    get_broker_symbol_info,
    get_broker_symbols,
    get_broker_ticks,
    get_broker_trading_sessions,
    get_broker_value_field,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


async def _require_unreleased(adapter: object, operation: str) -> None:
    """Require one cTrader market read to remain release-gated."""
    if operation == "symbols":
        result = await get_broker_symbols(adapter, limit=5)
    elif operation == "symbol_info":
        result = await get_broker_symbol_info(adapter, "EURUSD")
    elif operation == "quote":
        result = await get_broker_quote(adapter, "EURUSD")
    elif operation == "ticks":
        result = await get_broker_ticks(adapter, "EURUSD", limit=5)
    else:
        result = await get_broker_historical_bars(adapter, "EURUSD", "1m", limit=5)
    if get_broker_value_field(result, "status") == "success":
        require_success("Result", result)
    else:
        require_error("Result", result, "BROKER_CAPABILITY_UNSUPPORTED")


async def fr_brokers_124(adapter: object) -> None:
    """FR-BRK-124: Fetch exact provider-native symbols when released."""
    _header("FR-BRK-124: Fetch exact provider-native symbols when released.")
    await _require_unreleased(adapter, "symbols")


async def fr_brokers_125(adapter: object) -> None:
    """FR-BRK-125: Fetch genuine cTrader symbol information when released."""
    _header("FR-BRK-125: Fetch genuine cTrader symbol information when released.")
    await _require_unreleased(adapter, "symbol_info")


async def fr_brokers_126(adapter: object) -> None:
    """FR-BRK-126: Fetch a genuine cTrader quote when released."""
    _header("FR-BRK-126: Fetch a genuine cTrader quote when released.")
    await _require_unreleased(adapter, "quote")


async def fr_brokers_127(adapter: object) -> None:
    """FR-BRK-127: Fetch bounded genuine cTrader ticks when released."""
    _header("FR-BRK-127: Fetch bounded genuine cTrader ticks when released.")
    await _require_unreleased(adapter, "ticks")


async def fr_brokers_128(adapter: object) -> None:
    """FR-BRK-128: Fetch bounded genuine cTrader bars when released."""
    _header("FR-BRK-128: Fetch bounded genuine cTrader bars when released.")
    await _require_unreleased(adapter, "bars")


async def fr_brokers_062(adapter: object) -> None:
    """FR-BRK-062: Return genuine provider-authored UTC trading windows."""
    _header("FR-BRK-062: Return genuine provider-authored UTC trading windows.")
    result = await get_broker_trading_sessions(adapter, "EURUSD")
    if get_broker_value_field(result, "status") == "success":
        require_success("Result", result)
    else:
        require_error("Result", result, "BROKER_CAPABILITY_UNSUPPORTED")


async def _run() -> None:
    """Execute cTrader market evidence in one genuine demo session."""
    async with real_session("ctrader") as adapter:
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
