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
    bus = EventBus()
    received: list[str] = []

    def sync_handler(event: SampleFactEvent) -> None:
        received.append(f"sync:{event.message}")

    async def async_handler(event: SampleFactEvent) -> None:
        await asyncio.sleep(0.01)
        received.append(f"async:{event.message}")

    def failing_handler(_event: SampleFactEvent) -> None:
        raise RuntimeError("Intentional handler failure")

    bus.subscribe(SampleFactEvent, sync_handler)
    bus.subscribe(SampleFactEvent, async_handler)
    bus.subscribe(SampleFactEvent, failing_handler)
    await bus.publish(SampleFactEvent("hello"))
    assert "sync:hello" in received
    assert "async:hello" in received


@pytest.mark.asyncio
async def test_dispatch_modes_are_isolated_for_same_event_type() -> None:
    bus = EventBus()
    calls: list[str] = []

    def publish_handler(_event: SampleFactEvent) -> None:
        calls.append("publish")

    def serial_handler(_event: SampleFactEvent) -> None:
        calls.append("serial")

    def parallel_handler(_event: SampleFactEvent) -> None:
        calls.append("parallel")

    bus.subscribe(SampleFactEvent, publish_handler, mode=EventMode.PUBLISH)
    bus.subscribe(SampleFactEvent, serial_handler, mode=EventMode.SERIAL)
    bus.subscribe(SampleFactEvent, parallel_handler, mode=EventMode.PARALLEL)

    await bus.publish(SampleFactEvent("one"))
    assert calls == ["publish"]
    await bus.dispatch_serial(SampleFactEvent("two"))
    assert calls == ["publish", "serial"]
    await bus.dispatch_parallel(SampleFactEvent("three"))
    assert calls == ["publish", "serial", "parallel"]


@pytest.mark.asyncio
async def test_exact_disposer_removes_only_one_duplicate_handler_registration() -> None:
    bus = EventBus()
    calls: list[str] = []

    def handler(_event: SampleFactEvent) -> None:
        calls.append("called")

    dispose_publish = bus.subscribe(SampleFactEvent, handler, mode=EventMode.PUBLISH)
    bus.subscribe(SampleFactEvent, handler, mode=EventMode.SERIAL)
    assert bus.listener_count(SampleFactEvent) == 2

    dispose_publish()
    assert bus.listener_count(SampleFactEvent) == 1
    await bus.publish(SampleFactEvent("ignored"))
    assert calls == []
    await bus.dispatch_serial(SampleFactEvent("kept"))
    assert calls == ["called"]


@pytest.mark.asyncio
async def test_event_bus_dispatch_serial() -> None:
    bus = EventBus()
    order: list[int] = []

    async def h1(_event: SampleFactEvent) -> None:
        await asyncio.sleep(0.01)
        order.append(1)

    def h2(_event: SampleFactEvent) -> None:
        order.append(2)

    bus.subscribe(SampleFactEvent, h1, mode=EventMode.SERIAL)
    bus.subscribe(SampleFactEvent, h2, mode=EventMode.SERIAL)
    await bus.dispatch_serial(SampleFactEvent("run"))
    assert order == [1, 2]


@pytest.mark.asyncio
async def test_event_bus_dispatch_pipeline_transformation_and_short_circuit() -> None:
    bus = EventBus()

    def add_tax(event: PolicyProposalEvent) -> PolicyProposalEvent:
        return PolicyProposalEvent(amount=event.amount * 1.1)

    def discount(event: PolicyProposalEvent) -> PolicyProposalEvent:
        return PolicyProposalEvent(amount=event.amount - 5.0)

    bus.subscribe(PolicyProposalEvent, add_tax, mode=EventMode.PIPELINE)
    bus.subscribe(PolicyProposalEvent, discount, mode=EventMode.PIPELINE)
    result = await bus.dispatch_pipeline(PolicyProposalEvent(amount=100.0))
    assert result is not None
    assert result.amount == pytest.approx(105.0)

    rejecting_bus = EventBus()
    rejecting_bus.subscribe(
        PolicyProposalEvent,
        lambda _event: None,
        mode=EventMode.PIPELINE,
    )
    assert await rejecting_bus.dispatch_pipeline(PolicyProposalEvent(10.0)) is None


def test_contributor_registry_generation_safe_disposal() -> None:
    registry = ContributorRegistry[str](name="adapters")
    disposer = registry.register("mt5", "MT5Adapter")
    registry.register("binance", "BinanceAdapter")
    assert registry.require("mt5") == "MT5Adapter"
    assert registry.list_keys() == ("mt5", "binance")

    with pytest.raises(ValueError, match="already registered"):
        registry.register("mt5", "Duplicate")
    with pytest.raises(KeyError, match="not found"):
        registry.require("unknown")

    disposer()
    assert registry.get("mt5") is None
    assert registry.list_keys() == ("binance",)
