"""FEAT-BRK-02: exercise the MT5 lifecycle and account diagnostics surface.

Runs the genuine `MT5BrokerAdapter` against recorded provider payloads served by
an offline transport, so real session verification, account mapping, balance and
permission decoding all execute without a terminal, network, or credential.
"""

import asyncio

from _support import (
    OfflineMT5Transport,
    available_capabilities,
    config,
    show,
    show_value,
    unavailable_capabilities,
)
from app.services.brokers import BrokerId, MT5BrokerAdapter


async def example_verified_lifecycle_and_account_reads() -> None:
    """Connect, read genuine mapped account state, and release the session."""
    transport = OfflineMT5Transport()
    adapter = MT5BrokerAdapter(
        config(BrokerId.MT5), available_capabilities(), transport=transport
    )
    show("connect", await adapter.connect())

    account = await adapter.get_account_info()
    show_value(
        "account",
        account,
        f"id={account.data.account_id} equity={account.data.equity}"
        if account.data
        else None,
    )

    balances = await adapter.get_balances()
    show_value(
        "balances",
        balances,
        f"{balances.data[0].asset}={balances.data[0].total}" if balances.data else None,
    )

    permissions = await adapter.get_permissions()
    show_value(
        "permissions",
        permissions,
        f"trade_write={permissions.data.trade_write}" if permissions.data else None,
    )

    show("last-error", await adapter.get_last_error())
    show("disconnect", await adapter.disconnect())
    print("provider calls", len(transport.calls))


async def example_unreleased_capability_fails_closed() -> None:
    """An unavailable capability returns unsupported without a provider call."""
    transport = OfflineMT5Transport()
    adapter = MT5BrokerAdapter(
        config(BrokerId.MT5), unavailable_capabilities(), transport=transport
    )
    show("gated-balances", await adapter.get_balances())
    print("provider calls while gated", len(transport.calls))


async def main() -> None:
    """Exercise every FEAT-BRK-02 operation offline."""
    await example_verified_lifecycle_and_account_reads()
    await example_unreleased_capability_fails_closed()


if __name__ == "__main__":
    asyncio.run(main())
