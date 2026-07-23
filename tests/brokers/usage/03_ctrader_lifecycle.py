"""FEAT-BRK-03: exercise the cTrader lifecycle surface.

Runs the genuine `CTraderBrokerAdapter` over an injected offline sender, so the
real session verification, platform-info mapping, and deterministic release all
execute without Spotware network traffic or credentials.
"""

import asyncio

from _support import (
    OfflineCTraderTransport,
    available_capabilities,
    config,
    show,
    show_value,
    unavailable_capabilities,
)
from app.services.brokers import BrokerId, CTraderBrokerAdapter


async def example_verified_lifecycle() -> None:
    """Connect, verify the session, read platform truth, and disconnect."""
    transport = OfflineCTraderTransport()
    adapter = CTraderBrokerAdapter(
        config(BrokerId.CTRADER), available_capabilities(), transport=transport
    )
    show("connect", await adapter.connect())
    show_value("is-connected", await adapter.is_connected(), None)

    platform = await adapter.get_platform_info()
    show_value(
        "platform",
        platform,
        f"{platform.data.provider_name}/{platform.data.environment.value}"
        if platform.data
        else None,
    )
    show("ping", await adapter.ping())
    show("disconnect", await adapter.disconnect())
    print("transport released", transport.closed)


async def example_unreleased_capability_fails_closed() -> None:
    """A gated capability returns unsupported without a provider request."""
    transport = OfflineCTraderTransport()
    adapter = CTraderBrokerAdapter(
        config(BrokerId.CTRADER), unavailable_capabilities(), transport=transport
    )
    show("gated-platform", await adapter.get_platform_info())
    print("provider requests while gated", len(transport.requests))


async def main() -> None:
    """Exercise every FEAT-BRK-03 operation offline."""
    await example_verified_lifecycle()
    await example_unreleased_capability_fails_closed()


if __name__ == "__main__":
    asyncio.run(main())
