"""FEAT-BRK-08: cTrader mutation capabilities."""

import asyncio
from decimal import Decimal

import _support  # noqa: F401
from _support import config
from app.services.brokers import (
    BrokerErrorCode,
    BrokerId,
    BrokerMarginRequest,
    BrokerProfitRequest,
    create_broker_adapter,
)


def fr_brokers_098() -> None:
    """FR-BRK-098: Request provider-native margin calculation."""
    adapter = create_broker_adapter(BrokerId.CTRADER, config(BrokerId.CTRADER)).data
    assert adapter is not None
    req = BrokerMarginRequest(
        symbol="EURUSD",
        side="BUY",
        quantity=Decimal("1.0"),
        quantity_unit="lots",
        product_profile="ctrader",
    )

    async def run() -> None:
        res = await adapter.calculate_margin(req)
        print("FR-BRK-098:", res.status)

    asyncio.run(run())


def fr_brokers_099() -> None:
    """FR-BRK-099: Request provider-native profit calculation."""
    adapter = create_broker_adapter(BrokerId.CTRADER, config(BrokerId.CTRADER)).data
    assert adapter is not None
    req = BrokerProfitRequest(
        symbol="EURUSD",
        side="BUY",
        quantity=Decimal("1.0"),
        quantity_unit="lots",
        open_price=Decimal("1.10"),
        close_price=Decimal("1.11"),
        product_profile="ctrader",
    )

    async def run() -> None:
        res = await adapter.calculate_profit(req)
        print("FR-BRK-099:", res.status)

    asyncio.run(run())


def fr_brokers_100() -> None:
    """FR-BRK-100: Request provider-native commission estimate."""
    adapter = create_broker_adapter(BrokerId.CTRADER, config(BrokerId.CTRADER)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.get_commission_estimate("EURUSD", Decimal("1.0"))
        print("FR-BRK-100:", res.status)

    asyncio.run(run())


def fr_brokers_101() -> None:
    """FR-BRK-101: Resolve explicit broker adapter profile."""
    created = create_broker_adapter(BrokerId.CTRADER, config(BrokerId.CTRADER))
    print("FR-BRK-101:", created.status)


def fr_brokers_102() -> None:
    """FR-BRK-102: List registered brokers without SDK import."""
    from app.services.brokers import get_registered_brokers

    brokers = get_registered_brokers()
    print("FR-BRK-102:", len(brokers))


def fr_brokers_103() -> None:
    """FR-BRK-103: Expose complete static capability catalogue."""
    from app.services.brokers import get_broker_capability_catalogue

    cat = get_broker_capability_catalogue()
    print("FR-BRK-103:", len(cat))


def fr_brokers_104() -> None:
    """FR-BRK-104: Block unreleased cTrader write operations."""
    adapter = create_broker_adapter(BrokerId.CTRADER, config(BrokerId.CTRADER)).data
    assert adapter is not None

    async def run() -> None:
        res = await adapter.cancel_order("o1")
        assert res.error is not None
        assert res.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED
        print("FR-BRK-104: write blocked")

    asyncio.run(run())


def main() -> None:
    """Execute every FR-BRK-098..104 usage function."""
    fr_brokers_098()
    fr_brokers_099()
    fr_brokers_100()
    fr_brokers_101()
    fr_brokers_102()
    fr_brokers_103()
    fr_brokers_104()


if __name__ == "__main__":
    main()
