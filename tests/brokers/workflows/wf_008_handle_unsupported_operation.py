"""WF-BRK-008: handle unsupported operations without provider calls."""

import asyncio

import _bootstrap  # noqa: F401
from app.services.brokers import BrokerId, create_broker_adapter
from wf_support import build_mt5_connection_config, print_result


async def _run() -> None:
    """Try an unsupported write and show canonical fail-closed output."""
    created = create_broker_adapter(BrokerId.MT5, build_mt5_connection_config())
    if created.data is None:
        print("WF-BRK-008: adapter creation failed")
        print_result("WF-BRK-008", created)
        return

    adapter = created.data
    cancel_result = await adapter.cancel_order("ticket-001")
    print_result("WF-BRK-008: cancel_order", cancel_result)


def main() -> None:
    """Execute WF-BRK-008 demonstration."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
