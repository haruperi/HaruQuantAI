"""Tests for scoped event subscription and publishing via FeatureContext."""

from dataclasses import dataclass

import pytest

from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus, EventMode
from app.kernel.feature import FeatureSpec
from app.kernel.scope import FeatureScope


@dataclass(frozen=True, slots=True)
class CustomTestEvent:
    payload: str


@dataclass(frozen=True, slots=True)
class PriceProposalEvent:
    price: float


@pytest.mark.asyncio
async def test_context_subscribe_and_scope_cleanup() -> None:
    """Test that event subscription is automatically disposed when scope closes."""
    bus = EventBus()
    spec = FeatureSpec(
        feature_id="FEAT-SYS-TEST_EVENTS",
        domain="system",
        provides=frozenset(),
    )
    scope = FeatureScope(owner_id=spec.feature_id)
    ctx = DefaultFeatureContext(spec=spec, scope=scope, event_bus=bus)

    received: list[str] = []

    def on_event(event: CustomTestEvent) -> None:
        received.append(event.payload)

    ctx.subscribe(CustomTestEvent, on_event)
    assert bus.listener_count(CustomTestEvent) == 1

    # 1. Publish while scope is open
    await ctx.publish(CustomTestEvent("first_message"))
    assert received == ["first_message"]

    # 2. Close scope (simulating feature unmount)
    await scope.close()
    assert bus.listener_count(CustomTestEvent) == 0

    # 3. Publish after unmount -> listener should not be called
    await bus.publish(CustomTestEvent("second_message"))
    assert received == ["first_message"]


@pytest.mark.asyncio
async def test_context_dispatch_pipeline() -> None:
    """Test dispatching pipeline from FeatureContext."""
    bus = EventBus()
    spec = FeatureSpec(
        feature_id="FEAT-RISK-POLICY_TEST",
        domain="risk",
        provides=frozenset(),
    )
    scope = FeatureScope(owner_id=spec.feature_id)
    ctx = DefaultFeatureContext(spec=spec, scope=scope, event_bus=bus)

    def cap_price(event: PriceProposalEvent) -> PriceProposalEvent:
        if event.price > 100.0:
            return PriceProposalEvent(price=100.0)
        return event

    ctx.subscribe(PriceProposalEvent, cap_price, mode=EventMode.PIPELINE)

    result = await ctx.dispatch_pipeline(PriceProposalEvent(price=150.0))
    assert result is not None
    assert result.price == 100.0

    await scope.close()
