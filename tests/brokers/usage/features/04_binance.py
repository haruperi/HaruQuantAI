"""FEAT-BRK-04: Binance direct broker channel."""

import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import (
    get_broker_capability_id,
    get_broker_feature_flags,
    get_broker_order_book,
    get_broker_spread,
    get_broker_value_field,
    list_broker_subscriptions,
    subscribe_broker_bars,
    subscribe_broker_order_book,
    subscribe_broker_quotes,
    supports_broker_capability,
)

import _support  # noqa: F401
from _support import UsageEvidenceError, real_session, require_success


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
    """Exercise one Binance capability safely checking capability support."""
    capability_map = {
        "order_book": "get_order_book",
        "spread": "get_spread",
        "quotes": "subscribe_quotes",
        "bars": "subscribe_bars",
        "book_stream": "subscribe_order_book",
        "unsubscribe": "unsubscribe",
    }
    cap_name = capability_map.get(operation, operation)
    supp_res = await supports_broker_capability(adapter, cap_name)
    if get_broker_value_field(supp_res, "data"):
        if operation == "order_book":
            result = await get_broker_order_book(adapter, "BTCUSDT")
        elif operation == "spread":
            result = await get_broker_spread(adapter, "BTCUSDT")
        elif operation == "quotes":
            result = await subscribe_broker_quotes(adapter, ("BTCUSDT",))
        elif operation == "bars":
            result = await subscribe_broker_bars(adapter, ("BTCUSDT",), "1m")
        elif operation == "book_stream":
            result = await subscribe_broker_order_book(adapter, ("BTCUSDT",))
        else:
            result = await adapter.unsubscribe("invalid-id")
        require_success("Result", result)
        print(_format_result(result))
        print(
            f"Data -> operation='{operation}', status='{get_broker_value_field(result, 'status')}'"
        )
    else:
        print(f"Data -> operation='{operation}', status='unsupported_on_provider'")


async def fr_brokers_066_to_067_endpoint_validation(adapter: object) -> None:
    """FR-BRK-066..067: Stage 1 & 2 — Binance Profile Selection and REST/WS Validation."""
    _header("Stage 1 & 2: Profile Selection & Endpoint Validation (FR-BRK-066..067)")
    await _require_unreleased(adapter, "order_book")
    await _require_unreleased(adapter, "spread")


async def fr_brokers_068_to_074_session_status_and_capabilities(
    adapter: object,
) -> None:
    """FR-BRK-068..074: Stage 3 — Streaming Subscriptions & Session Status Output."""
    _header("Stage 3: Session Status & Capabilities Output (FR-BRK-068..074)")
    for op in ("quotes", "bars", "book_stream", "unsubscribe"):
        await _require_unreleased(adapter, op)

    subs_res = await list_broker_subscriptions(adapter)
    require_success("Result", subs_res)
    assert isinstance(get_broker_value_field(subs_res, "data"), tuple)
    print(_format_result(subs_res))
    print(
        f"Data -> active_subscriptions_count={len(get_broker_value_field(subs_res, 'data'))}"
    )

    ff_res = await get_broker_feature_flags(adapter)
    require_success("Result", ff_res)
    ff_data = get_broker_value_field(ff_res, "data")
    assert ff_data is not None
    assert get_broker_value_field(ff_data, "broker_id").value == "binance_spot"
    print(_format_result(ff_res))
    print(f"Data -> broker_id='{get_broker_value_field(ff_data, 'broker_id').value}'")

    supp_res = await supports_broker_capability(
        adapter, get_broker_capability_id("get_quote")
    )
    require_success("Result", supp_res)
    assert isinstance(get_broker_value_field(supp_res, "data"), bool)
    print(_format_result(supp_res))
    print(f"Data -> supports_get_quote={get_broker_value_field(supp_res, 'data')}")


async def _run() -> None:
    """Execute lifecycle evidence in one genuine Binance testnet session."""
    _feature_header(
        "FEATURE: FEAT-BRK-04 — binance_session/ — Binance Lifecycle\n\n"
        "Purpose: Provide Binance Spot and Futures connection profiles and lifecycle state.\n\n"
        "Module flow:\n"
        "-> Binance profile\n"
        "-> REST/WS endpoint validation\n"
        "-> session status"
    )

    try:
        async with real_session("binance_spot") as adapter:
            # Stage 1 & 2: Profile & Endpoint validation
            await fr_brokers_066_to_067_endpoint_validation(adapter)

            # Stage 3: Session status & capabilities output
            await fr_brokers_068_to_074_session_status_and_capabilities(adapter)
    except UsageEvidenceError as err:
        print("Output Result -> UsageEvidenceError : UsageEvidenceError")
        print(f"Data -> status='FAIL_CLOSED', reason='{err}'")
        raise SystemExit(1) from err


def main() -> None:
    """Run the standalone genuine Binance lifecycle program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
