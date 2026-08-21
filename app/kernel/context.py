"""Feature context interface and implementation for scoped capability operations."""

import asyncio
import inspect
from collections.abc import Awaitable, Callable, Coroutine
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import TYPE_CHECKING, Any, Protocol

from app.kernel.capability import CapabilityKey, CapabilityUnavailableError
from app.kernel.events import EventBus, EventMode
from app.kernel.scope import EffectType

if TYPE_CHECKING:
    from app.kernel.feature import FeatureSpec
    from app.kernel.scope import FeatureScope


class FeatureContext(Protocol):
    """Protocol for scoped runtime operations available to mounting features."""

    def require[CapT](self, capability: CapabilityKey[CapT]) -> CapT:
        """Resolve a mandatory capability from the service registry.

        Args:
            capability: Target capability key.

        Returns:
            Active capability provider.

        Raises:
            CapabilityUnavailableError: If no provider is available.
        """
        ...

    def optional[CapT](self, capability: CapabilityKey[CapT]) -> CapT | None:
        """Resolve an optional capability if an active provider is present.

        Args:
            capability: Target capability key.

        Returns:
            Active capability provider if available, None otherwise.
        """
        ...

    def provide[CapT](
        self,
        capability: CapabilityKey[CapT],
        implementation: CapT,
    ) -> None:
        """Register a capability provider owned by this feature's scope.

        Args:
            capability: Target capability key.
            implementation: Conforming capability provider instance.
        """
        ...

    def spawn(
        self,
        coroutine: Coroutine[Any, Any, Any],
        *,
        name: str,
    ) -> asyncio.Task[Any]:
        """Spawn a background task owned and cancelled upon feature unmount.

        Args:
            coroutine: Async coroutine to run.
            name: Diagnostic name for the task.

        Returns:
            Tracked asyncio Task instance.
        """
        ...

    def register_callback(
        self,
        callback: Callable[[], None] | Callable[[], Awaitable[None]],
    ) -> None:
        """Register a synchronous or asynchronous teardown disposer.

        Args:
            callback: Cleanup callback executed upon unmount.
        """
        ...

    def enter_context[ContextT](
        self,
        cm: AbstractContextManager[ContextT],
        *,
        name: str = "",
    ) -> ContextT:
        """Enter a synchronous context manager and track its cleanup in this scope.

        Args:
            cm: Context manager to enter.
            name: Optional descriptive resource name.

        Returns:
            Resource yielded by context manager.
        """
        ...

    async def enter_async_context[ContextT](
        self,
        cm: AbstractAsyncContextManager[ContextT],
        *,
        name: str = "",
    ) -> ContextT:
        """Enter an asynchronous context manager and track its cleanup in this scope.

        Args:
            cm: Async context manager to enter.
            name: Optional descriptive resource name.

        Returns:
            Resource yielded by context manager.
        """
        ...

    def subscribe[EventT](
        self,
        event_type: type[EventT],
        handler: Callable[[EventT], Any | Awaitable[Any]],
        mode: EventMode = EventMode.PUBLISH,
    ) -> None:
        """Subscribe to typed events with automatic scope disposal upon unmount.

        Args:
            event_type: Class or type of the event.
            handler: Callable or coroutine handling the event.
            mode: Dispatch mode (e.g. PUBLISH, SERIAL, PARALLEL, PIPELINE).
        """
        ...

    async def publish(self, event: object) -> None:
        """Publish a fact event to the kernel event bus.

        Args:
            event: Event object to broadcast.
        """
        ...

    async def dispatch_pipeline[EventT](self, initial_event: EventT) -> EventT | None:
        """Dispatch an event through an interceptor/policy pipeline.

        Args:
            initial_event: Initial event payload.

        Returns:
            Transformed event, or None if short-circuited.
        """
        ...


