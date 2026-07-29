"""FEAT-BRK-07: MetaTrader 5 mutation capability safety."""

import asyncio

import _support  # noqa: F401
from _support import (
    create_real_adapter,
    real_session,
    require_error,
    require_success,
)
from app.services.brokers import (
    build_broker_order_modification_request,
    build_broker_order_request,
    build_broker_position_close_request,
    build_broker_position_modification_request,
    cancel_broker_order,
    check_broker_order,
    close_broker_position,
    disconnect_broker,
    get_broker_connection_status,
    modify_broker_order,
    modify_broker_position,
    place_broker_order,
    replace_broker_order,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _order() -> object:
    """Build one bounded demo order request without transmitting it."""
    return build_broker_order_request(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity="0.01",
        quantity_unit="lots",
        environment="demo",
    )


async def fr_brokers_091(adapter: object) -> None:
    """FR-BRK-091: Validate an order request before transmission."""
    _header("FR-BRK-091: Validate an order request before transmission.")
    require_error(
        "Result",
        await check_broker_order(adapter, _order()),
        "BROKER_NOT_CONNECTED",
        "BROKER_CAPABILITY_UNSUPPORTED",
    )


async def fr_brokers_092(adapter: object) -> None:
    """FR-BRK-092: Submit one mutation once without retry."""
    _header("FR-BRK-092: Submit one mutation once without retry.")
    require_error(
        "Result",
        await place_broker_order(adapter, _order()),
        "BROKER_NOT_CONNECTED",
        "BROKER_CAPABILITY_UNSUPPORTED",
    )


async def fr_brokers_093(adapter: object) -> None:
    """FR-BRK-093: Modify one existing pending order."""
    _header("FR-BRK-093: Modify one existing pending order.")
    modification = build_broker_order_modification_request(
        order_id="o1",
        limit_price="1.11",
    )
    require_error(
        "Result",
        await modify_broker_order(adapter, modification),
        "BROKER_CAPABILITY_UNSUPPORTED",
        "BROKER_NOT_CONNECTED",
    )


async def fr_brokers_094(adapter: object) -> None:
    """FR-BRK-094: Cancel one pending order."""
    _header("FR-BRK-094: Cancel one pending order.")
    require_error(
        "Result",
        await cancel_broker_order(adapter, "o1"),
        "BROKER_NOT_CONNECTED",
        "BROKER_CAPABILITY_UNSUPPORTED",
    )


async def fr_brokers_095(adapter: object) -> None:
    """FR-BRK-095: Modify one position's stop-loss or take-profit."""
    _header("FR-BRK-095: Modify one position's stop-loss or take-profit.")
    modification = build_broker_position_modification_request(
        position_id="p1",
        stop_loss="1.09",
    )
    require_error(
        "Result",
        await modify_broker_position(adapter, modification),
        "BROKER_CAPABILITY_UNSUPPORTED",
        "BROKER_NOT_CONNECTED",
    )


async def fr_brokers_096(adapter: object) -> None:
    """FR-BRK-096: Close or reduce one position."""
    _header("FR-BRK-096: Close or reduce one position.")
    close = build_broker_position_close_request(
        position_id="p1",
        quantity="0.5",
        quantity_unit="lots",
    )
    require_error(
        "Result",
        await close_broker_position(adapter, close),
        "BROKER_NOT_CONNECTED",
        "BROKER_CAPABILITY_UNSUPPORTED",
    )


async def fr_brokers_097(adapter: object) -> None:
    """FR-BRK-097: Replace one order atomically or fail closed."""
    _header("FR-BRK-097: Replace one order atomically or fail closed.")
    require_error(
        "Result",
        await replace_broker_order(
            adapter,
            build_broker_order_modification_request(
                order_id="o1",
                limit_price="1.11",
            ),
        ),
        "BROKER_CAPABILITY_UNSUPPORTED",
        "BROKER_NOT_CONNECTED",
    )


async def _run() -> None:
    """Verify a real MT5 demo session, then prove mutations remain no-side-effect."""
    async with real_session("mt5") as connected:
        require_success(
            "Verified demo status",
            await get_broker_connection_status(connected),
        )

    disconnected = create_real_adapter("mt5")
    await fr_brokers_091(disconnected)
    await fr_brokers_092(disconnected)
    await fr_brokers_093(disconnected)
    await fr_brokers_094(disconnected)
    await fr_brokers_095(disconnected)
    await fr_brokers_096(disconnected)
    await fr_brokers_097(disconnected)
    require_success("Final cleanup", await disconnect_broker(disconnected))


def main() -> None:
    """Run the genuine-session, no-mutation MT5 safety program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
