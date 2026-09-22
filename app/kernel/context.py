"""Restricted feature scope for dependencies, exports, and owned resources."""

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
    """Describe a business-neutral lifecycle observation."""

    code: str
    owner: str
    detail: str = ""


type DiagnosticSink = Callable[[KernelDiagnostic], None]
type CloseCallback = Callable[[], Awaitable[None] | None]


def _ignore_diagnostic(_diagnostic: KernelDiagnostic) -> None:
    """Accept a diagnostic when composition did not install an observer."""


class FeatureContext:
    """Restrict one component to its declared dependencies and owned scope."""

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
        """Return whether this lifecycle scope accepts operations."""
        return not self._closed

    @property
    def staged_capabilities(self) -> frozenset[Capability[Any]]:
        """Return only this component's staged exports."""
        return frozenset(self._staged)

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError(f"Feature scope for '{self._spec.name}' is closed")

    def _diagnose(self, code: str, detail: str = "") -> None:
        try:
            self._diagnostic_sink(KernelDiagnostic(code, self._spec.name, detail))
        except BaseException:
            return

    def require[T](self, key: Capability[T]) -> T:
        """Resolve one declared mandatory dependency."""
        self._ensure_open()
        if key not in self._spec.requires:
            raise ValueError(f"Undeclared dependency: {self._spec.name}: {key.name}")
        if key not in self._providers:
            raise CapabilityUnavailableError(key.identifier, blocked_by=self._spec.name)
        return cast("T", self._providers[key])

    def provide[T](self, key: Capability[T], service: T) -> None:
        """Stage one declared export for atomic publication after startup."""
        self._ensure_open()
        if self._published or key not in self._spec.provides or key in self._staged:
            raise ValueError("Export is undeclared, duplicate, or already published")
        self._staged[key] = service

    def commit_exports(self) -> dict[Capability[Any], object]:
        """Return the complete declared export bundle exactly once."""
        self._ensure_open()
        if self._published or frozenset(self._staged) != self._spec.provides:
            raise ValueError("Feature did not stage its exact export bundle")
        self._published = True
        return dict(self._staged)

    def on_close(self, callback: CloseCallback) -> None:
        """Register a synchronous or asynchronous cleanup callback."""
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
        """Enter and own a synchronous context manager."""
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
        """Enter and own an asynchronous context manager."""
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
        """Create a task whose cancellation and result belong to this scope."""
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
        """Close all owned resources once and aggregate independent failures."""
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