class DefaultFeatureContext:
    """Concrete FeatureContext implementation wired to a FeatureScope."""

    def __init__(
        self,
        spec: FeatureSpec,
        scope: FeatureScope,
        resolver: Callable[[CapabilityKey[Any]], Any | None] | None = None,
        provider_registrar: (
            Callable[[CapabilityKey[Any], Any, FeatureScope], None] | None
        ) = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the feature context.

        Args:
            spec: Declared specification for the feature.
            scope: Private temporal scope owning reversible effects.
            resolver: Callable to resolve active capability implementations.
            provider_registrar: Callable to register new capability providers.
            event_bus: Shared application event bus.
        """
        self._spec = spec
        self._scope = scope
        self._resolver = resolver or (lambda _cap: None)
        self._provider_registrar = provider_registrar or (
            lambda _cap, _impl, _scope: None
        )
        self._event_bus = event_bus or EventBus()

    @property
    def scope(self) -> FeatureScope:
        """Return the underlying scope.

        Returns:
            Underlying FeatureScope.
        """
        return self._scope

    @property
    def event_bus(self) -> EventBus:
        """Return the event bus.

        Returns:
            Active EventBus instance.
        """
        return self._event_bus

    def require[CapT](self, capability: CapabilityKey[CapT]) -> CapT:
        """Resolve a required capability, validating against spec.requires.

        Args:
            capability: Capability key to resolve.

        Returns:
            Resolved capability provider instance.

        Raises:
            ValueError: If capability is not declared in requires or optional.
            CapabilityUnavailableError: If capability is not currently active.
        """
        if (
            capability not in self._spec.requires
            and capability not in self._spec.optional
        ):
            msg = (
                f"Feature '{self._spec.feature_id}' attempted to require undeclared "
                f"capability '{capability.identifier}'"
            )
            raise ValueError(msg)
        provider = self._resolver(capability)
        if provider is None:
            raise CapabilityUnavailableError(capability.identifier)
        return provider  # type: ignore[no-any-return]

    def optional[CapT](self, capability: CapabilityKey[CapT]) -> CapT | None:
        """Resolve an optional capability, validating against spec.optional.

        Args:
            capability: Capability key to resolve.

        Returns:
            Resolved capability provider instance if active, None otherwise.

        Raises:
            ValueError: If capability is not declared in optional or requires.
        """
        if (
            capability not in self._spec.optional
            and capability not in self._spec.requires
        ):
            msg = (
                f"Feature '{self._spec.feature_id}' attempted to access undeclared "
                f"optional capability '{capability.identifier}'"
            )
            raise ValueError(msg)
        provider: CapT | None = self._resolver(capability)
        return provider

    def provide[CapT](
        self,
        capability: CapabilityKey[CapT],
        implementation: CapT,
    ) -> None:
        """Register a capability provider, validating against spec.provides.

        Args:
            capability: Capability key being provided.
            implementation: Implementation conforming to capability protocol.

        Raises:
            ValueError: If capability is not declared in provides.
        """
        if capability not in self._spec.provides:
            msg = (
                f"Feature '{self._spec.feature_id}' attempted to provide undeclared "
                f"capability '{capability.identifier}'"
            )
            raise ValueError(msg)
        self._provider_registrar(capability, implementation, self._scope)

    def spawn(
        self,
        coroutine: Coroutine[Any, Any, Any],
        *,
        name: str,
    ) -> asyncio.Task[Any]:
        """Spawn a managed background task in the feature scope.

        Args:
            coroutine: Async coroutine to run.
            name: Task name.

        Returns:
            Tracked asyncio Task.
        """
        return self._scope.spawn(coroutine, name=name)

    def register_callback(
        self,
        callback: Callable[[], None] | Callable[[], Awaitable[None]],
    ) -> None:
        """Register a cleanup callback in the feature scope.

        Args:
            callback: Sync or async cleanup callable.
        """
        if inspect.iscoroutinefunction(callback):
            self._scope.async_callback(callback)
        else:
            self._scope.callback(callback)

    def enter_context[ContextT](
        self,
        cm: AbstractContextManager[ContextT],
        *,
        name: str = "",
    ) -> ContextT:
        """Enter a synchronous context manager and track its cleanup in this scope.

        Args:
            cm: Context manager to enter.
            name: Optional descriptive resource name.

        Returns:
            Resource yielded by context manager.
        """
        return self._scope.enter_context(cm, name=name)

    async def enter_async_context[ContextT](
        self,
        cm: AbstractAsyncContextManager[ContextT],
        *,
        name: str = "",
    ) -> ContextT:
        """Enter an asynchronous context manager and track its cleanup in this scope.

        Args:
            cm: Async context manager to enter.
            name: Optional descriptive resource name.

        Returns:
            Resource yielded by context manager.
        """
        return await self._scope.enter_async_context(cm, name=name)

    def subscribe[EventT](
        self,
        event_type: type[EventT],
        handler: Callable[[EventT], Any | Awaitable[Any]],
        mode: EventMode = EventMode.PUBLISH,
    ) -> None:
        """Subscribe a handler and register its disposal in this feature scope.

        Args:
            event_type: Target event class.
            handler: Event handler function or coroutine.
            mode: Dispatch mode for this subscription.
        """
        disposer = self._event_bus.subscribe(
            event_type, handler, mode=mode, owner_id=self._spec.feature_id
        )
        self._scope.callback(
            disposer,
            name=f"unsubscribe:{event_type.__name__}",
            effect_type=EffectType.EVENT_LISTENER,
        )

    async def publish(self, event: object) -> None:
        """Publish an event to the shared event bus.

        Args:
            event: Event object to broadcast.
        """
        await self._event_bus.publish(event)

    async def dispatch_pipeline[EventT](self, initial_event: EventT) -> EventT | None:
        """Dispatch an event through an interceptor pipeline.

        Args:
            initial_event: Initial event payload.

        Returns:
            Transformed event, or None if short-circuited.
        """
        return await self._event_bus.dispatch_pipeline(initial_event)
