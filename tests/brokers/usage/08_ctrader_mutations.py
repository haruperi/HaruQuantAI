"""FEAT-BRK-08: exercise the cTrader single-target mutation surface.

Runs the genuine `CTraderBrokerAdapter` over an offline sender. Real lot-size
aware volume conversion, protobuf request construction, acknowledgement mapping,
and fail-closed validation execute without Spotware traffic or a live order.
"""

import asyncio
from decimal import Decimal

from _support import (
    OfflineCTraderTransport,
    available_capabilities,
    config,
    show,
    show_value,
    unavailable_capabilities,
)
from app.services.brokers import (
    BrokerEnvironment,
    BrokerId,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
    BrokerPositionCloseRequest,
    BrokerPositionModificationRequest,
    CTraderBrokerAdapter,
)

_REQUEST_ID = "req-2f1d5a6c-8b3e-4c17-9f52-70a1c8d94e33"


def _order() -> BrokerOrderRequest:
    """Build one complete, structurally valid V1 order request."""
    return BrokerOrderRequest(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal(1),
        quantity_unit="lots",
        environment=BrokerEnvironment.DEMO,
        client_request_id=_REQUEST_ID,
    )


async def example_acknowledged_mutations() -> None:
    """Each mutation maps an explicit provider acknowledgement, once."""
    transport = OfflineCTraderTransport()
    adapter = CTraderBrokerAdapter(
        config(BrokerId.CTRADER), available_capabilities(), transport=transport
    )
    await adapter.connect()

    checked = await adapter.check_order(_order())
    show_value(
        "check",
        checked,
        f"final={checked.data.is_final_acceptance}" if checked.data else None,
    )

    placed = await adapter.place_order(_order())
    show_value(
        "place",
        placed,
        f"outcome={placed.data.outcome} order_id={placed.data.order_id}"
        if placed.data
        else None,
    )
    show(
        "modify-order",
        await adapter.modify_order(
            BrokerOrderModificationRequest(
                order_id="11",
                client_request_id=_REQUEST_ID,
                limit_price=Decimal("1.09000"),
            )
        ),
    )
    show("cancel-order", await adapter.cancel_order("11", _REQUEST_ID))
    show(
        "modify-position",
        await adapter.modify_position(
            BrokerPositionModificationRequest(
                position_id="21",
                client_request_id=_REQUEST_ID,
                stop_loss=Decimal("1.09000"),
            )
        ),
    )
    show(
        "close-position",
        await adapter.close_position(
            BrokerPositionCloseRequest(
                position_id="21",
                quantity=Decimal(1),
                quantity_unit="lots",
                client_request_id=_REQUEST_ID,
            )
        ),
    )
    print("provider requests", len(transport.requests))


async def example_unrepresentable_quantity_is_rejected() -> None:
    """A quantity outside the provider volume grid never reaches the venue."""
    transport = OfflineCTraderTransport()
    adapter = CTraderBrokerAdapter(
        config(BrokerId.CTRADER), available_capabilities(), transport=transport
    )
    await adapter.connect()
    request = BrokerOrderRequest(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.000000001"),
        quantity_unit="lots",
        environment=BrokerEnvironment.DEMO,
        client_request_id=_REQUEST_ID,
    )
    show("place-unrepresentable", await adapter.place_order(request))
    print("new-order requests", transport.requests.count("ProtoOANewOrderReq"))


async def example_writes_remain_unreleased() -> None:
    """Mutations stay fail-closed while the release gate is unsatisfied."""
    transport = OfflineCTraderTransport()
    adapter = CTraderBrokerAdapter(
        config(BrokerId.CTRADER), unavailable_capabilities(), transport=transport
    )
    show("gated-place", await adapter.place_order(_order()))
    print("provider requests while gated", len(transport.requests))


async def main() -> None:
    """Exercise every FEAT-BRK-08 operation offline."""
    await example_acknowledged_mutations()
    await example_unrepresentable_quantity_is_rejected()
    await example_writes_remain_unreleased()


if __name__ == "__main__":
    asyncio.run(main())
