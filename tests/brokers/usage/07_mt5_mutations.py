"""FEAT-BRK-07: MetaTrader 5 mutation capabilities."""

import asyncio
from decimal import Decimal

import _support  # noqa: F401
from _support import config
from app.services.brokers import (
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
    BrokerPositionCloseRequest,
    BrokerPositionModificationRequest,
    create_broker_adapter,
)


def fr_brokers_091() -> None:
    """FR-BRK-091: Validate order request before transmission."""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None
    req = BrokerOrderRequest(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.01"),
        quantity_unit="lots",
        environment=BrokerEnvironment.DEMO,
    )

    async def run() -> None:
        res = await adapter.check_order(req)
        print("FR-BRK-091:", res.error.code if res.error else None)

    asyncio.run(run())


def fr_brokers_092() -> None:
    """FR-BRK-092: Submit single order mutation once without retry."""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None
    req = BrokerOrderRequest(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.01"),
        quantity_unit="lots",
        environment=BrokerEnvironment.DEMO,
    )

    async def run() -> None:
        res = await adapter.place_order(req)
        assert res.error is not None
        assert res.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
        print("FR-BRK-092: unreleased write blocked closed")

    asyncio.run(run())


def fr_brokers_093() -> None:
    """FR-BRK-093: Modify single existing pending order."""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None
    mod = BrokerOrderModificationRequest(order_id="o1", limit_price=Decimal("1.11"))

    async def run() -> None:
        res = await adapter.modify_order(mod)
        assert res.error is not None
        assert res.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
        print("FR-BRK-093: unreleased write blocked closed")

    asyncio.run(run())


def fr_brokers_094() -> None:
    """FR-BRK-094: Cancel single pending order."""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.cancel_order("o1")
        assert res.error is not None
        assert res.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
        print("FR-BRK-094: unreleased write blocked closed")

    asyncio.run(run())


def fr_brokers_095() -> None:
    """FR-BRK-095: Modify single position stop-loss/take-profit."""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None
    mod = BrokerPositionModificationRequest(position_id="p1", stop_loss=Decimal("1.09"))

    async def run() -> None:
        res = await adapter.modify_position(mod)
        assert res.error is not None
        assert res.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
        print("FR-BRK-095: unreleased write blocked closed")

    asyncio.run(run())


def fr_brokers_096() -> None:
    """FR-BRK-096: Close or reduce single position."""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None
    close = BrokerPositionCloseRequest(
        position_id="p1", quantity=Decimal("0.5"), quantity_unit="lots"
    )

    async def run() -> None:
        res = await adapter.close_position(close)
        assert res.error is not None
        assert res.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
        print("FR-BRK-096: unreleased write blocked closed")

    asyncio.run(run())


def fr_brokers_097() -> None:
    """FR-BRK-097: Replace single order in single atomic operation."""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None
    req = BrokerOrderRequest(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.01"),
        quantity_unit="lots",
        environment=BrokerEnvironment.DEMO,
    )

    async def run() -> None:
        res = await adapter.replace_order("o1", req)
        assert res.error is not None
        assert res.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
        print("FR-BRK-097: unreleased write blocked closed")

    asyncio.run(run())


def main() -> None:
    """Execute every FR-BRK-091..097 usage function."""
    fr_brokers_091()
    fr_brokers_092()
    fr_brokers_093()
    fr_brokers_094()
    fr_brokers_095()
    fr_brokers_096()
    fr_brokers_097()


if __name__ == "__main__":
    main()
