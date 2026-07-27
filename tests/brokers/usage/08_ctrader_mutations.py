"""FEAT-BRK-08: cTrader calculation and mutation release boundaries."""

import asyncio
from decimal import Decimal

import _support  # noqa: F401
from _support import real_session, require_error, require_success
from app.services.brokers import (
    BrokerAdapter,
    BrokerErrorCode,
    BrokerId,
    BrokerMarginRequest,
    BrokerProfitRequest,
    get_broker_capability_catalogue,
    get_registered_brokers,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


async def fr_brokers_098(adapter: BrokerAdapter) -> None:
    """FR-BRK-098: Request a provider-native margin calculation."""
    _header("FR-BRK-098: Request a provider-native margin calculation.")
    request = BrokerMarginRequest(
        symbol="EURUSD",
        side="BUY",
        quantity=Decimal("1.0"),
        quantity_unit="lots",
        price=Decimal("1.10"),
        product_profile="ctrader",
    )
    require_error(
        "Result",
        await adapter.calculate_margin(request),
        BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
    )


async def fr_brokers_099(adapter: BrokerAdapter) -> None:
    """FR-BRK-099: Request a provider-native profit calculation."""
    _header("FR-BRK-099: Request a provider-native profit calculation.")
    request = BrokerProfitRequest(
        symbol="EURUSD",
        side="BUY",
        quantity=Decimal("1.0"),
        quantity_unit="lots",
        open_price=Decimal("1.10"),
        close_price=Decimal("1.11"),
        product_profile="ctrader",
    )
    require_error(
        "Result",
        await adapter.calculate_profit(request),
        BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
    )


async def fr_brokers_100(adapter: BrokerAdapter) -> None:
    """FR-BRK-100: Request a provider-native commission estimate."""
    _header("FR-BRK-100: Request a provider-native commission estimate.")
    require_error(
        "Result",
        await adapter.get_commission_estimate("EURUSD", Decimal("1.0")),
        BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
    )


async def fr_brokers_101(adapter: BrokerAdapter) -> None:
    """FR-BRK-101: Resolve an explicit cTrader adapter profile."""
    _header("FR-BRK-101: Resolve an explicit cTrader adapter profile.")
    require_success("Result", await adapter.get_connection_status())


async def fr_brokers_102(adapter: BrokerAdapter) -> None:
    """FR-BRK-102: List registered brokers without importing all SDKs."""
    del adapter
    _header("FR-BRK-102: List registered brokers without importing all SDKs.")
    response = get_registered_brokers()
    assert response.status == "success"
    assert response.data is not None
    brokers = response.data
    print("Result", len(brokers))
    assert BrokerId.CTRADER in brokers


async def fr_brokers_103(adapter: BrokerAdapter) -> None:
    """FR-BRK-103: Expose the complete static capability catalogue."""
    del adapter
    _header("FR-BRK-103: Expose the complete static capability catalogue.")
    response = get_broker_capability_catalogue()
    assert response.status == "success"
    assert response.data is not None
    catalogue = response.data
    print("Result", len(catalogue))
    assert BrokerId.CTRADER in catalogue


async def fr_brokers_104(adapter: BrokerAdapter) -> None:
    """FR-BRK-104: Block unreleased cTrader write operations."""
    _header("FR-BRK-104: Block unreleased cTrader write operations.")
    require_error(
        "Result",
        await adapter.cancel_order("o1"),
        BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
    )


async def _run() -> None:
    """Execute release evidence in one genuine cTrader demo session."""
    async with real_session(BrokerId.CTRADER) as adapter:
        await fr_brokers_098(adapter)
        await fr_brokers_099(adapter)
        await fr_brokers_100(adapter)
        await fr_brokers_101(adapter)
        await fr_brokers_102(adapter)
        await fr_brokers_103(adapter)
        await fr_brokers_104(adapter)


def main() -> None:
    """Run the standalone genuine cTrader release-boundary program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
