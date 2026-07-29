"""FEAT-BRK-08: cTrader calculation and mutation release boundaries."""

import asyncio

import _support  # noqa: F401
from _support import real_session, require_error, require_success
from app.services.brokers import (
    build_broker_margin_request,
    build_broker_order_request,
    build_broker_profit_request,
    calculate_broker_margin,
    calculate_broker_profit,
    cancel_broker_order,
    get_broker_capability_catalogue,
    get_broker_commission_estimate,
    get_broker_connection_status,
    get_broker_value_field,
    get_registered_brokers,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


async def fr_brokers_098(adapter: object) -> None:
    """FR-BRK-098: Request a provider-native margin calculation."""
    _header("FR-BRK-098: Request a provider-native margin calculation.")
    request = build_broker_margin_request(
        symbol="EURUSD",
        side="BUY",
        quantity="1.0",
        quantity_unit="lots",
        price="1.10",
        product_profile="ctrader",
    )
    result = await calculate_broker_margin(adapter, request)
    if get_broker_value_field(result, "status") == "success":
        require_success("Result", result)
    else:
        require_error("Result", result, "BROKER_CAPABILITY_UNSUPPORTED")


async def fr_brokers_099(adapter: object) -> None:
    """FR-BRK-099: Request a provider-native profit calculation."""
    _header("FR-BRK-099: Request a provider-native profit calculation.")
    request = build_broker_profit_request(
        symbol="EURUSD",
        side="BUY",
        quantity="1.0",
        quantity_unit="lots",
        open_price="1.10",
        close_price="1.11",
        product_profile="ctrader",
    )
    result = await calculate_broker_profit(adapter, request)
    if get_broker_value_field(result, "status") == "success":
        require_success("Result", result)
    else:
        require_error("Result", result, "BROKER_CAPABILITY_UNSUPPORTED")


async def fr_brokers_100(adapter: object) -> None:
    """FR-BRK-100: Request a provider-native commission estimate."""
    _header("FR-BRK-100: Request a provider-native commission estimate.")
    result = await get_broker_commission_estimate(
        adapter,
        build_broker_order_request(
            symbol="EURUSD",
            side="BUY",
            order_type="MARKET",
            quantity="1.0",
            quantity_unit="lots",
            environment="demo",
        ),
    )
    if get_broker_value_field(result, "status") == "success":
        require_success("Result", result)
    else:
        require_error("Result", result, "BROKER_CAPABILITY_UNSUPPORTED")


async def fr_brokers_101(adapter: object) -> None:
    """FR-BRK-101: Resolve an explicit cTrader adapter profile."""
    _header("FR-BRK-101: Resolve an explicit cTrader adapter profile.")
    require_success("Result", await get_broker_connection_status(adapter))


async def fr_brokers_102(adapter: object) -> None:
    """FR-BRK-102: List registered brokers without importing all SDKs."""
    del adapter
    _header("FR-BRK-102: List registered brokers without importing all SDKs.")
    response = get_registered_brokers()
    assert response.status == "success"
    assert response.data is not None
    brokers = response.data
    print("Result", len(brokers))
    assert "ctrader" in brokers


async def fr_brokers_103(adapter: object) -> None:
    """FR-BRK-103: Expose the complete static capability catalogue."""
    del adapter
    _header("FR-BRK-103: Expose the complete static capability catalogue.")
    response = get_broker_capability_catalogue()
    assert response.status == "success"
    assert response.data is not None
    catalogue = response.data
    print("Result", len(catalogue))
    assert "ctrader" in catalogue


async def fr_brokers_104(adapter: object) -> None:
    """FR-BRK-104: Block unreleased cTrader write operations."""
    _header("FR-BRK-104: Block unreleased cTrader write operations.")
    require_error(
        "Result",
        await cancel_broker_order(adapter, "o1"),
        "BROKER_CAPABILITY_UNSUPPORTED",
    )


async def _run() -> None:
    """Execute release evidence in one genuine cTrader demo session."""
    async with real_session("ctrader") as adapter:
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
