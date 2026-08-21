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
    """Scoped runtime operations available to mounting features."""

    def require[CapT](self, capability: CapabilityKey[CapT]) -> CapT: ...

    def optional[CapT](self, capability: CapabilityKey[CapT]) -> CapT | None: ...

    def provide[CapT](
        self,
        capability: CapabilityKey[CapT],
        implementation: CapT,
    ) -> None: ...

    def spawn(
        self,
        coroutine: Coroutine[Any, Any, Any],
        *,
        name: str,
    ) -> asyncio.Task[Any]: ...

    def register_callback(
        self,
        callback: Callable[[], None] | Callable[[], Awaitable[None]],
    ) -> None: ...

    def enter_context[ContextT](
        self,
        context_manager: AbstractContextManager[ContextT],
        *,
        name: str = "",
    ) -> ContextT: ...

    async def enter_async_context[ContextT](
        self,
        context_manager: AbstractAsyncContextManager[ContextT],
        *,
        name: str = "",
    ) -> ContextT: ...

    def subscribe[EventT](
        self,
        event_type: type[EventT],
        handler: Callable[[EventT], Any | Awaitable[Any]],
        mode: EventMode = EventMode.PUBLISH,
    ) -> None: ...

    async def publish(self, event: object) -> None: ...

    async def dispatch_pipeline[EventT](
        self,
        initial_event: EventT,
    ) -> EventT | None: ...


class DefaultFeatureContext:
    """Concrete FeatureContext implementation wired to a private FeatureScope."""

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
        self._spec = spec
        self._scope = scope
        self._resolver = resolver or (lambda _cap: None)
        self._provider_registrar = provider_registrar or (
            lambda _cap, _impl, _scope: None
        )
        self._event_bus = event_bus or EventBus()

    @property
    def scope(self) -> FeatureScope:
        return self._scope

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    def require[CapT](self, capability: CapabilityKey[CapT]) -> CapT:
        """Resolve a declared required or optional capability."""
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
        """Resolve a declared optional capability when available."""
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
        """Stage a provider declared by this feature specification."""
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
        return self._scope.spawn(coroutine, name=name)

    def register_callback(
        self,
        callback: Callable[[], None] | Callable[[], Awaitable[None]],
    ) -> None:
        if inspect.iscoroutinefunction(callback):
            self._scope.async_callback(callback)
        else:
            self._scope.callback(callback)

    def enter_context[ContextT](
        self,
        context_manager: AbstractContextManager[ContextT],
        *,
        name: str = "",
    ) -> ContextT:
        """Enter a synchronous managed resource owned by the feature scope."""
        return self._scope.enter_context(context_manager, name=name)

    async def enter_async_context[ContextT](
        self,
        context_manager: AbstractAsyncContextManager[ContextT],
        *,
        name: str = "",
    ) -> ContextT:
        """Enter an asynchronous managed resource owned by the feature scope."""
        return await self._scope.enter_async_context(context_manager, name=name)

    def subscribe[EventT](
        self,
        event_type: type[EventT],
        handler: Callable[[EventT], Any | Awaitable[Any]],
        mode: EventMode = EventMode.PUBLISH,
    ) -> None:
        """Subscribe with exact-registration disposal bound to this scope."""
        disposer = self._event_bus.subscribe(event_type, handler, mode=mode)
        self._scope.callback(
            disposer,
            name=f"event:{event_type.__name__}:{mode.value}",
            effect_type=EffectType.EVENT_LISTENER,
        )

    async def publish(self, event: object) -> None:
        await self._event_bus.publish(event)

    async def dispatch_pipeline[EventT](
        self,
        initial_event: EventT,
    ) -> EventT | None:
        return await self._event_bus.dispatch_pipeline(initial_event)
