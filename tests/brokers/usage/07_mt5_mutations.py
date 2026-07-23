"""FEAT-BRK-07: exercise the MT5 single-target mutation surface.

Runs the genuine `MT5BrokerAdapter` over an offline transport. Real request
construction, provider acknowledgement mapping, pre-transmission validation and
fail-closed unknown-outcome behaviour execute without a terminal or live order.
"""

import asyncio
from decimal import Decimal

from _support import (
    OfflineMT5Transport,
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
    MT5BrokerAdapter,
)

_REQUEST_ID = "req-2f1d5a6c-8b3e-4c17-9f52-70a1c8d94e33"


def _order() -> BrokerOrderRequest:
    """Build one complete, structurally valid V1 order request."""
    return BrokerOrderRequest(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.01"),
        quantity_unit="lots",
        environment=BrokerEnvironment.DEMO,
        client_request_id=_REQUEST_ID,
    )


async def example_acknowledged_mutations() -> None:
    """Every single-target mutation maps an explicit provider acknowledgement."""
    transport = OfflineMT5Transport()
    adapter = MT5BrokerAdapter(
        config(BrokerId.MT5), available_capabilities(), transport=transport
    )
    await adapter.connect()

    checked = await adapter.check_order(_order())
    show_value(
        "check",
        checked,
        f"accepted={checked.data.accepted_for_submission} "
        f"final={checked.data.is_final_acceptance}"
        if checked.data
        else None,
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
                order_id="555002",
                client_request_id=_REQUEST_ID,
                limit_price=Decimal("1.09000"),
            )
        ),
    )
    show("cancel-order", await adapter.cancel_order("555002", _REQUEST_ID))
    show(
        "modify-position",
        await adapter.modify_position(
            BrokerPositionModificationRequest(
                position_id="555001",
                client_request_id=_REQUEST_ID,
                stop_loss=Decimal("1.09000"),
            )
        ),
    )
    show(
        "close-position",
        await adapter.close_position(
            BrokerPositionCloseRequest(
                position_id="555001",
                quantity=Decimal("0.25"),
                quantity_unit="lots",
                client_request_id=_REQUEST_ID,
            )
        ),
    )
    print("provider calls", len(transport.calls))


async def example_invalid_target_is_rejected_before_transmission() -> None:
    """A malformed caller identifier never becomes an uncertain outcome."""
    transport = OfflineMT5Transport()
    adapter = MT5BrokerAdapter(
        config(BrokerId.MT5), available_capabilities(), transport=transport
    )
    await adapter.connect()
    show("cancel-invalid-target", await adapter.cancel_order("not-a-ticket"))
    print("order_send calls", transport.calls.count("order_send"))


async def example_writes_remain_unreleased() -> None:
    """Mutations stay fail-closed while the release gate is unsatisfied."""
    transport = OfflineMT5Transport()
    adapter = MT5BrokerAdapter(
        config(BrokerId.MT5), unavailable_capabilities(), transport=transport
    )
    show("gated-place", await adapter.place_order(_order()))
    print("provider calls while gated", len(transport.calls))


async def main() -> None:
    """Exercise every FEAT-BRK-07 operation offline."""
    await example_acknowledged_mutations()
    await example_invalid_target_is_rejected_before_transmission()
    await example_writes_remain_unreleased()


if __name__ == "__main__":
    asyncio.run(main())
