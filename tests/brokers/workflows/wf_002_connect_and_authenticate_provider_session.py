"""WF-BRK-002: connect and authenticate provider session."""

import asyncio

import _bootstrap  # noqa: F401
from app.services.brokers import BrokerConnectionState, BrokerId, create_broker_adapter
from wf_support import (
    build_mt5_connection_config,
    print_connection_status,
    print_result,
)


async def _run() -> None:
    """Run a bounded connect -> status -> disconnect sequence."""
    created = create_broker_adapter(BrokerId.MT5, build_mt5_connection_config())
    if created.data is None:
        print("WF-BRK-002: adapter creation failed")
        print_result("WF-BRK-002", created)
        return

    adapter = created.data
    initial = await adapter.get_connection_status()
    print_connection_status("WF-BRK-002: initial", initial)

    connect_result = await adapter.connect()
    print_result("WF-BRK-002: connect", connect_result)
    if connect_result.is_success:
        connected = await adapter.get_connection_status()
        print_connection_status("WF-BRK-002: connected", connected)
    else:
        print("WF-BRK-002: skipping post-connect checks")

    disconnect_result = await adapter.disconnect()
    print_result("WF-BRK-002: disconnect", disconnect_result)

    final_state = await adapter.get_connection_status()
    print_connection_status("WF-BRK-002: final", final_state)
    if final_state.data is not None:
        print(
            "WF-BRK-002: final state",
            final_state.data.state == BrokerConnectionState.DISCONNECTED,
        )


def main() -> None:
    """Execute WF-BRK-002 demonstration."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
