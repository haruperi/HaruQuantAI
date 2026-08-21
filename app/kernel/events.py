"""Typed event bus and contributor registry with reversible scopes."""

import asyncio
import inspect
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from itertools import count
from typing import Any

logger = logging.getLogger(__name__)

EventHandler = Callable[[Any], Any | Awaitable[Any]]


class EventMode(StrEnum):
    """Event dispatch and execution mode."""

    PUBLISH = "publish"
    SERIAL = "serial"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"


@dataclass(frozen=True, slots=True)
class EventSubscription:
    """Represent one exact event subscription registration."""

    token: int
    event_type: type[Any]
    handler: EventHandler
    mode: EventMode


class EventBus:
    """Type-safe asynchronous event dispatcher supporting explicit dispatch modes."""

    def __init__(self) -> None:
        self._subscriptions: dict[type[Any], list[EventSubscription]] = defaultdict(list)
        self._token_counter = count(1)

    def subscribe[EventT](
        self,
        event_type: type[EventT],
        handler: Callable[[EventT], Any | Awaitable[Any]],
        mode: EventMode = EventMode.PUBLISH,
    ) -> Callable[[], None]:
        """Subscribe a handler and return an exact-registration disposer."""
        subscription = EventSubscription(
            token=next(self._token_counter),
            event_type=event_type,
            handler=handler,
            mode=mode,
        )
        self._subscriptions[event_type].append(subscription)

        def disposer() -> None:
            self.unsubscribe_token(subscription.token)

        return disposer

    def unsubscribe_token(self, token: int) -> bool:
        """Remove exactly one subscription by token."""
        for event_type, subscriptions in tuple(self._subscriptions.items()):
            remaining = [sub for sub in subscriptions if sub.token != token]
            if len(remaining) == len(subscriptions):
                continue
            if remaining:
                self._subscriptions[event_type] = remaining
            else:
                del self._subscriptions[event_type]
            return True
        return False

    def unsubscribe[EventT](
        self,
        event_type: type[EventT],
        handler: Callable[[EventT], Any | Awaitable[Any]],
    ) -> bool:
        """Remove the first matching handler registration for compatibility."""
        subscriptions = self._subscriptions.get(event_type, [])
        for sub in subscriptions:
            if sub.handler == handler:
                return self.unsubscribe_token(sub.token)
        return False

    def _subscriptions_for(
        self,
        event_type: type[Any],
        mode: EventMode,
    ) -> list[EventSubscription]:
        return [
            sub for sub in self._subscriptions.get(event_type, []) if sub.mode == mode
        ]

    async def publish(self, event: object) -> None:
        """Dispatch only PUBLISH handlers concurrently with error isolation."""
        subscriptions = self._subscriptions_for(type(event), EventMode.PUBLISH)
        if not subscriptions:
            return
        tasks = [asyncio.create_task(self._invoke_handler(sub.handler, event)) for sub in subscriptions]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for sub, result in zip(subscriptions, results, strict=True):
            if isinstance(result, BaseException):
                logger.error(
                    "Error in event handler %s for %s: %s",
                    sub.handler,
                    type(event).__name__,
                    result,
                    exc_info=result,
                )

    async def dispatch_serial(self, event: object) -> None:
        """Dispatch only SERIAL handlers sequentially."""
        for sub in self._subscriptions_for(type(event), EventMode.SERIAL):
            await self._invoke_handler(sub.handler, event)

    async def dispatch_parallel(self, event: object) -> None:
        """Dispatch only PARALLEL handlers concurrently and propagate failures."""
        subscriptions = self._subscriptions_for(type(event), EventMode.PARALLEL)
        if subscriptions:
            await asyncio.gather(
                *(self._invoke_handler(sub.handler, event) for sub in subscriptions)
            )

    async def dispatch_pipeline[EventT](self, initial_event: EventT) -> EventT | None:
        """Dispatch only PIPELINE handlers as a transformation chain."""
        current: Any = initial_event
        for sub in self._subscriptions_for(type(initial_event), EventMode.PIPELINE):
            result = await self._invoke_handler(sub.handler, current)
            if result is None:
                return None
            current = result
        return current  # type: ignore[no-any-return]

    async def _invoke_handler(self, handler: EventHandler, event: object) -> object:
        result = handler(event)
        if inspect.isawaitable(result):
            return await result
        return result

    def listener_count(self, event_type: type[Any] | None = None) -> int:
        """Return total or type-specific active listener count."""
        if event_type is not None:
            return len(self._subscriptions.get(event_type, []))
        return sum(len(subscriptions) for subscriptions in self._subscriptions.values())

    def clear(self) -> None:
        """Remove all subscriptions."""
        self._subscriptions.clear()


class ContributorRegistry[ItemT]:
    """Generic registry for pluggable components."""

    def __init__(self, name: str = "contributor") -> None:
        self._name = name
        self._items: dict[str, ItemT] = {}
        self._generations: dict[str, int] = {}

    def register(self, key: str, item: ItemT) -> Callable[[], None]:
        """Register one contributor and return generation-safe disposer."""
        if key in self._items:
            msg = f"Contributor '{key}' already registered in {self._name} registry"
            raise ValueError(msg)
        generation = self._generations.get(key, 0) + 1
        self._generations[key] = generation
        self._items[key] = item

        def disposer() -> None:
            if self._generations.get(key) == generation:
                self._items.pop(key, None)

        return disposer

    def get(self, key: str) -> ItemT | None:
        return self._items.get(key)

    def require(self, key: str) -> ItemT:
        if key not in self._items:
            msg = f"Contributor '{key}' not found in {self._name} registry"
            raise KeyError(msg)
        return self._items[key]

    def list_keys(self) -> tuple[str, ...]:
        return tuple(self._items.keys())

    def items(self) -> dict[str, ItemT]:
        return dict(self._items)

    def clear(self) -> None:
        self._items.clear()
        self._generations.clear()
