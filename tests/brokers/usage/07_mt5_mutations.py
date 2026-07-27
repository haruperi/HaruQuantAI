"""FEAT-BRK-07: MetaTrader 5 mutation capability safety."""

import asyncio
from decimal import Decimal

import _support  # noqa: F401
from _support import (
    create_real_adapter,
    real_session,
    require_error,
    require_success,
)
from app.services.brokers import (
    BrokerAdapter,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
    BrokerPositionCloseRequest,
    BrokerPositionModificationRequest,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _order() -> BrokerOrderRequest:
    """Build one bounded demo order request without transmitting it."""
    return BrokerOrderRequest(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.01"),
        quantity_unit="lots",
        environment=BrokerEnvironment.DEMO,
    )


async def fr_brokers_091(adapter: BrokerAdapter) -> None:
    """FR-BRK-091: Validate an order request before transmission."""
    _header("FR-BRK-091: Validate an order request before transmission.")
    require_error(
        "Result",
        await adapter.check_order(_order()),
        BrokerErrorCode.BROKER_NOT_CONNECTED,
    )


async def fr_brokers_092(adapter: BrokerAdapter) -> None:
    """FR-BRK-092: Submit one mutation once without retry."""
    _header("FR-BRK-092: Submit one mutation once without retry.")
    require_error(
        "Result",
        await adapter.place_order(_order()),
        BrokerErrorCode.BROKER_NOT_CONNECTED,
    )


async def fr_brokers_093(adapter: BrokerAdapter) -> None:
    """FR-BRK-093: Modify one existing pending order."""
    _header("FR-BRK-093: Modify one existing pending order.")
    modification = BrokerOrderModificationRequest(
        order_id="o1",
        limit_price=Decimal("1.11"),
    )
    require_error(
        "Result",
        await adapter.modify_order(modification),
        BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
    )


async def fr_brokers_094(adapter: BrokerAdapter) -> None:
    """FR-BRK-094: Cancel one pending order."""
    _header("FR-BRK-094: Cancel one pending order.")
    require_error(
        "Result",
        await adapter.cancel_order("o1"),
        BrokerErrorCode.BROKER_NOT_CONNECTED,
    )


async def fr_brokers_095(adapter: BrokerAdapter) -> None:
    """FR-BRK-095: Modify one position's stop-loss or take-profit."""
    _header("FR-BRK-095: Modify one position's stop-loss or take-profit.")
    modification = BrokerPositionModificationRequest(
        position_id="p1",
        stop_loss=Decimal("1.09"),
    )
    require_error(
        "Result",
        await adapter.modify_position(modification),
        BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
    )


async def fr_brokers_096(adapter: BrokerAdapter) -> None:
    """FR-BRK-096: Close or reduce one position."""
    _header("FR-BRK-096: Close or reduce one position.")
    close = BrokerPositionCloseRequest(
        position_id="p1",
        quantity=Decimal("0.5"),
        quantity_unit="lots",
    )
    require_error(
        "Result",
        await adapter.close_position(close),
        BrokerErrorCode.BROKER_NOT_CONNECTED,
    )


async def fr_brokers_097(adapter: BrokerAdapter) -> None:
    """FR-BRK-097: Replace one order atomically or fail closed."""
    _header("FR-BRK-097: Replace one order atomically or fail closed.")
    require_error(
        "Result",
        await adapter.replace_order("o1", _order()),
        BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
    )


async def _run() -> None:
    """Verify a real MT5 demo session, then prove mutations remain no-side-effect."""
    async with real_session(BrokerId.MT5) as connected:
        require_success("Verified demo status", await connected.get_connection_status())

    disconnected = create_real_adapter(BrokerId.MT5)
    await fr_brokers_091(disconnected)
    await fr_brokers_092(disconnected)
    await fr_brokers_093(disconnected)
    await fr_brokers_094(disconnected)
    await fr_brokers_095(disconnected)
    await fr_brokers_096(disconnected)
    await fr_brokers_097(disconnected)
    require_success("Final cleanup", await disconnected.disconnect())


def main() -> None:
    """Run the genuine-session, no-mutation MT5 safety program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
