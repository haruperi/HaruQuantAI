"""Restricted feature scope for dependencies, exports, and owned resources.

This module implements ``FeatureContext``, the single object a feature
receives at startup, together with ``KernelDiagnostic``, the immutable
observation record scopes emit through an injected sink. The scope
enforces each feature's declaration: dependency reads are limited to
``FeatureSpec.requires``, export writes to ``FeatureSpec.provides``, and
every entered resource, registered callback, and spawned task is owned
by the scope and released exactly once at close, in reverse order.

Authority: this module is part of the standard-library kernel required
by ``AGENTS.md``. It builds only on the Python standard library and the
kernel's capability and feature declarations. Importing it performs no
I/O, starts no tasks or threads, configures no logging, and reads no
environment.
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable, Coroutine, Mapping
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    AsyncExitStack,
)
from dataclasses import dataclass
from typing import Any, cast

from app.kernel.capability import Capability, CapabilityUnavailableError
from app.kernel.feature import FeatureSpec


@dataclass(frozen=True, slots=True)
class KernelDiagnostic:
    """Describe a business-neutral lifecycle observation.

    An immutable record emitted through the diagnostic sink; the kernel
    never logs, prints, or interprets observations itself.

    Attributes:
        code: Stable dotted observation code (for example
            ``kernel.cleanup.task_failed``).
        owner: Name of the feature that produced the observation, or
            ``"runtime"`` for composition-level events.
        detail: Short payload such as an error type name; may be empty.
    """

    code: str
    owner: str
    detail: str = ""


type DiagnosticSink = Callable[[KernelDiagnostic], None]
type CloseCallback = Callable[[], Awaitable[None] | None]


def _ignore_diagnostic(_diagnostic: KernelDiagnostic) -> None:
    """Accept a diagnostic when composition did not install an observer."""


class FeatureContext:
    """Restrict one component to its declared dependencies and owned scope.

    The runtime constructs one context per feature start and closes it
    during shutdown; the class is also directly constructible, as the
    kernel tests do. Reads honor the declaration: ``require`` resolves
    only capabilities in ``FeatureSpec.requires``, ``provide`` stages
    only capabilities in ``FeatureSpec.provides``, and publication is
    all-or-nothing through ``commit_exports``. Every resource entered,
    callback registered, and task spawned is owned by the scope and
    released exactly once when it closes.

    The context adds no locking; it is driven sequentially by one
    feature's ``start`` and one ``close``. Cleanup honors LIFO order
    across all ownership kinds, and ``close`` is idempotent.

    Args:
        spec: The declaration restricting this scope.
        providers: Mapping of already-published provider values; stored
            as given, not copied.
        diagnostic_sink: Receiver for cleanup diagnostics; defaults to
            a sink that drops every diagnostic.
    """

    def __init__(
        self,
        spec: FeatureSpec,
        providers: Mapping[Capability[Any], object],
        diagnostic_sink: DiagnosticSink = _ignore_diagnostic,
    ) -> None:
        self._spec = spec
        self._providers = providers
        self._diagnostic_sink = diagnostic_sink
        self._staged: dict[Capability[Any], object] = {}
        self._stack = AsyncExitStack()
        self._closed = False
        self._published = False
        self._cleanup_errors: list[BaseException] = []

    @property
    def is_open(self) -> bool:
        """Return whether this lifecycle scope accepts operations.

        Returns:
            ``True`` until ``close`` is invoked; ``False`` from the
            moment close begins, after which every scope operation
            fails closed.
        """
        return not self._closed

    @property
    def staged_capabilities(self) -> frozenset[Capability[Any]]:
        """Return only this component's staged exports.

        Returns:
            A fresh ``frozenset`` of the capabilities staged so far
            through ``provide``; dependencies and undeclared
            capabilities are never included.
        """
        return frozenset(self._staged)

    def _ensure_open(self) -> None:
        """Raise ``RuntimeError`` when the scope has already closed."""
        if self._closed:
            raise RuntimeError(f"Feature scope for '{self._spec.name}' is closed")

    def _diagnose(self, code: str, detail: str = "") -> None:
        """Emit one diagnostic, suppressing any observer failure."""
        try:
            self._diagnostic_sink(KernelDiagnostic(code, self._spec.name, detail))
        except BaseException:
            return

    def require[T](self, key: Capability[T]) -> T:
        """Resolve one declared mandatory dependency.

        Fails closed: the capability must be declared in this feature's
        ``requires`` and a provider value must already be published;
        this method never returns a substitute or partial value.

        Args:
            key: The capability binding to resolve.

        Returns:
            The provider's published value, typed as ``T``.

        Raises:
            RuntimeError: If the scope is closed.
            ValueError: If ``key`` is not declared in this feature's
                ``FeatureSpec.requires``.
            CapabilityUnavailableError: If ``key`` is declared but no
                value is published, with ``blocked_by`` set to this
                feature's name.
        """
        self._ensure_open()
        if key not in self._spec.requires:
            raise ValueError(f"Undeclared dependency: {self._spec.name}: {key.name}")
        if key not in self._providers:
            raise CapabilityUnavailableError(key.identifier, blocked_by=self._spec.name)
        return cast("T", self._providers[key])

    def provide[T](self, key: Capability[T], service: T) -> None:
        """Stage one declared export for atomic publication after startup.

        Staged values stay invisible to other features until the
        runtime commits the complete bundle after ``start`` returns.

        Args:
            key: The capability binding to stage; must be declared in
                this feature's ``FeatureSpec.provides``.
            service: The value to publish for ``key``.

        Raises:
            RuntimeError: If the scope is closed.
            ValueError: If ``key`` is undeclared, already staged, or
                the export bundle was already committed.
        """
        self._ensure_open()
        if self._published or key not in self._spec.provides or key in self._staged:
            raise ValueError("Export is undeclared, duplicate, or already published")
        self._staged[key] = service

    def commit_exports(self) -> dict[Capability[Any], object]:
        """Return the complete declared export bundle exactly once.

        Called by the runtime after ``start`` returns; the staged set
        must equal ``FeatureSpec.provides`` exactly.

        Returns:
            A new mapping of every declared capability to its staged
            value, for the runtime to publish.

        Raises:
            RuntimeError: If the scope is closed.
            ValueError: If called a second time, or if the staged set
                differs from the declared ``provides`` set.
        """
        self._ensure_open()
        if self._published or frozenset(self._staged) != self._spec.provides:
            raise ValueError("Feature did not stage its exact export bundle")
        self._published = True
        return dict(self._staged)

    def on_close(self, callback: CloseCallback) -> None:
        """Register a synchronous or asynchronous cleanup callback.

        Callbacks run when the scope closes, in reverse registration
        order (LIFO), interleaved with resource exits and task shutdown
        in that same order. A failing callback is diagnosed, recorded,
        and aggregated into the ``BaseExceptionGroup`` raised by
        ``close``; it never prevents the remaining callbacks from
        running.

        Args:
            callback: Zero-argument callable returning ``None`` or an
                awaitable.

        Raises:
            RuntimeError: If the scope is closed.
        """
        self._ensure_open()

        async def guarded() -> None:
            try:
                result = callback()
                if inspect.isawaitable(result):
                    await result
            except BaseException as error:
                self._diagnose("kernel.cleanup.callback_failed", type(error).__name__)
                self._cleanup_errors.append(error)

        self._stack.push_async_callback(guarded)

    def enter_context[T](self, resource: AbstractContextManager[T]) -> T:
        """Enter and own a synchronous context manager.

        The resource is entered immediately, and its ``__exit__`` is
        invoked with no exception information when the scope closes, in
        reverse acquisition order. A failing release is diagnosed and
        aggregated by ``close``; an exception from ``__enter__``
        propagates unchanged and unwinds nothing here.

        Args:
            resource: The synchronous context manager to enter.

        Returns:
            The value yielded by ``resource.__enter__()``.

        Raises:
            RuntimeError: If the scope is closed.
        """
        self._ensure_open()
        value = resource.__enter__()

        async def release() -> None:
            try:
                resource.__exit__(None, None, None)
            except BaseException as error:
                self._diagnose("kernel.cleanup.context_failed", type(error).__name__)
                self._cleanup_errors.append(error)

        self._stack.push_async_callback(release)
        return value

    async def enter[T](self, resource: AbstractAsyncContextManager[T]) -> T:
        """Enter and own an asynchronous context manager.

        The resource is entered immediately, and its ``__aexit__`` is
        awaited with no exception information when the scope closes, in
        reverse acquisition order. A failing release is diagnosed and
        aggregated by ``close``; an exception from ``__aenter__``
        propagates unchanged and unwinds nothing here.

        Args:
            resource: The asynchronous context manager to enter.

        Returns:
            The value yielded by ``resource.__aenter__()``.

        Raises:
            RuntimeError: If the scope is closed.
        """
        self._ensure_open()
        value = await resource.__aenter__()

        async def release() -> None:
            try:
                await resource.__aexit__(None, None, None)
            except BaseException as error:
                self._diagnose("kernel.cleanup.context_failed", type(error).__name__)
                self._cleanup_errors.append(error)

        self._stack.push_async_callback(release)
        return value

    enter_async_context = enter

    def spawn[T](
        self, coroutine: Coroutine[Any, Any, T], *, name: str | None = None
    ) -> asyncio.Task[T]:
        """Create a task whose cancellation and result belong to this scope.

        The task is scheduled immediately. When the scope closes, an
        unfinished task is cancelled and awaited; the resulting
        ``asyncio.CancelledError`` is ignored, while any other failure
        is diagnosed and aggregated into the ``BaseExceptionGroup``
        raised by ``close``.

        Args:
            coroutine: The coroutine to schedule.
            name: Optional task name forwarded to
                ``asyncio.create_task``.

        Returns:
            The created ``asyncio.Task``.

        Raises:
            RuntimeError: If the scope is closed; the coroutine is
                closed without being scheduled.
        """
        if self._closed:
            coroutine.close()
            raise RuntimeError(f"Feature scope for '{self._spec.name}' is closed")
        task = asyncio.create_task(coroutine, name=name)

        async def stop() -> None:
            if not task.done():
                task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                return
            except BaseException as error:
                self._diagnose("kernel.cleanup.task_failed", type(error).__name__)
                self._cleanup_errors.append(error)

        self._stack.push_async_callback(stop)
        return task

    async def close(self) -> None:
        """Close all owned resources once and aggregate independent failures.

        Idempotent: later calls return immediately. Callbacks, resource
        releases, and task shutdown run in reverse registration order
        (LIFO), and every owned cleanup is attempted even when an
        earlier one fails; independent failures are raised together in
        one ``BaseExceptionGroup`` labeled with the feature name. Once
        close begins, the scope rejects all further operations.

        Raises:
            BaseExceptionGroup: If one or more owned cleanups failed.
        """
        if self._closed:
            return
        self._closed = True
        await self._stack.aclose()
        if self._cleanup_errors:
            errors, self._cleanup_errors = self._cleanup_errors, []
            raise BaseExceptionGroup(
                f"Feature cleanup failed: {self._spec.name}", errors
            )


__all__ = ("DiagnosticSink", "FeatureContext", "KernelDiagnostic")
