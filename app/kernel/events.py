"""Typed event bus and contributor registry with reversible scopes."""

import asyncio
import inspect
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

E = TypeVar("E")
T = TypeVar("T")

EventHandler = Callable[[Any], Any | Awaitable[Any]]
PipelineHandler = Callable[[Any], Any | Awaitable[Any | None] | None]


class EventMode(StrEnum):
    """Event dispatch and execution mode."""

    PUBLISH = "publish"
    SERIAL = "serial"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"


@dataclass(frozen=True, slots=True)
class EventSubscription:
    """Represents an active event subscription."""

    event_type: type[Any]
    handler: EventHandler
    mode: EventMode = EventMode.PUBLISH


class EventBus:
    """Type-safe asynchronous event dispatcher supporting multiple dispatch modes."""

    def __init__(self) -> None:
        """Initialize empty event bus."""
        self._subscriptions: dict[type[Any], list[EventSubscription]] = defaultdict(
            list
        )
        self._lock = asyncio.Lock()

    def subscribe[EventT](
        self,
        event_type: type[EventT],
        handler: Callable[[EventT], Any | Awaitable[Any]],
        mode: EventMode = EventMode.PUBLISH,
    ) -> Callable[[], None]:
        """Subscribe a handler to an event type.

        Args:
            event_type: Class or type of the event to listen for.
            handler: Callable or coroutine receiving the event instance.
            mode: Dispatch mode for this subscription.

        Returns:
            Disposer callable that unregisters the subscription when called.
        """
        sub = EventSubscription(
            event_type=event_type,
            handler=handler,
            mode=mode,
        )
        self._subscriptions[event_type].append(sub)

        def disposer() -> None:
            self.unsubscribe(event_type, handler)

        return disposer

    def unsubscribe[EventT](
        self,
        event_type: type[EventT],
        handler: Callable[[EventT], Any | Awaitable[Any]],
    ) -> bool:
        """Unsubscribe a previously registered handler.

        Args:
            event_type: Target event type.
            handler: Handler callable to remove.

        Returns:
            True if a subscription was removed, False otherwise.
        """
        if event_type not in self._subscriptions:
            return False

        original_len = len(self._subscriptions[event_type])
        self._subscriptions[event_type] = [
            s for s in self._subscriptions[event_type] if s.handler != handler
        ]
        if not self._subscriptions[event_type]:
            del self._subscriptions[event_type]

        return len(self._subscriptions.get(event_type, [])) < original_len

    async def publish(self, event: object) -> None:
        """Dispatch event in observational PUBLISH mode (concurrent, error-isolated).

        Args:
            event: Event instance to publish.
        """
        event_type = type(event)
        subscriptions = list(self._subscriptions.get(event_type, []))
        if not subscriptions:
            return

        tasks: list[asyncio.Task[Any]] = []
        for sub in subscriptions:
            coro = self._invoke_handler(sub.handler, event)
            task = asyncio.create_task(coro)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for idx, res in enumerate(results):
            if isinstance(res, BaseException):
                logger.error(
                    "Error in event handler %s for %s: %s",
                    subscriptions[idx].handler,
                    event_type.__name__,
                    res,
                    exc_info=res,
                )

    async def dispatch_serial(self, event: object) -> None:
        """Dispatch event sequentially to all registered handlers in order.

        Args:
            event: Event instance to dispatch.
        """
        event_type = type(event)
        subscriptions = list(self._subscriptions.get(event_type, []))
        for sub in subscriptions:
            await self._invoke_handler(sub.handler, event)

    async def dispatch_parallel(self, event: object) -> None:
        """Dispatch event concurrently, raising exceptions if any handler fails.

        Args:
            event: Event instance to dispatch.
        """
        event_type = type(event)
        subscriptions = list(self._subscriptions.get(event_type, []))
        if not subscriptions:
            return

        coros = [self._invoke_handler(sub.handler, event) for sub in subscriptions]
        await asyncio.gather(*coros)

    async def dispatch_pipeline[EventT](self, initial_event: EventT) -> EventT | None:
        """Dispatch through a waterfall transformation pipeline.

        Each handler receives the output of the previous handler. If any handler
        returns None, the pipeline is short-circuited and returns None.

        Args:
            initial_event: Starting event payload.

        Returns:
            Final transformed event, or None if short-circuited.
        """
        event_type = type(initial_event)
        subscriptions = list(self._subscriptions.get(event_type, []))
        current: Any = initial_event

        for sub in subscriptions:
            res = await self._invoke_handler(sub.handler, current)
            if res is None:
                return None
            current = res

        return current  # type: ignore[no-any-return]

    async def _invoke_handler(self, handler: EventHandler, event: object) -> object:
        """Invoke a handler synchronously or asynchronously.

        Args:
            handler: Callable or coroutine handler.
            event: Event object to pass.

        Returns:
            Result returned by the handler.
        """
        res = handler(event)
        if inspect.isawaitable(res):
            return await res
        return res

    def listener_count(self, event_type: type[Any] | None = None) -> int:
        """Return total or type-specific active listener count.

        Args:
            event_type: Optional event type filter.

        Returns:
            Number of registered subscriptions.
        """
        if event_type is not None:
            return len(self._subscriptions.get(event_type, []))
        return sum(len(subs) for subs in self._subscriptions.values())

    def clear(self) -> None:
        """Remove all subscriptions."""
        self._subscriptions.clear()


class ContributorRegistry[ItemT]:
    """Generic registry for pluggable components (e.g. broker adapters, indicators)."""

    def __init__(self, name: str = "contributor") -> None:
        """Initialize registry.

        Args:
            name: Diagnostic category name.
        """
        self._name = name
        self._items: dict[str, ItemT] = {}

    def register(self, key: str, item: ItemT) -> Callable[[], None]:
        """Register a contributor item and return a disposable unregister function.

        Args:
            key: Contributor identifier key.
            item: Implementation instance.

        Returns:
            Disposer callable removing the item upon execution.

        Raises:
            ValueError: If key is already registered.
        """
        if key in self._items:
            msg = f"Contributor '{key}' already registered in {self._name} registry"
            raise ValueError(msg)

        self._items[key] = item

        def disposer() -> None:
            self._items.pop(key, None)

        return disposer

    def get(self, key: str) -> ItemT | None:
        """Get contributor item if present.

        Args:
            key: Contributor identifier.

        Returns:
            Contributor item or None.
        """
        return self._items.get(key)

    def require(self, key: str) -> ItemT:
        """Get contributor item or raise KeyError if missing.

        Args:
            key: Contributor identifier.

        Returns:
            Contributor item.

        Raises:
            KeyError: If item is not registered.
        """
        if key not in self._items:
            msg = f"Contributor '{key}' not found in {self._name} registry"
            raise KeyError(msg)
        return self._items[key]

    def list_keys(self) -> tuple[str, ...]:
        """Return all registered keys."""
        return tuple(self._items.keys())

    def items(self) -> dict[str, ItemT]:
        """Return shallow copy of all registered items."""
        return dict(self._items)

    def clear(self) -> None:
        """Clear all registered items."""
        self._items.clear()
