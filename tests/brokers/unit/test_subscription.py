"""Bounded subscription runtime tests."""

import asyncio
from datetime import UTC, datetime

from app.services.brokers import (
    BrokerCapabilityId,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerId,
    BrokerSubscriptionInfo,
)
from app.services.brokers.runtime.subscription import _BrokerSubscription


def test_subscription_overflow_is_terminal_and_requires_resync() -> None:
    """Overflow is explicit and never silently drops into continued delivery."""

    async def exercise() -> None:
        subscription = _BrokerSubscription[int](
            broker=BrokerId.YAHOO,
            environment=BrokerEnvironment.SANDBOX,
            adapter_version="1",
            info=BrokerSubscriptionInfo(
                subscription_id="sub",
                capability=BrokerCapabilityId.SUBSCRIBE_QUOTES,
                symbols=("A",),
                created_at=datetime.now(UTC),
                buffer_size=1,
            ),
        )
        assert await subscription.publish(1)
        assert not await subscription.publish(2)
        events = [event async for event in subscription.events()]
        assert len(events) == 1
        assert isinstance(events[0], BrokerError)
        assert events[0].code == BrokerErrorCode.BROKER_BACKPRESSURE
        assert subscription.info.resynchronization_required

    asyncio.run(exercise())


def test_subscription_unsubscribe_is_idempotent() -> None:
    """Repeated unsubscribe closes only the owned handle."""

    async def exercise() -> None:
        subscription = _BrokerSubscription[int](
            broker=BrokerId.YAHOO,
            environment=BrokerEnvironment.SANDBOX,
            adapter_version="1",
            info=BrokerSubscriptionInfo(
                subscription_id="sub",
                capability=BrokerCapabilityId.SUBSCRIBE_QUOTES,
                symbols=("A",),
                created_at=datetime.now(UTC),
                buffer_size=1,
            ),
        )
        assert (await subscription.unsubscribe()).is_success
        assert (await subscription.unsubscribe()).is_success

    asyncio.run(exercise())


def test_subscription_unsubscribe_invokes_callback_once() -> None:
    """The injected unsubscribe callback runs only on the first call."""

    async def exercise() -> None:
        calls = 0

        async def _callback() -> None:
            nonlocal calls
            calls += 1

        subscription = _BrokerSubscription[int](
            broker=BrokerId.YAHOO,
            environment=BrokerEnvironment.SANDBOX,
            adapter_version="1",
            info=BrokerSubscriptionInfo(
                subscription_id="sub",
                capability=BrokerCapabilityId.SUBSCRIBE_QUOTES,
                symbols=("A",),
                created_at=datetime.now(UTC),
                buffer_size=1,
            ),
            unsubscribe_callback=_callback,
        )
        await subscription.unsubscribe()
        await subscription.unsubscribe()
        assert calls == 1

    asyncio.run(exercise())


def test_subscription_fail_yields_one_terminal_error() -> None:
    """An explicit provider failure yields exactly one terminal error."""

    async def exercise() -> None:
        subscription = _BrokerSubscription[int](
            broker=BrokerId.YAHOO,
            environment=BrokerEnvironment.SANDBOX,
            adapter_version="1",
            info=BrokerSubscriptionInfo(
                subscription_id="sub",
                capability=BrokerCapabilityId.SUBSCRIBE_QUOTES,
                symbols=("A",),
                created_at=datetime.now(UTC),
                buffer_size=2,
            ),
        )
        assert await subscription.publish(1)
        await subscription.fail(
            BrokerError(
                code=BrokerErrorCode.BROKER_CONNECTION_LOST,
                message="terminal",
            )
        )
        events = [event async for event in subscription.events()]
        assert len(events) == 2
        assert events[0] == 1
        assert isinstance(events[1], BrokerError)
        assert not subscription.info.active
        assert not await subscription.publish(2)

    asyncio.run(exercise())
