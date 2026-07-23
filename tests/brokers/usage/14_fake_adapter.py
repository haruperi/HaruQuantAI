"""FEAT-BRK-14: exercise the deterministic fake broker adapter.

Demonstrates the complete protocol surface, per-operation fixture and error
injection, bounded FIFO subscriptions, instance isolation, and the fail-closed
capability gate that error injection can never bypass.
"""

import asyncio

from _support import (
    available_capabilities,
    config,
    show,
    show_value,
    unavailable_capabilities,
)
from app.services.brokers import (
    BrokerCapabilityId,
    BrokerError,
    BrokerErrorCode,
    BrokerId,
)
from app.services.brokers.testing import FakeBrokerAdapter

_CONFIG = config(BrokerId.YAHOO)


def _fake(**kwargs: object) -> FakeBrokerAdapter:
    """Build one isolated fake adapter with an available capability map."""
    return FakeBrokerAdapter(_CONFIG, available_capabilities(), **kwargs)  # type: ignore[arg-type]


async def example_complete_protocol_surface() -> None:
    """Every canonical operation exists on the fake adapter."""
    fake = _fake()
    present = sum(
        1 for operation in BrokerCapabilityId if hasattr(fake, operation.value)
    )
    print("operations exposed", present, "of", len(tuple(BrokerCapabilityId)))
    show("connect", await fake.connect())
    show("disconnect", await fake.disconnect())


async def example_fixture_and_error_injection() -> None:
    """A selected operation returns a chosen fixture or canonical failure."""
    fake = _fake(fixtures={BrokerCapabilityId.GET_QUOTE: "recorded-quote"})
    await fake.connect()
    show_value("fixture", await fake.get_quote("EURUSD"), "recorded-quote")

    fake.inject_error(
        BrokerCapabilityId.GET_QUOTE,
        BrokerError(code=BrokerErrorCode.BROKER_TIMEOUT, message="timeout"),
    )
    show("injected-error", await fake.get_quote("EURUSD"))

    fake.inject_error(BrokerCapabilityId.GET_QUOTE, None)
    show("cleared-error", await fake.get_quote("EURUSD"))


async def example_bounded_subscription() -> None:
    """Fake streams enforce the same backpressure semantics as real adapters."""
    fake = _fake()
    await fake.connect()
    opened = await fake.subscribe_quotes(("EURUSD",))
    handle = opened.data
    if handle is None:
        return
    print("buffer size", handle.info.buffer_size)

    accepted = 0
    for index in range(handle.info.buffer_size + 1):
        if await fake.publish(handle.info.subscription_id, index):
            accepted += 1
    print(
        "accepted", accepted, "resync required", handle.info.resynchronization_required
    )

    events = [event async for event in handle.events()]
    terminal = events[-1]
    print(
        "terminal", terminal.code.value if isinstance(terminal, BrokerError) else None
    )


async def example_instances_are_isolated() -> None:
    """State never leaks between two independent fake adapters."""
    first = _fake()
    second = _fake()
    await first.connect()
    await second.connect()
    await first.subscribe_quotes(("EURUSD",))
    print(
        "first open",
        len((await first.list_subscriptions()).data or ()),
        "second open",
        len((await second.list_subscriptions()).data or ()),
    )


async def example_injection_cannot_bypass_the_capability_gate() -> None:
    """A fixture never overrides a capability declared UNAVAILABLE."""
    gated = FakeBrokerAdapter(
        _CONFIG,
        unavailable_capabilities(),
        fixtures={BrokerCapabilityId.GET_QUOTE: "recorded-quote"},
    )
    show("gated-fixture", await gated.get_quote("EURUSD"))
    gated.inject_error(
        BrokerCapabilityId.GET_QUOTE,
        BrokerError(code=BrokerErrorCode.BROKER_TIMEOUT, message="timeout"),
    )
    show("gated-injected-error", await gated.get_quote("EURUSD"))


async def main() -> None:
    """Exercise every FEAT-BRK-14 operation."""
    await example_complete_protocol_surface()
    await example_fixture_and_error_injection()
    await example_bounded_subscription()
    await example_instances_are_isolated()
    await example_injection_cannot_bypass_the_capability_gate()


if __name__ == "__main__":
    asyncio.run(main())
