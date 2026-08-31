"""Unit tests for typed EventBus and ContributorRegistry."""

import asyncio
from dataclasses import dataclass

import pytest
from app.kernel.events import ContributorRegistry, EventBus, EventMode


@dataclass(frozen=True, slots=True)
class SampleFactEvent:
    message: str


@dataclass(frozen=True, slots=True)
class PolicyProposalEvent:
    amount: float
    is_valid: bool = True


@pytest.mark.asyncio
async def test_event_bus_publish_observational() -> None:
    """Test publish mode dispatches to multiple handlers concurrently with error isolation."""
    bus = EventBus()
    received: list[str] = []

    def sync_handler(event: SampleFactEvent) -> None:
        received.append(f"sync:{event.message}")

    async def async_handler(event: SampleFactEvent) -> None:
        await asyncio.sleep(0.01)
        received.append(f"async:{event.message}")

    def failing_handler(_event: SampleFactEvent) -> None:
        msg = "Intentional handler failure"
        raise RuntimeError(msg)

    bus.subscribe(SampleFactEvent, sync_handler)
    bus.subscribe(SampleFactEvent, async_handler)
    bus.subscribe(SampleFactEvent, failing_handler)

    assert bus.listener_count(SampleFactEvent) == 3

    # Publish should not raise despite failing_handler
    await bus.publish(SampleFactEvent("hello"))

    assert "sync:hello" in received
    assert "async:hello" in received


@pytest.mark.asyncio
async def test_event_bus_unsubscribe_and_disposer() -> None:
    """Test unsubscribing via explicit call and via returned disposer."""
    bus = EventBus()
    calls: list[str] = []

    def handler1(event: SampleFactEvent) -> None:
        calls.append("h1")

    def handler2(event: SampleFactEvent) -> None:
        calls.append("h2")

    disposer1 = bus.subscribe(SampleFactEvent, handler1)
    bus.subscribe(SampleFactEvent, handler2)

    await bus.publish(SampleFactEvent("first"))
    assert calls == ["h1", "h2"]

    calls.clear()
    disposer1()  # Remove handler1
    await bus.publish(SampleFactEvent("second"))
    assert calls == ["h2"]

    calls.clear()
    bus.unsubscribe(SampleFactEvent, handler2)  # Remove handler2
    await bus.publish(SampleFactEvent("third"))
    assert calls == []
    assert bus.listener_count() == 0


@pytest.mark.asyncio
async def test_event_bus_dispatch_serial() -> None:
    """Test dispatch_serial runs handlers sequentially in registration order."""
    bus = EventBus()
    order: list[int] = []

    async def h1(_e: SampleFactEvent) -> None:
        await asyncio.sleep(0.02)
        order.append(1)

    def h2(_e: SampleFactEvent) -> None:
        order.append(2)

    bus.subscribe(SampleFactEvent, h1, mode=EventMode.SERIAL)
    bus.subscribe(SampleFactEvent, h2, mode=EventMode.SERIAL)

    await bus.dispatch_serial(SampleFactEvent("run"))
    assert order == [1, 2]


@pytest.mark.asyncio
async def test_event_bus_dispatch_parallel() -> None:
    """Test dispatch_parallel executes handlers concurrently."""
    bus = EventBus()
    results: list[int] = []

    async def task_a(_e: SampleFactEvent) -> None:
        results.append(10)

    async def task_b(_e: SampleFactEvent) -> None:
        results.append(20)

    bus.subscribe(SampleFactEvent, task_a, mode=EventMode.PARALLEL)
    bus.subscribe(SampleFactEvent, task_b, mode=EventMode.PARALLEL)

    await bus.dispatch_parallel(SampleFactEvent("par"))
    assert set(results) == {10, 20}


