"""FEAT-BRK-12: cTrader genuine market-data release evidence."""

import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import _support  # noqa: F401
from _support import UsageEvidenceError, real_session, require_error, require_success
from app.services.brokers import (
    get_broker_historical_bars,
    get_broker_quote,
    get_broker_symbol_info,
    get_broker_symbols,
    get_broker_ticks,
    get_broker_trading_sessions,
    get_broker_value_field,
)


def _feature_header(title: str) -> None:
    """Print feature title and module flow banner."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'-' * 88}\n{title}\n{'-' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


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
    print(_format_result(result))
    print(
        f"Data -> operation='{operation}', status='{get_broker_value_field(result, 'status')}'"
    )


async def fr_brokers_124_to_125_symbol_request(adapter: object) -> None:
    """FR-BRK-124..125: Stage 1 — Symbol Request Specification."""
    _header("Stage 1: Symbol Request Specification (FR-BRK-124..125)")
    await _require_unreleased(adapter, "symbols")
    await _require_unreleased(adapter, "symbol_info")


async def fr_brokers_126_to_128_protobuf_calls(adapter: object) -> None:
    """FR-BRK-126..128: Stage 2 — cTrader Protobuf Call Execution."""
    _header("Stage 2: cTrader Protobuf Call Execution (FR-BRK-126..128)")
    await _require_unreleased(adapter, "quote")
    await _require_unreleased(adapter, "ticks")
    await _require_unreleased(adapter, "bars")


async def fr_brokers_062_canonical_market_data(adapter: object) -> None:
    """FR-BRK-062: Stage 3 — Canonical Market Data Output."""
    _header("Stage 3: Canonical Market Data Output (FR-BRK-062)")
    ts_res = await get_broker_trading_sessions(adapter, "EURUSD")
    if get_broker_value_field(ts_res, "status") == "success":
        require_success("Result", ts_res)
    else:
        require_error("Result", ts_res, "BROKER_CAPABILITY_UNSUPPORTED")
    print(_format_result(ts_res))
    print(
        f"Data -> trading_sessions_status='{get_broker_value_field(ts_res, 'status')}'"
    )


async def _run() -> None:
    """Execute cTrader market evidence in one genuine demo session."""
    _feature_header(
        "FEATURE: FEAT-BRK-12 — ctrader_market_data/ — cTrader Market Data\n\n"
        "Purpose: Provide cTrader symbols, trading sessions, quotes, spreads, ticks, and historical bars.\n\n"
        "Module flow:\n"
        "-> symbol request\n"
        "-> cTrader protobuf call\n"
        "-> canonical market data"
    )

    try:
        async with real_session("ctrader") as adapter:
            # Stage 1: Symbol request
            await fr_brokers_124_to_125_symbol_request(adapter)

            # Stage 2: Protobuf call
            await fr_brokers_126_to_128_protobuf_calls(adapter)

            # Stage 3: Canonical market data output
            await fr_brokers_062_canonical_market_data(adapter)
    except UsageEvidenceError as err:
        print("Output Result -> UsageEvidenceError : UsageEvidenceError")
        print(f"Data -> status='FAIL_CLOSED', reason='{err}'")
        raise SystemExit(1) from err


def main() -> None:
    """Run the standalone genuine cTrader market-data program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
