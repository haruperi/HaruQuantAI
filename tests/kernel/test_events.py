# cspell:words awaitables awaitable unregisters
"""Comprehensive unit tests for the EventBus observation mechanism."""

import asyncio
from typing import Any

import pytest
from app.kernel.events import EventBus


class BaseEvent:
    """Base event marker class."""


class DerivedEvent(BaseEvent):
    """Derived event marker class."""


def test_subscribe_and_publish_sync_handler() -> None:
    """Verify that synchronous handlers receive published events."""

    async def scenario() -> None:
        bus = EventBus()
        received: list[str] = []

        bus.subscribe(str, received.append)
        await bus.publish("hello")
        await bus.publish("world")

        assert received == ["hello", "world"]

    asyncio.run(scenario())


def test_subscribe_and_publish_async_handler() -> None:
    """Verify that asynchronous handlers are awaited."""

    async def scenario() -> None:
        bus = EventBus()
        received: list[int] = []

        async def async_handler(event: int) -> None:
            await asyncio.sleep(0.001)
            received.append(event * 2)

        bus.subscribe(int, async_handler)
        await bus.publish(10)
        await bus.publish(20)

        assert received == [20, 40]

    asyncio.run(scenario())


def test_multiple_handlers_ordered() -> None:
    """Verify handlers execute sequentially in order of registration."""

    async def scenario() -> None:
        bus = EventBus()
        order: list[int] = []

        bus.subscribe(str, lambda _: order.append(1))
        bus.subscribe(str, lambda _: order.append(2))
        bus.subscribe(str, lambda _: order.append(3))

        await bus.publish("trigger")
        assert order == [1, 2, 3]

    asyncio.run(scenario())


def test_exact_type_matching() -> None:
    """Verify exact-type matching does not dispatch to base class handlers."""

    async def scenario() -> None:
        bus = EventBus()
        base_received: list[BaseEvent] = []
        derived_received: list[DerivedEvent] = []

        bus.subscribe(BaseEvent, base_received.append)
        bus.subscribe(DerivedEvent, derived_received.append)

        derived = DerivedEvent()
        await bus.publish(derived)

        # Only DerivedEvent handler should receive it, not BaseEvent handler
        assert derived_received == [derived]
        assert base_received == []

        base = BaseEvent()
        await bus.publish(base)
        assert base_received == [base]

    asyncio.run(scenario())


def test_idempotent_disposal() -> None:
    """Verify disposer function can be called repeatedly with no side effects."""

    async def scenario() -> None:
        bus = EventBus()
        received: list[str] = []

        dispose = bus.subscribe(str, received.append)
        assert bus.listener_count(str) == 1
        assert bus.active_listener_count == 1
        assert bus.active_subscription_count == 1

        await bus.publish("first")
        assert received == ["first"]

        dispose()
        assert bus.listener_count(str) == 0
        assert bus.active_listener_count == 0
        assert bus.subscribed_event_types == frozenset()

        # Second invocation is safe and idempotent
        dispose()
        assert bus.listener_count(str) == 0

        await bus.publish("second")
        assert received == ["first"]

    asyncio.run(scenario())


def test_listener_count_and_active_properties() -> None:
    """Verify listener count and subscription set introspection."""
    bus = EventBus()
    assert bus.listener_count() == 0
    assert bus.listener_count(str) == 0
    assert bus.active_listener_count == 0
    assert bus.subscribed_event_types == frozenset()

    d1 = bus.subscribe(str, lambda _: None)
    d2 = bus.subscribe(str, lambda _: None)
    d3 = bus.subscribe(int, lambda _: None)

    assert bus.listener_count() == 3
    assert bus.listener_count(str) == 2
    assert bus.listener_count(int) == 1
    assert bus.listener_count(float) == 0
    assert bus.active_listener_count == 3
    assert bus.active_subscription_count == 3
    assert bus.subscribed_event_types == frozenset({str, int})

    d1()
    assert bus.listener_count(str) == 1
    assert bus.listener_count() == 2

    d2()
    assert bus.listener_count(str) == 0
    assert bus.listener_count() == 1
    assert bus.subscribed_event_types == frozenset({int})

    d3()
    assert bus.listener_count() == 0
    assert bus.subscribed_event_types == frozenset()


def test_snapshot_isolation_unsubscribe_during_publish() -> None:
    """Verify handler can safely unsubscribe itself during its own execution."""

    async def scenario() -> None:
        bus = EventBus()
        disposer: list[Any] = []
        executions: list[str] = []

        def self_removing_handler(event: str) -> None:
            executions.append(f"self:{event}")
            disposer[0]()

        d = bus.subscribe(str, self_removing_handler)
        disposer.append(d)

        await bus.publish("first")
        assert executions == ["self:first"]
        assert bus.listener_count(str) == 0

        await bus.publish("second")
        assert executions == ["self:first"]

    asyncio.run(scenario())


def test_snapshot_isolation_subscribe_during_publish() -> None:
    """Verify new subscriber added during publish is not called in same publish."""

    async def scenario() -> None:
        bus = EventBus()
        log: list[str] = []

        def adding_handler(event: str) -> None:
            log.append(f"adder:{event}")
            bus.subscribe(str, lambda e: log.append(f"late:{e}"))

        bus.subscribe(str, adding_handler)

        await bus.publish("first")
        assert log == ["adder:first"]

        await bus.publish("second")
        # In second publish, both adder and the late subscriber are invoked
        assert log == ["adder:first", "adder:second", "late:second"]

    asyncio.run(scenario())


def test_handler_exception_propagates() -> None:
    """Verify handler exceptions propagate and halt subsequent delivery."""

    async def scenario() -> None:
        bus = EventBus()
        called: list[int] = []

        def failing_handler(_: str) -> None:
            called.append(1)
            raise RuntimeError("handler failed intentionally")

        def second_handler(_: str) -> None:
            called.append(2)

        bus.subscribe(str, failing_handler)
        bus.subscribe(str, second_handler)

        with pytest.raises(RuntimeError, match="handler failed intentionally"):
            await bus.publish("trigger")

        assert called == [1]

    asyncio.run(scenario())


def test_clear() -> None:
    """Verify that clear unregisters all listeners across all types."""
    bus = EventBus()
    bus.subscribe(str, lambda _: None)
    bus.subscribe(int, lambda _: None)
    assert bus.listener_count() == 2

    bus.clear()
    assert bus.listener_count() == 0
    assert bus.subscribed_event_types == frozenset()


def test_publish_unsubscribed_event() -> None:
    """Verify publishing an event type with no listeners is a safe no-op."""

    async def scenario() -> None:
        bus = EventBus()
        # Should complete without error
        await bus.publish("no listeners")

    asyncio.run(scenario())
