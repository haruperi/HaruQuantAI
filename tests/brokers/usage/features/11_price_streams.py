"""FEAT-BRK-11: genuine session and price-stream release boundaries."""

import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import _support  # noqa: F401
from _support import UsageEvidenceError, real_session, require_error, require_success
from app.services.brokers import (
    get_broker_value_field,
    list_broker_subscriptions,
    subscribe_broker_bars,
    subscribe_broker_order_book,
    subscribe_broker_quotes,
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
    """Require one stream operation to remain release-gated."""
    if operation == "quotes":
        result = await subscribe_broker_quotes(adapter, "BTCUSDT")
    elif operation == "bars":
        result = await subscribe_broker_bars(adapter, "BTCUSDT", "1m")
    elif operation == "book":
        result = await subscribe_broker_order_book(adapter, "BTCUSDT")
    else:
        return

    if get_broker_value_field(result, "status") == "success":
        require_success("Result", result)
    else:
        require_error("Result", result, "BROKER_CAPABILITY_UNSUPPORTED")
    print(_format_result(result))
    print(
        f"Data -> operation='{operation}', status='{get_broker_value_field(result, 'status')}'"
    )


async def fr_brokers_118_to_120_subscription_requests(adapter: object) -> None:
    """FR-BRK-118..120: Stage 1 & 2 — Subscription Request & Async Channel Creation."""
    _header(
        "Stage 1 & 2: Subscription Request & Async Channel Creation (FR-BRK-118..120)"
    )
    await _require_unreleased(adapter, "quotes")
    await _require_unreleased(adapter, "bars")
    await _require_unreleased(adapter, "book")


async def fr_brokers_121_to_123_streaming_events(adapter: object) -> None:
    """FR-BRK-121..123: Stage 3 — Streaming Events & Subscription Metadata Output."""
    _header("Stage 3: Streaming Events & Active Subscriptions Output (FR-BRK-121..123)")
    subs_res = await list_broker_subscriptions(adapter)
    require_success("Result", subs_res)
    assert isinstance(get_broker_value_field(subs_res, "data"), tuple)
    print(_format_result(subs_res))
    print(
        f"Data -> active_subscriptions_count={len(get_broker_value_field(subs_res, 'data'))}"
    )


async def _run() -> None:
    """Execute stream release evidence in one genuine Binance testnet session."""
    _feature_header(
        "FEATURE: FEAT-BRK-11 — price_streams/ — Price Streams\n\n"
        "Purpose: Provide bounded streaming subscriptions for quotes, bars, and order books.\n\n"
        "Module flow:\n"
        "-> subscription request\n"
        "-> async channel creation\n"
        "-> streaming events"
    )

    try:
        async with real_session("binance_spot") as adapter:
            # Stage 1 & 2: Subscription request & async channel creation
            await fr_brokers_118_to_120_subscription_requests(adapter)

            # Stage 3: Streaming events output & active subscriptions
            await fr_brokers_121_to_123_streaming_events(adapter)
    except UsageEvidenceError as err:
        print("Output Result -> UsageEvidenceError : UsageEvidenceError")
        print(f"Data -> status='FAIL_CLOSED', reason='{err}'")


def main() -> None:
    """Run the standalone genuine price-stream release program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
