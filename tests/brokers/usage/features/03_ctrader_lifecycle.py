"""FEAT-BRK-03: cTrader provider lifecycle."""

import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import _support  # noqa: F401
from _support import UsageEvidenceError, real_session, require_success
from app.services.brokers import (
    get_broker_connection_events,
    get_broker_connection_status,
    get_broker_historical_bars,
    get_broker_market_status,
    get_broker_quote,
    get_broker_symbol_info,
    get_broker_symbols,
    get_broker_ticks,
    get_broker_value_field,
    select_broker_symbol,
    supports_broker_capability,
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


async def fr_brokers_057_connection_events(adapter: object) -> None:
    """FR-BRK-057: Stage 1 & 2 — cTrader Credentials and Connection Verification."""
    _header("Stage 1 & 2: Credentials & Connection Verification (FR-BRK-057)")
    result = await get_broker_connection_status(adapter)
    require_success("Connection status", result)
    data = get_broker_value_field(result, "data")
    assert data is not None
    assert get_broker_value_field(data, "transport_connected")
    print(_format_result(result))
    print(
        f"Data -> transport_connected={get_broker_value_field(data, 'transport_connected')}, connection_events={get_broker_connection_events(adapter) is not None}"
    )


async def _require_unreleased(
    adapter: object,
    operation: str,
) -> None:
    """Exercise one cTrader market operation safely checking capability support."""
    capability_map = {
        "symbols": "get_symbols",
        "symbol_info": "get_symbol_info",
        "select_symbol": "select_symbol",
        "market_status": "get_market_status",
        "quote": "get_quote",
        "ticks": "get_ticks",
        "bars": "get_historical_bars",
    }
    cap_name = capability_map.get(operation, operation)
    supp_res = await supports_broker_capability(adapter, cap_name)
    if get_broker_value_field(supp_res, "data"):
        if operation == "symbols":
            result = await get_broker_symbols(adapter, limit=5)
        elif operation == "symbol_info":
            result = await get_broker_symbol_info(adapter, "EURUSD")
        elif operation == "select_symbol":
            result = await select_broker_symbol(adapter, "EURUSD")
        elif operation == "market_status":
            result = await get_broker_market_status(adapter, "EURUSD")
        elif operation == "quote":
            result = await get_broker_quote(adapter, "EURUSD")
        elif operation == "ticks":
            result = await get_broker_ticks(adapter, "EURUSD", limit=5)
        else:
            result = await get_broker_historical_bars(adapter, "EURUSD", "1m", limit=5)
        require_success("Result", result)
        print(_format_result(result))
        print(
            f"Data -> operation='{operation}', status='{get_broker_value_field(result, 'status')}'"
        )
    else:
        print(f"Data -> operation='{operation}', status='unsupported_on_provider'")


async def fr_brokers_058_to_065_authenticated_session_reads(adapter: object) -> None:
    """FR-BRK-058..065: Stage 3 — Authenticated Session Read Surface Output."""
    _header("Stage 3: Authenticated Session Reads Output (FR-BRK-058..065)")
    for op in (
        "symbols",
        "symbol_info",
        "select_symbol",
        "market_status",
        "quote",
        "ticks",
        "bars",
    ):
        await _require_unreleased(adapter, op)


async def _run() -> None:
    """Execute lifecycle evidence in one genuine cTrader demo session."""
    _feature_header(
        "FEATURE: FEAT-BRK-03 — ctrader_session/ — cTrader Account Lifecycle\n\n"
        "Purpose: Provide cTrader session lifecycle, authentication, and platform info.\n\n"
        "Module flow:\n"
        "-> cTrader credentials\n"
        "-> protobuf connection\n"
        "-> authenticated session"
    )

    try:
        async with real_session("ctrader") as adapter:
            # Stage 1 & 2: Credentials and connection verification
            await fr_brokers_057_connection_events(adapter)

            # Stage 3: Authenticated session reads output
            await fr_brokers_058_to_065_authenticated_session_reads(adapter)
    except UsageEvidenceError as err:
        print("Output Result -> UsageEvidenceError : UsageEvidenceError")
        print(f"Data -> status='FAIL_CLOSED', reason='{err}'")


def main() -> None:
    """Run the standalone genuine cTrader lifecycle program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
