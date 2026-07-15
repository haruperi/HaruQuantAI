"""WF-BRK-006: stream provider and connection events."""

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


def _subscription(buffer_size: int) -> _BrokerSubscription[int]:
    return _BrokerSubscription[int](
        broker=BrokerId.YAHOO,
        environment=BrokerEnvironment.SANDBOX,
        adapter_version="1.0.0",
        info=BrokerSubscriptionInfo(
            subscription_id="sub-1",
            capability=BrokerCapabilityId.SUBSCRIBE_QUOTES,
            symbols=("EURUSD",),
            created_at=datetime.now(UTC),
            buffer_size=buffer_size,
        ),
    )


def test_streaming_reports_backpressure_and_resync() -> None:
    """Buffer overflow terminates the stream and requires resynchronization."""

    async def exercise() -> None:
        subscription = _subscription(buffer_size=1)
        assert await subscription.publish(1)
        assert not await subscription.publish(2)
        events = [event async for event in subscription.events()]
        assert len(events) == 1
        assert events[0].code == BrokerErrorCode.BROKER_BACKPRESSURE
        assert subscription.info.resynchronization_required
        assert not subscription.info.active

    asyncio.run(exercise())


def test_streaming_unknown_subscription_never_affects_others() -> None:
    """Unsubscribing one handle never disturbs an unrelated subscription."""

    async def exercise() -> None:
        first = _subscription(buffer_size=4)
        second = _subscription(buffer_size=4)
        await first.publish(1)
        await first.unsubscribe()
        assert not first.info.active
        assert await second.publish(2)
        assert second.info.active

    asyncio.run(exercise())


def test_streaming_disconnect_terminates_every_owned_subscription() -> None:
    """A simulated disconnect fails every owned subscription, never silently."""

    async def exercise() -> None:
        subscriptions = [_subscription(buffer_size=4) for _ in range(3)]
        error = BrokerError(
            code=BrokerErrorCode.BROKER_CONNECTION_LOST, message="disconnected"
        )
        for subscription in subscriptions:
            await subscription.fail(error)
        for subscription in subscriptions:
            assert not subscription.info.active
            events = [event async for event in subscription.events()]
            assert len(events) == 1
            assert events[0] is error

    asyncio.run(exercise())
