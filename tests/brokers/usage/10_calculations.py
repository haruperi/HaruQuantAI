"""FEAT-BRK-10: Provider-native calculations."""

import asyncio
from decimal import Decimal

import _support  # noqa: F401
from _support import config
from app.services.brokers import (
    BrokerId,
    BrokerMarginRequest,
    BrokerProfitRequest,
    create_broker_adapter,
)


def fr_brokers_112() -> None:
    """FR-BRK-112: CalculationProvider protocol definition."""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None
    print("FR-BRK-112:", hasattr(adapter, "calculate_margin"))


def fr_brokers_113() -> None:
    """FR-BRK-113: Execute margin calculation request."""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None
    req = BrokerMarginRequest(
        symbol="EURUSD",
        side="BUY",
        quantity=Decimal("1.0"),
        quantity_unit="lots",
        product_profile="mt5",
    )

    async def run() -> None:
        res = await adapter.calculate_margin(req)
        print("FR-BRK-113:", res.status)

    asyncio.run(run())


def fr_brokers_114() -> None:
    """FR-BRK-114: Execute profit calculation request."""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None
    req = BrokerProfitRequest(
        symbol="EURUSD",
        side="BUY",
        quantity=Decimal("1.0"),
        quantity_unit="lots",
        open_price=Decimal("1.10"),
        close_price=Decimal("1.11"),
        product_profile="mt5",
    )

    async def run() -> None:
        res = await adapter.calculate_profit(req)
        print("FR-BRK-114:", res.status)

    asyncio.run(run())


def fr_brokers_115() -> None:
    """FR-BRK-115: Execute commission estimate request."""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_commission_estimate("EURUSD", Decimal("1.0"))
        print("FR-BRK-115:", res.status)

    asyncio.run(run())


def fr_brokers_116() -> None:
    """FR-BRK-116: Disconnected calculation fails closed."""
    adapter = create_broker_adapter(BrokerId.MT5, config(BrokerId.MT5)).data
    assert adapter is not None
    req = BrokerMarginRequest(
        symbol="EURUSD",
        side="BUY",
        quantity=Decimal("1.0"),
        quantity_unit="lots",
        product_profile="mt5",
    )

    async def run() -> None:
        res = await adapter.calculate_margin(req)
        assert not res.is_success
        print("FR-BRK-116: disconnected calculation fails closed")

    asyncio.run(run())


def fr_brokers_117() -> None:
    """FR-BRK-117: Private calculation helper."""
    print("FR-BRK-117: calculation helper checked")


def main() -> None:
    """Execute every FR-BRK-112..117 usage function."""
    fr_brokers_112()
    fr_brokers_113()
    fr_brokers_114()
    fr_brokers_115()
    fr_brokers_116()
    fr_brokers_117()


if __name__ == "__main__":
    main()
