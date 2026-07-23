"""WF-BRK-004: submit one mutation through canonical API."""

import asyncio
from decimal import Decimal

import _bootstrap  # noqa: F401
from app.services.brokers import (
    BrokerEnvironment,
    BrokerId,
    BrokerOrderRequest,
    create_broker_adapter,
)
from wf_support import build_mt5_connection_config, print_result


def _order_request() -> BrokerOrderRequest:
    """Build one complete mutation request for demonstration.

    Returns:
        Bounded demo mutation request.
    """
    return BrokerOrderRequest(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.01"),
        quantity_unit="lots",
        environment=BrokerEnvironment.DEMO,
    )


async def _run() -> None:
    """Call an unreleased write and show deterministic fail-closed behavior."""
    created = create_broker_adapter(BrokerId.MT5, build_mt5_connection_config())
    if created.data is None:
        print("WF-BRK-004: adapter creation failed")
        print_result("WF-BRK-004", created)
        return

    adapter = created.data
    result = await adapter.place_order(_order_request())
    print_result("WF-BRK-004: place_order", result)


def main() -> None:
    """Execute WF-BRK-004 demonstration."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
