"""Bounded subscription streams behave correctly under caller cancellation."""

import asyncio
import contextlib
from datetime import UTC, datetime

from app.services.brokers import (
    BrokerCapabilityId,
    BrokerEnvironment,
    BrokerId,
    BrokerSubscriptionInfo,
)
from app.services.brokers.runtime.subscription import _BrokerSubscription


def _subscription() -> _BrokerSubscription[int]:
    return _BrokerSubscription[int](
        broker=BrokerId.YAHOO,
        environment=BrokerEnvironment.SANDBOX,
        adapter_version="1.0.0",
        info=BrokerSubscriptionInfo(
            subscription_id="sub-cancel",
            capability=BrokerCapabilityId.SUBSCRIBE_QUOTES,
            symbols=("EURUSD",),
            created_at=datetime.now(UTC),
            buffer_size=4,
        ),
    )


def test_cancelling_a_consumer_never_corrupts_subscription_state() -> None:
    """Cancelling an in-progress ``events()`` consumer leaves state usable."""

    async def exercise() -> bool:
        subscription = _subscription()

        async def _consume_forever() -> None:
            async for _event in subscription.events():
                pass

        task = asyncio.create_task(_consume_forever())
        await asyncio.sleep(0)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        result = await subscription.unsubscribe()
        return result.is_success

    assert asyncio.run(exercise())


def test_unsubscribe_while_consuming_ends_the_stream_cleanly() -> None:
    """Unsubscribing mid-stream yields a terminal marker with no further events."""

    async def exercise() -> list[int]:
        subscription = _subscription()
        await subscription.publish(1)

        events: list[int] = []

        async def _consume() -> None:
            async for event in subscription.events():
                events.append(event)

        task = asyncio.create_task(_consume())
        await asyncio.sleep(0)
        await subscription.unsubscribe()
        await task
        return events

    assert asyncio.run(exercise()) == [1]
