"""Bounded FIFO broker subscription implementation."""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import replace

from app.services.brokers.contracts import (
    BrokerCapabilityId,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerId,
    BrokerResult,
    BrokerSubscriptionInfo,
)
from app.utils import generate_id, logger, utc_now

type _Event[TEvent] = TEvent | BrokerError | None


class _BrokerSubscription[TEvent]:
    """One adapter-owned bounded FIFO provider-event stream."""

    def __init__(
        self,
        *,
        broker: BrokerId,
        environment: BrokerEnvironment,
        adapter_version: str,
        info: BrokerSubscriptionInfo,
        unsubscribe_callback: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        """Initialize the _BrokerSubscription instance.

        Args:
            broker: Value supplied to the operation.
            environment: Value supplied to the operation.
            adapter_version: Value supplied to the operation.
            info: Value supplied to the operation.
            unsubscribe_callback: Value supplied to the operation.
        """
        self._broker = broker
        self._environment = environment
        self._adapter_version = adapter_version
        self._info = info
        self._unsubscribe_callback = unsubscribe_callback
        self._queue: asyncio.Queue[_Event[TEvent]] = asyncio.Queue(info.buffer_size + 1)
        self._closed = False
        self._terminal_enqueued = False
        self._lock = asyncio.Lock()

    @property
    def info(self) -> BrokerSubscriptionInfo:
        """Return immutable current subscription metadata."""
        return self._info

    async def publish(self, event: TEvent) -> bool:
        """Publish one event, terminating explicitly on overflow.

        Returns:
            Whether the event was accepted without terminal overflow.
        """
        async with self._lock:
            if self._closed:
                return False
            if self._queue.qsize() >= self._info.buffer_size:
                self._info = replace(
                    self._info,
                    active=False,
                    resynchronization_required=True,
                )
                self._closed = True
                logger.bind(
                    broker=self._broker.value,
                    environment=self._environment.value,
                    subscription_id=self._info.subscription_id,
                    capability=self._info.capability.value,
                    result="error",
                    provider_code=BrokerErrorCode.BROKER_BACKPRESSURE.value,
                ).warning("Subscription buffer overflow; resynchronization required")
                await self._enqueue_terminal(
                    BrokerError(
                        code=BrokerErrorCode.BROKER_BACKPRESSURE,
                        message=(
                            "Subscription buffer overflow; resynchronization required"
                        ),
                        capability=self._info.capability,
                    )
                )
                return False
            self._queue.put_nowait(event)
            self._info = replace(
                self._info,
                delivery_sequence=self._info.delivery_sequence + 1,
            )
            return True

    async def fail(self, error: BrokerError) -> None:
        """Yield one terminal provider error and close the stream."""
        async with self._lock:
            if self._closed:
                return
            self._closed = True
            self._info = replace(self._info, active=False)
            logger.bind(
                broker=self._broker.value,
                environment=self._environment.value,
                subscription_id=self._info.subscription_id,
                capability=self._info.capability.value,
                result="error",
                provider_code=error.code.value,
            ).warning("Subscription failed with terminal provider error")
            await self._enqueue_terminal(error)

    async def _enqueue_terminal(self, error: BrokerError) -> None:
        """Handle enqueue terminal.

        Args:
            error: Value supplied to the operation.
        """
        if self._terminal_enqueued:
            return
        self._queue.put_nowait(error)
        self._terminal_enqueued = True

    async def events(self) -> AsyncIterator[TEvent | BrokerError]:
        """Yield events in FIFO order until a terminal marker or error.

        Yields:
            Canonical provider events or one terminal error.
        """
        while True:
            event = await self._queue.get()
            if event is None:
                return
            yield event
            if isinstance(event, BrokerError):
                return

    async def unsubscribe(self) -> BrokerResult[None]:
        """Idempotently stop the exact subscription and provider stream.

        Returns:
            Canonical successful unsubscribe result.
        """
        async with self._lock:
            if not self._closed and self._unsubscribe_callback is not None:
                await self._unsubscribe_callback()
            self._closed = True
            self._info = replace(self._info, active=False)
            if not self._terminal_enqueued:
                self._queue.put_nowait(None)
        logger.bind(
            broker=self._broker.value,
            environment=self._environment.value,
            subscription_id=self._info.subscription_id,
            capability=self._info.capability.value,
            result="success",
        ).info("Subscription unsubscribed and provider stream released")
        return BrokerResult(
            status="success",
            broker=self._broker,
            operation=BrokerCapabilityId.UNSUBSCRIBE,
            request_id=generate_id("req"),
            timestamp=utc_now(),
            environment=self._environment,
            adapter_version=self._adapter_version,
        )