@pytest.mark.asyncio
async def test_event_bus_dispatch_pipeline_transformation() -> None:
    """Test pipeline transforms event payload through handlers."""
    bus = EventBus()

    def policy_add_tax(event: PolicyProposalEvent) -> PolicyProposalEvent:
        return PolicyProposalEvent(amount=event.amount * 1.1, is_valid=True)

    def policy_discount(event: PolicyProposalEvent) -> PolicyProposalEvent:
        return PolicyProposalEvent(amount=event.amount - 5.0, is_valid=True)

    bus.subscribe(PolicyProposalEvent, policy_add_tax, mode=EventMode.PIPELINE)
    bus.subscribe(PolicyProposalEvent, policy_discount, mode=EventMode.PIPELINE)

    initial = PolicyProposalEvent(amount=100.0)
    final = await bus.dispatch_pipeline(initial)

    assert final is not None
    # 100 * 1.1 = 110 - 5 = 105
    assert final.amount == pytest.approx(105.0)


@pytest.mark.asyncio
async def test_event_bus_dispatch_pipeline_short_circuit() -> None:
    """Test pipeline stops if any handler returns None."""
    bus = EventBus()

    def policy_reject(_event: PolicyProposalEvent) -> None:
        return None

    def policy_never_reached(event: PolicyProposalEvent) -> PolicyProposalEvent:
        return PolicyProposalEvent(amount=999.0)

    bus.subscribe(PolicyProposalEvent, policy_reject, mode=EventMode.PIPELINE)
    bus.subscribe(PolicyProposalEvent, policy_never_reached, mode=EventMode.PIPELINE)

    initial = PolicyProposalEvent(amount=100.0)
    result = await bus.dispatch_pipeline(initial)
    assert result is None


def test_contributor_registry() -> None:
    """Test ContributorRegistry registration, retrieval, and disposal."""
    registry = ContributorRegistry[str](name="adapters")

    disposer = registry.register("mt5", "MT5Adapter")
    registry.register("binance", "BinanceAdapter")

    assert registry.get("mt5") == "MT5Adapter"
    assert registry.require("binance") == "BinanceAdapter"
    assert registry.list_keys() == ("mt5", "binance")

    # Duplicate key raises ValueError
    with pytest.raises(ValueError, match="already registered"):
        registry.register("mt5", "Duplicate")

    # Missing key raises KeyError
    with pytest.raises(KeyError, match="not found"):
        registry.require("unknown")

    # Test disposer
    disposer()
    assert registry.get("mt5") is None
    assert registry.list_keys() == ("binance",)


@pytest.mark.asyncio
async def test_event_mode_strict_isolation() -> None:
    """Characterization test: event dispatch must strictly isolate and only invoke matching modes."""
    bus = EventBus()
    invocations: list[str] = []

    def pub_handler(_e: SampleFactEvent) -> None:
        invocations.append("publish")

    def serial_handler(_e: SampleFactEvent) -> None:
        invocations.append("serial")

    def parallel_handler(_e: SampleFactEvent) -> None:
        invocations.append("parallel")

    def pipeline_handler(e: SampleFactEvent) -> SampleFactEvent:
        invocations.append("pipeline")
        return e

    bus.subscribe(SampleFactEvent, pub_handler, mode=EventMode.PUBLISH)
    bus.subscribe(SampleFactEvent, serial_handler, mode=EventMode.SERIAL)
    bus.subscribe(SampleFactEvent, parallel_handler, mode=EventMode.PARALLEL)
    bus.subscribe(SampleFactEvent, pipeline_handler, mode=EventMode.PIPELINE)

    # 1. Calling publish() must ONLY invoke PUBLISH mode handlers
    invocations.clear()
    await bus.publish(SampleFactEvent("test_publish"))
    assert invocations == ["publish"], (
        f"publish() invoked non-publish handlers: {invocations}"
    )

    # 2. Calling dispatch_serial() must ONLY invoke SERIAL mode handlers
    invocations.clear()
    await bus.dispatch_serial(SampleFactEvent("test_serial"))
    assert invocations == ["serial"], (
        f"dispatch_serial() invoked non-serial handlers: {invocations}"
    )

    # 3. Calling dispatch_parallel() must ONLY invoke PARALLEL mode handlers
    invocations.clear()
    await bus.dispatch_parallel(SampleFactEvent("test_parallel"))
    assert invocations == ["parallel"], (
        f"dispatch_parallel() invoked non-parallel handlers: {invocations}"
    )

    # 4. Calling dispatch_pipeline() must ONLY invoke PIPELINE mode handlers
    invocations.clear()
    await bus.dispatch_pipeline(SampleFactEvent("test_pipeline"))
    assert invocations == ["pipeline"], (
        f"dispatch_pipeline() invoked non-pipeline handlers: {invocations}"
    )


