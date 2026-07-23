"""WF-BRK-006: stream connection events."""

import asyncio

import _bootstrap  # noqa: F401
from app.services.brokers import BrokerId, create_broker_adapter
from wf_support import build_mt5_connection_config, print_result

_EXPECTED_EVENT_COUNT = 3


async def _run() -> None:
    """Capture a few connection lifecycle events from the adapter."""
    created = create_broker_adapter(BrokerId.MT5, build_mt5_connection_config())
    if created.data is None:
        print("WF-BRK-006: adapter creation failed")
        print_result("WF-BRK-006", created)
        return

    adapter = created.data
    observed: list[tuple[str, str]] = []

    async def consume_events() -> None:
        async for event in adapter.connection_events():
            observed.append((str(event.previous_state), str(event.new_state)))
            print(f"WF-BRK-006: event {event.previous_state} -> {event.new_state}")
            if len(observed) >= _EXPECTED_EVENT_COUNT:
                break

    consumer = asyncio.create_task(consume_events())
    connect_result = await adapter.connect()
    print_result("WF-BRK-006: connect", connect_result)
    disconnect_result = await adapter.disconnect()
    print_result("WF-BRK-006: disconnect", disconnect_result)

    try:
        await asyncio.wait_for(consumer, timeout=2.0)
    except TimeoutError:
        print("WF-BRK-006: event stream timed out before 3 events")
        consumer.cancel()


def main() -> None:
    """Execute WF-BRK-006 demonstration."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
