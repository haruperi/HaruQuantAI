# cspell:words awaitables awaitable unregisters
"""Feature-scoped capabilities, tasks, subscriptions, and resource cleanup.

In this architecture, every Feature receives an isolated, feature-specific
`FeatureContext` instance when its asynchronous `start(context)` method is
invoked.

The context provides four core responsibilities:
1. Dependency Resolution (`require`, `optional`, `has`):
   - Strict declaration enforcement: features can only request capabilities
     declared in their `FeatureSpec.requires` or `FeatureSpec.optional`.
   - Any attempt to resolve undeclared capabilities raises `ValueError`.
   - Missing required capabilities fail fast with `CapabilityUnavailableError`.
   - Optional capabilities safely return `None` or a caller-supplied default.
2. Export Staging & Transactional Publication (`provide`, `commit_exports`):
   - Features stage instances for each capability declared in `FeatureSpec.provides`.
   - `commit_exports()` validates that the exact declared set is staged before
     the runtime exposes them to dependent features.
3. Managed Effect Lifecycles (`enter`, `enter_context`, `spawn`, `on_close`):
   - Context managers, background tasks, and cleanup hooks registered on the
     context are automatically torn down in strict reverse acquisition (LIFO)
     order during shutdown.
   - Background tasks created via `spawn()` are cancelled and awaited.
   - Failures during cleanup are caught and grouped into `BaseExceptionGroup`,
     guaranteeing that every registered cleanup callback runs.
4. Scoped Event Observation (`subscribe`, `publish`):
   - Handlers subscribed via `context.subscribe()` are automatically unregistered
     when the feature shuts down, preventing memory leaks and stale callbacks.
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable, Coroutine, Mapping
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    AsyncExitStack,
)
from typing import Any, cast

from app.kernel.capability import Capability, CapabilityUnavailableError
from app.kernel.events import EventBus, Handler
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

logger = get_logger(__name__)


class FeatureContext:
    """Enforce declarations and manage lifecycles for one feature activation.

    Instances are runtime-created and confined to one asyncio event loop.
    All operations are guarded against use after the context has been closed.
    """

    def __init__(
        self,
        spec: FeatureSpec,
        providers: Mapping[Capability[Any], object],
        events: EventBus,
    ) -> None:
        """Initialize a feature execution context.

        Args:
            spec: The immutable specification of the feature owning this context.
            providers: Mapping of available capability keys to service instances.
            events: In-process event bus for inter-feature pub/sub.
        """
        self._spec = spec
        self._providers = providers
        self._events = events
        self._staged: dict[Capability[Any], object] = {}
        self._stack = AsyncExitStack()
        self._closed = False
        self._published = False
        self._cleanup_errors: list[BaseException] = []

    def _ensure_open(self) -> None:
        """Reject effects and lookups after this activation has closed.

        Raises:
            RuntimeError: If the feature context has already been closed.
        """
        if self._closed:
            raise RuntimeError(f"Feature scope for '{self._spec.name}' is closed")

    @property
    def spec(self) -> FeatureSpec:
        """Return the manifest specification of the feature owning this context."""
        return self._spec

    @property
    def is_open(self) -> bool:
        """Return True if this context is active and not yet closed."""
        return not self._closed

    @property
    def staged_capabilities(self) -> frozenset[Capability[Any]]:
        """Return the set of capabilities staged for export so far."""
        return frozenset(self._staged.keys())

    @property
    def available_capabilities(self) -> frozenset[Capability[Any]]:
        """Return the set of all capabilities currently available to this feature."""
        return frozenset(self._providers.keys())

    def has(self, key: Capability[Any]) -> bool:
        """Return True if a capability is available in the provider registry.

        Args:
            key: The capability key to check.

        Returns:
            True if the capability is available; False otherwise.
        """
        return key in self._providers

    def require[T](self, key: Capability[T]) -> T:
        """Resolve a declared dependency or raise an attributed failure.

        Args:
            key: The declared required capability token.

        Returns:
            The resolved service instance.

        Raises:
            RuntimeError: If the context is closed.
            ValueError: If the capability was not declared in `requires`.
            CapabilityUnavailableError: If declared but missing from providers.
        """
        self._ensure_open()
        if key not in self._spec.requires:
            raise ValueError(f"Undeclared dependency: {self._spec.name}: {key.name}")
        if key not in self._providers:
            raise CapabilityUnavailableError(f"{self._spec.name}: {key.name}")
        return cast("T", self._providers[key])

    def optional[T](self, key: Capability[T], default: T | None = None) -> T | None:
        """Resolve an optional dependency or return default if absent.

        Args:
            key: The declared optional capability token.
            default: Value returned if the capability is unavailable (default: None).

        Returns:
            The resolved service instance if present; otherwise `default`.

        Raises:
            RuntimeError: If the context is closed.
            ValueError: If the capability was not declared in `optional`.
        """
        self._ensure_open()
        if key not in self._spec.optional:
            raise ValueError(
                f"Undeclared optional dependency: {self._spec.name}: {key.name}"
            )
        if key not in self._providers:
            return default
        return cast("T", self._providers[key])

    def provide[T](self, key: Capability[T], service: T) -> None:
        """Stage a declared export; duplicate and late exports are rejected.

        Args:
            key: The capability token declared in `provides`.
            service: The service instance fulfilling this capability.

        Raises:
            RuntimeError: If the context is closed.
            ValueError: If the export is undeclared, duplicate, or already published.
        """
        self._ensure_open()
        if self._published or key not in self._spec.provides or key in self._staged:
            raise ValueError("Export is undeclared, duplicate, or already published")
        self._staged[key] = service

    def commit_exports(self) -> dict[Capability[Any], object]:
        """Freeze the exact declared bundle for runtime publication.

        Returns:
            A dictionary mapping each declared capability to its provider.

        Raises:
            RuntimeError: If the context is closed.
            ValueError: If the feature did not stage its exact declared bundle.
        """
        self._ensure_open()
        if self._published or self._staged.keys() != self._spec.provides:
            raise ValueError("Feature did not stage its exact export bundle")
        self._published = True
        return dict(self._staged)

    def on_close(self, callback: Callable[[], Any]) -> None:
        """Register synchronous or asynchronous cleanup in reverse acquisition order.

        Args:
            callback: A callable (sync or async) executed during feature shutdown.

        Raises:
            RuntimeError: If the context is closed.
        """
        self._ensure_open()

        async def guarded() -> None:
            try:
                result = callback()
                if inspect.isawaitable(result):
                    await result
            except BaseException as error:
                logger.error(
                    "feature_cleanup_callback_error",
                    feature=self._spec.name,
                    error=str(error),
                )
                self._cleanup_errors.append(error)

        self._stack.push_async_callback(guarded)

    def enter_context[T](self, resource: AbstractContextManager[T]) -> T:
        """Enter a synchronous context manager and register its exit.

        Args:
            resource: A synchronous context manager to manage.

        Returns:
            The resource yielded by `__enter__()`.

        Raises:
            RuntimeError: If the context is closed.
        """
        self._ensure_open()
        value = resource.__enter__()

        async def release() -> None:
            try:
                resource.__exit__(None, None, None)
            except BaseException as error:
                logger.error(
                    "feature_sync_context_exit_error",
                    feature=self._spec.name,
                    error=str(error),
                )
                self._cleanup_errors.append(error)

        self._stack.push_async_callback(release)
        return value

    async def enter[T](self, resource: AbstractAsyncContextManager[T]) -> T:
        """Enter an asynchronous context manager and register its exit.

        Args:
            resource: An asynchronous context manager to manage.

        Returns:
            The resource yielded by `__aenter__()`.

        Raises:
            RuntimeError: If the context is closed.
        """
        self._ensure_open()
        value = await resource.__aenter__()

        async def release() -> None:
            try:
                await resource.__aexit__(None, None, None)
            except BaseException as error:
                logger.error(
                    "feature_async_context_exit_error",
                    feature=self._spec.name,
                    error=str(error),
                )
                self._cleanup_errors.append(error)

        self._stack.push_async_callback(release)
        return value

    enter_async_context = enter

    def spawn[T](
        self, coroutine: Coroutine[Any, Any, T], *, name: str | None = None
    ) -> asyncio.Task[T]:
        """Spawn a managed task, cancel/await it at shutdown, and surface errors.

        Args:
            coroutine: The coroutine to execute concurrently in the background.
            name: Optional diagnostic name for the task.

        Returns:
            The created `asyncio.Task` instance.

        Raises:
            RuntimeError: If the context is closed.
        """
        if self._closed:
            coroutine.close()
            raise RuntimeError(f"Feature scope for '{self._spec.name}' is closed")
        task = asyncio.create_task(coroutine, name=name)
        logger.debug(
            "feature_task_spawned",
            feature=self._spec.name,
            task_name=name or "",
        )

        async def stop() -> None:
            if not task.done():
                task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except BaseException as error:
                logger.error(
                    "feature_task_error",
                    feature=self._spec.name,
                    task_name=name or "",
                    error=str(error),
                )
                self._cleanup_errors.append(error)

        self._stack.push_async_callback(stop)
        return task

    def subscribe[E](self, event_type: type[E], handler: Handler[E]) -> None:
        """Subscribe to an event type with automatic lifecycle unsubscription.

        Args:
            event_type: The exact Python type of event to observe.
            handler: A synchronous or asynchronous callable receiving the event.

        Raises:
            RuntimeError: If the context is closed.
        """
        self._ensure_open()
        self.on_close(self._events.subscribe(event_type, handler))

    async def publish(self, event: object) -> None:
        """Publish an observation to the event bus.

        Args:
            event: The event instance to publish.

        Raises:
            RuntimeError: If the context is closed.
        """
        self._ensure_open()
        await self._events.publish(event)

    async def close(self) -> None:
        """Close this feature context and unwind all managed resources in LIFO order.

        Raises:
            BaseExceptionGroup: If one or more cleanup callbacks raised exceptions.
        """
        if not self._closed:
            self._closed = True
            logger.debug("feature_context_closing", feature=self._spec.name)
            await self._stack.aclose()
            if self._cleanup_errors:
                errors, self._cleanup_errors = self._cleanup_errors, []
                raise BaseExceptionGroup("Feature cleanup failed", errors)


__all__ = ("FeatureContext",)
