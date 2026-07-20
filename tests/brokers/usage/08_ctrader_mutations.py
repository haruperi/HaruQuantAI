"""FEAT-BRK-08: demonstrate that implemented cTrader writes remain unavailable."""

import asyncio
from decimal import Decimal

from _support import config, show, unavailable_capabilities
from app.services.brokers import (
    BrokerEnvironment,
    BrokerId,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
    BrokerPositionCloseRequest,
    BrokerPositionModificationRequest,
    CTraderBrokerAdapter,
)


async def main() -> None:
    """Call every FEAT-BRK-08 operation through the fail-closed public boundary."""
    adapter = CTraderBrokerAdapter(config(BrokerId.CTRADER), unavailable_capabilities())
    order = BrokerOrderRequest(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.01"),
        quantity_unit="lots",
        environment=BrokerEnvironment.DEMO,
    )
    show("check", await adapter.check_order(order))
    show("place", await adapter.place_order(order))
    show(
        "modify-order",
        await adapter.modify_order(
            BrokerOrderModificationRequest(order_id="11", limit_price=Decimal("1.1"))
        ),
    )
    show("cancel", await adapter.cancel_order("11"))
    show(
        "modify-position",
        await adapter.modify_position(
            BrokerPositionModificationRequest(
                position_id="21", stop_loss=Decimal("1.0")
            )
        ),
    )
    show(
        "close-position",
        await adapter.close_position(
            BrokerPositionCloseRequest(
                position_id="21",
                quantity=Decimal("0.01"),
                quantity_unit="lots",
            )
        ),
    )


if __name__ == "__main__":
    asyncio.run(main())
