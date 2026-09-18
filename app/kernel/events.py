# cspell:words awaitables awaitable unregisters
"""In-process asynchronous event bus with explicit subscription disposal.

This module provides an in-process, publish-subscribe observation mechanism
for loosely coupled feature communication.

Key Design Principles:
- Exact-Type Dispatch: Events are dispatched to handlers registered for the
  exact runtime type (`type(event)`). Subclass inheritance dispatch is not
  performed, keeping dispatch deterministic and fast.
- Sequential Delivery: Handlers for a given event type are executed
  sequentially in registration order. If a handler raises an exception,
  delivery ceases and the exception propagates immediately to the publisher.
- Unified Sync/Async Support: Handlers can be synchronous callables or
  asynchronous coroutines. Awaitables are awaited automatically.
- Idempotent Disposal: `subscribe` returns a zero-argument callable that
  unregisters the subscription. Invoking the disposer multiple times is safe
  and has no side effects.
- Snapshot Isolation: Handlers are copied to a snapshot before dispatch,
  allowing handlers to safely unsubscribe themselves or register new
  subscribers during event processing without mutating the active iteration.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import cast

type Handler[T] = Callable[[T], Awaitable[None] | None]


class EventBus:
    """Deliver exact-type events sequentially; handler failures propagate.

    This is an in-memory observation channel operating on a single event loop,
    not a distributed or durable message queue.

    Example:
        >>> bus = EventBus()
        >>> dispose = bus.subscribe(str, lambda msg: print(f"Received: {msg}"))
        >>> await bus.publish("hello")
        Received: hello
        >>> dispose()
    """

    def __init__(self) -> None:
        """Initialize an empty event bus with no registered handlers."""
        self._handlers: dict[type[object], dict[object, Handler[object]]] = {}

    def subscribe[E](
        self, event_type: type[E], handler: Handler[E]
    ) -> Callable[[], None]:
        """Register a handler for exact-type events and return a disposer.

        Args:
            event_type: The exact Python type of event to observe.
            handler: A synchronous or asynchronous callable accepting the event.

        Returns:
            An idempotent parameterless callable that removes this subscription
            when invoked.

        Example:
            >>> bus = EventBus()
            >>> unsubscribe = bus.subscribe(int, lambda n: print(n * 2))
            >>> await bus.publish(21)
            42
            >>> unsubscribe()
        """
        token = object()
        handlers = self._handlers.setdefault(event_type, {})
        handlers[token] = cast("Handler[object]", handler)

        def dispose() -> None:
            handlers.pop(token, None)
            if not handlers and self._handlers.get(event_type) is handlers:
                del self._handlers[event_type]

        return dispose

    async def publish(self, event: object) -> None:
        """Deliver an event to all subscribers of its exact runtime type.

        Delivery proceeds sequentially in registration order. If a handler
        returns an awaitable (such as a coroutine), it is awaited before
        proceeding to the next handler.

        Args:
            event: The event instance to publish. Its type (`type(event)`)
                determines which registered handlers receive it.

        Raises:
            Exception: Any exception raised by a handler propagates immediately
                to the caller, halting further delivery of this event.
        """
        for handler in tuple(self._handlers.get(type(event), {}).values()):
            result = handler(event)
            if inspect.isawaitable(result):
                await result

    def listener_count(self, event_type: type[object] | None = None) -> int:
        """Return the count of active listeners.

        Args:
            event_type: If specified, return active listeners for this exact
                event type. If `None`, return the total count across all types.

        Returns:
            The number of active subscriptions.
        """
        if event_type is not None:
            return len(self._handlers.get(event_type, {}))
        return sum(len(h) for h in self._handlers.values())

    @property
    def active_listener_count(self) -> int:
        """Return the total count of active subscriptions across all event types."""
        return sum(len(h) for h in self._handlers.values())

    @property
    def active_subscription_count(self) -> int:
        """Return the total count of active subscriptions across all event types."""
        return self.active_listener_count

    @property
    def subscribed_event_types(self) -> frozenset[type[object]]:
        """Return the set of event types with at least one active subscriber."""
        return frozenset(self._handlers.keys())

    def clear(self) -> None:
        """Unregister all event handlers across all event types."""
        self._handlers.clear()


__all__ = ("EventBus", "Handler")
