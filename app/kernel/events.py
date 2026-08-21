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
class SubscriptionToken:
    """Unique ownership token for an exact event subscription.

    Attributes:
        token_id: Unique integer identifying this exact subscription.
        event_type: Target event type.
        mode: Dispatch mode for this subscription.
        owner_id: Feature ID that owns this subscription.
    """

    token_id: int
    event_type: type[Any]
    mode: EventMode
    owner_id: str = ""


@dataclass(frozen=True, slots=True)
class EventSubscription:
    """Represents an active event subscription binding a token to a handler."""

    token: SubscriptionToken
    handler: EventHandler


class EventBus:
    """Type-safe asynchronous event dispatcher supporting multiple dispatch modes."""

    def __init__(self) -> None:
        """Initialize empty event bus."""
        self._subscriptions: dict[type[Any], list[EventSubscription]] = defaultdict(
            list
        )
        self._token_map: dict[int, SubscriptionToken] = {}
        self._counter: int = 0
        self._lock = asyncio.Lock()

    def subscribe[EventT](
        self,
        event_type: type[EventT],
        handler: Callable[[EventT], Any | Awaitable[Any]],
        mode: EventMode = EventMode.PUBLISH,
        owner_id: str = "",
    ) -> Callable[[], None]:
        """Subscribe a handler to an event type.

        Args:
            event_type: Class or type of the event to listen for.
            handler: Callable or coroutine receiving the event instance.
            mode: Dispatch mode for this subscription.
            owner_id: Optional feature identifier registering this handler.

        Returns:
            Idempotent disposer callable that unregisters the exact subscription.
        """
        self._counter += 1
        token = SubscriptionToken(
            token_id=self._counter,
            event_type=event_type,
            mode=mode,
            owner_id=owner_id,
        )
        sub = EventSubscription(token=token, handler=handler)
        self._subscriptions[event_type].append(sub)
        self._token_map[token.token_id] = token

        def disposer() -> None:
            self.unsubscribe_token(token)

        return disposer

    def unsubscribe_token(self, token: SubscriptionToken) -> bool:
        """Unsubscribe an exact subscription using its unique token.

        Args:
            token: SubscriptionToken returned at registration.

        Returns:
            True if matching subscription was removed, False if token is stale.
        """
        if token.token_id not in self._token_map:
            return False

        del self._token_map[token.token_id]
        event_type = token.event_type
        if event_type in self._subscriptions:
            self._subscriptions[event_type] = [
                s for s in self._subscriptions[event_type] if s.token != token
            ]
            if not self._subscriptions[event_type]:
                del self._subscriptions[event_type]

        return True

    def unsubscribe[EventT](
        self,
        event_type: type[EventT],
        handler: Callable[[EventT], Any | Awaitable[Any]],
    ) -> bool:
        """Unsubscribe the first matching registered handler for an event type.

        Args:
            event_type: Target event type.
            handler: Handler callable to remove.

        Returns:
            True if a subscription was removed, False otherwise.
        """
        if event_type not in self._subscriptions:
            return False

        matching = [s for s in self._subscriptions[event_type] if s.handler == handler]
        if not matching:
            return False

        return self.unsubscribe_token(matching[0].token)

    async def publish(self, event: object) -> None:
        """Dispatch event in observational PUBLISH mode (concurrent, error-isolated).

        Only handlers registered with EventMode.PUBLISH are invoked.

        Args:
            event: Event instance to publish.
        """
        event_type = type(event)
        subscriptions = [
            s
            for s in list(self._subscriptions.get(event_type, []))
            if s.token.mode == EventMode.PUBLISH
        ]
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
        """Dispatch event sequentially to handlers in registration order.

        Only handlers registered with EventMode.SERIAL are invoked.

        Args:
            event: Event instance to dispatch.
        """
        event_type = type(event)
        subscriptions = [
            s
            for s in list(self._subscriptions.get(event_type, []))
            if s.token.mode == EventMode.SERIAL
        ]
        for sub in subscriptions:
            await self._invoke_handler(sub.handler, event)

    async def dispatch_parallel(self, event: object) -> None:
        """Dispatch event concurrently, raising exceptions if any handler fails.

        Only handlers registered with EventMode.PARALLEL are invoked.

        Args:
            event: Event instance to dispatch.
        """
        event_type = type(event)
        subscriptions = [
            s
            for s in list(self._subscriptions.get(event_type, []))
            if s.token.mode == EventMode.PARALLEL
        ]
        if not subscriptions:
            return

        coros = [self._invoke_handler(sub.handler, event) for sub in subscriptions]
        await asyncio.gather(*coros)

    async def dispatch_pipeline[EventT](self, initial_event: EventT) -> EventT | None:
        """Dispatch through a waterfall transformation pipeline.

        Only handlers registered with EventMode.PIPELINE are invoked.
        Each handler receives the output of the previous handler. If any handler
        returns None, the pipeline is short-circuited and returns None.

        Args:
            initial_event: Starting event payload.

        Returns:
            Final transformed event, or None if short-circuited.
        """
        event_type = type(initial_event)
        subscriptions = [
            s
            for s in list(self._subscriptions.get(event_type, []))
            if s.token.mode == EventMode.PIPELINE
        ]
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

    def listener_count(
        self,
        event_type: type[Any] | None = None,
        mode: EventMode | None = None,
    ) -> int:
        """Return total or type-specific active listener count.

        Args:
            event_type: Optional event type filter.
            mode: Optional event mode filter.

        Returns:
            Number of registered subscriptions matching criteria.
        """
        if event_type is not None:
            subs = self._subscriptions.get(event_type, [])
            if mode is not None:
                return sum(1 for s in subs if s.token.mode == mode)
            return len(subs)

        all_subs = [s for subs in self._subscriptions.values() for s in subs]
        if mode is not None:
            return sum(1 for s in all_subs if s.token.mode == mode)
        return len(all_subs)

    def clear(self) -> None:
        """Remove all subscriptions and reset counter."""
        self._subscriptions.clear()
        self._token_map.clear()
        self._counter = 0


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