@pytest.mark.asyncio
async def test_duplicate_subscription_exact_token_disposal() -> None:
    """Characterization test: disposing one subscription should not unsubscribe identical duplicate handlers."""
    bus = EventBus()
    calls: list[int] = []

    def shared_handler(_e: SampleFactEvent) -> None:
        calls.append(1)

    disposer1 = bus.subscribe(SampleFactEvent, shared_handler, mode=EventMode.PUBLISH)
    disposer2 = bus.subscribe(SampleFactEvent, shared_handler, mode=EventMode.PUBLISH)

    # Both subscriptions should fire
    await bus.publish(SampleFactEvent("both"))
    assert len(calls) == 2

    # Dispose ONLY the first subscription
    calls.clear()
    disposer1()

    # The second subscription MUST still receive the event
    await bus.publish(SampleFactEvent("one_left"))
    assert len(calls) == 1, (
        f"Expected exactly 1 call after disposing first token, got {len(calls)}"
    )

    # Dispose second subscription
    calls.clear()
    disposer2()
    await bus.publish(SampleFactEvent("none_left"))
    assert len(calls) == 0


@pytest.mark.asyncio
async def test_unsubscribe_during_dispatch_is_safe() -> None:
    """Test that disposing a subscription from within a handler during active dispatch does not corrupt iteration."""
    bus = EventBus()
    disposer: object = None
    calls: list[str] = []

    def self_unsubscribing_handler(_e: SampleFactEvent) -> None:
        calls.append("self_unsub")
        if callable(disposer):
            disposer()

    def second_handler(_e: SampleFactEvent) -> None:
        calls.append("second")

    disposer = bus.subscribe(SampleFactEvent, self_unsubscribing_handler)
    bus.subscribe(SampleFactEvent, second_handler)

    # First dispatch invokes both handlers, self_unsub removes itself
    await bus.publish(SampleFactEvent("first"))
    assert calls == ["self_unsub", "second"]

    # Second dispatch invokes only second_handler
    calls.clear()
    await bus.publish(SampleFactEvent("second"))
    assert calls == ["second"]


def test_listener_count_by_mode() -> None:
    """Test listener_count filtering by EventMode."""
    bus = EventBus()

    bus.subscribe(SampleFactEvent, lambda _e: None, mode=EventMode.PUBLISH)
    bus.subscribe(SampleFactEvent, lambda _e: None, mode=EventMode.SERIAL)
    bus.subscribe(PolicyProposalEvent, lambda _e: _e, mode=EventMode.PIPELINE)

    assert bus.listener_count() == 3
    assert bus.listener_count(mode=EventMode.PUBLISH) == 1
    assert bus.listener_count(mode=EventMode.SERIAL) == 1
    assert bus.listener_count(mode=EventMode.PIPELINE) == 1
    assert bus.listener_count(mode=EventMode.PARALLEL) == 0
    assert bus.listener_count(SampleFactEvent, mode=EventMode.PUBLISH) == 1
    assert bus.listener_count(PolicyProposalEvent, mode=EventMode.PUBLISH) == 0
