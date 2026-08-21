"""Typed event bus and contributor registry with exact ownership."""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from itertools import count
from threading import RLock
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

E = TypeVar("E")
T = TypeVar("T")
EventHandler = Callable[[Any], Any | Awaitable[Any]]


class EventMode(StrEnum):
    """Supported event dispatch semantics."""

    PUBLISH = "publish"
    SERIAL = "serial"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"


@dataclass(frozen=True, slots=True)
class SubscriptionToken:
    """Unique token identifying one exact event subscription."""

    token_id: int
    event_type: type[Any]
    mode: EventMode
    owner_id: str = ""


@dataclass(frozen=True, slots=True)
class EventSubscription:
    """One active event subscription."""

    token: SubscriptionToken
    handler: EventHandler


class EventBus:
    """Thread-safe typed event dispatcher with explicit dispatch modes."""

    def __init__(self) -> None:
        """Initialize an empty event bus."""
        self._subscriptions: dict[type[Any], list[EventSubscription]] = defaultdict(
            list
        )
        self._token_map: dict[int, SubscriptionToken] = {}
        self._token_counter = count(1)
        self._lock = RLock()

    def subscribe[EventT](
        self,
        event_type: type[EventT],
        handler: Callable[[EventT], Any | Awaitable[Any]],
        mode: EventMode = EventMode.PUBLISH,
        owner_id: str = "",
    ) -> Callable[[], None]:
        """Register one handler and return an idempotent exact disposer."""
        with self._lock:
            token = SubscriptionToken(
                token_id=next(self._token_counter),
                event_type=event_type,
                mode=mode,
                owner_id=owner_id,
            )
            subscription = EventSubscription(token=token, handler=handler)
            self._subscriptions[event_type].append(subscription)
            self._token_map[token.token_id] = token

        def disposer() -> None:
            self.unsubscribe_token(token)

        return disposer

    def unsubscribe_token(self, token: SubscriptionToken) -> bool:
        """Remove only the subscription identified by the exact token."""
        with self._lock:
            if token.token_id not in self._token_map:
                return False
            del self._token_map[token.token_id]
            subscriptions = self._subscriptions.get(token.event_type, [])
            remaining = [
                subscription
                for subscription in subscriptions
                if subscription.token != token
            ]
            if remaining:
                self._subscriptions[token.event_type] = remaining
            else:
                self._subscriptions.pop(token.event_type, None)
            return True

    def unsubscribe[EventT](
        self,
        event_type: type[EventT],
        handler: Callable[[EventT], Any | Awaitable[Any]],
    ) -> bool:
        """Remove the first matching registration for compatibility."""
        with self._lock:
            match = next(
                (
                    subscription.token
                    for subscription in self._subscriptions.get(event_type, [])
                    if subscription.handler == handler
                ),
                None,
            )
        return self.unsubscribe_token(match) if match is not None else False

    def _snapshot(
        self,
        event_type: type[Any],
        mode: EventMode,
    ) -> tuple[EventSubscription, ...]:
        with self._lock:
            return tuple(
                subscription
                for subscription in self._subscriptions.get(event_type, [])
                if subscription.token.mode == mode
            )

    async def publish(self, event: object) -> None:
        """Dispatch a fact event concurrently with error isolation."""
        subscriptions = self._snapshot(type(event), EventMode.PUBLISH)
        if not subscriptions:
            return
        tasks = [
            asyncio.create_task(self._invoke_handler(subscription.handler, event))
            for subscription in subscriptions
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for subscription, result in zip(subscriptions, results, strict=True):
            if isinstance(result, BaseException):
                logger.error(
                    "Error in event handler %s for %s: %s",
                    subscription.handler,
                    type(event).__name__,
                    result,
                    exc_info=result,
                )

    async def dispatch_serial(self, event: object) -> None:
        """Dispatch serial handlers in registration order."""
        for subscription in self._snapshot(type(event), EventMode.SERIAL):
            await self._invoke_handler(subscription.handler, event)

    async def dispatch_parallel(self, event: object) -> None:
        """Dispatch parallel handlers and propagate failures."""
        subscriptions = self._snapshot(type(event), EventMode.PARALLEL)
        if not subscriptions:
            return
        await asyncio.gather(
            *(
                self._invoke_handler(subscription.handler, event)
                for subscription in subscriptions
            )
        )

    async def dispatch_pipeline[EventT](self, initial_event: EventT) -> EventT | None:
        """Transform an event through ordered pipeline handlers."""
        current: Any = initial_event
        for subscription in self._snapshot(type(initial_event), EventMode.PIPELINE):
            current = await self._invoke_handler(subscription.handler, current)
            if current is None:
                return None
        return current  # type: ignore[no-any-return]

    async def _invoke_handler(self, handler: EventHandler, event: object) -> object:
        result = handler(event)
        if inspect.isawaitable(result):
            return await result
        return result

    def listener_count(
        self,
        event_type: type[Any] | None = None,
        mode: EventMode | None = None,
    ) -> int:
        """Return the number of subscriptions matching optional filters."""
        with self._lock:
            if event_type is not None:
                subscriptions = tuple(self._subscriptions.get(event_type, []))
            else:
                subscriptions = tuple(
                    subscription
                    for values in self._subscriptions.values()
                    for subscription in values
                )
        if mode is None:
            return len(subscriptions)
        return sum(subscription.token.mode == mode for subscription in subscriptions)

    def clear(self) -> None:
        """Remove all active subscriptions."""
        with self._lock:
            self._subscriptions.clear()
            self._token_map.clear()
            self._token_counter = count(1)


class ContributorRegistry[ItemT]:
    """Registry for pluggable contributors such as adapters or indicators."""

    def __init__(self, name: str = "contributor") -> None:
        """Initialize an empty contributor registry."""
        self._name = name
        self._items: dict[str, ItemT] = {}
        self._lock = RLock()

    def register(self, key: str, item: ItemT) -> Callable[[], None]:
        """Register an item and return an idempotent disposer."""
        with self._lock:
            if key in self._items:
                msg = f"Contributor '{key}' already registered in {self._name} registry"
                raise ValueError(msg)
            self._items[key] = item

        def disposer() -> None:
            with self._lock:
                self._items.pop(key, None)

        return disposer

    def get(self, key: str) -> ItemT | None:
        """Return an item when present."""
        with self._lock:
            return self._items.get(key)

    def require(self, key: str) -> ItemT:
        """Return an item or raise KeyError."""
        item = self.get(key)
        if item is None:
            msg = f"Contributor '{key}' not found in {self._name} registry"
            raise KeyError(msg)
        return item

    def list_keys(self) -> tuple[str, ...]:
        """Return registered contributor keys."""
        with self._lock:
            return tuple(self._items)

    def items(self) -> dict[str, ItemT]:
        """Return a shallow copy of registered contributors."""
        with self._lock:
            return dict(self._items)

    def clear(self) -> None:
        """Remove all contributors."""
        with self._lock:
            self._items.clear()
