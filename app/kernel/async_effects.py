"""Asynchronous effect scope adapter for edge coroutines and async context managers.

Traces to: P5-T04, Gate G5
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager, AsyncExitStack
from typing import TypeVar

from app.kernel.effects import EffectScope
from app.kernel.errors import LifecycleError

T = TypeVar("T")


class AsyncEffectScopeAdapter:
    """Asynchronous adapter delegating synchronous effects to an EffectScope while managing async cleanup."""

    def __init__(self, sync_scope: EffectScope) -> None:
        """Initialize adapter around an existing open EffectScope.

        Args:
            sync_scope: Open synchronous EffectScope.

        Raises:
            LifecycleError: If sync_scope is already closed.
        """
        if sync_scope.closed:
            raise LifecycleError("cannot adapt a closed effect scope")

        self._sync_scope = sync_scope
        self._async_stack = AsyncExitStack()
        self._closed = False

    @property
    def closed(self) -> bool:
        """Return True if this async adapter has been closed."""
        return self._closed or self._sync_scope.closed

    def callback(self, disposer: Callable[[], object]) -> None:
        """Register a synchronous disposer callback.

        Args:
            disposer: Zero-argument callable.

        Raises:
            LifecycleError: If scope is closed.
        """
        if self.closed:
            raise LifecycleError("async effect scope is closed")
        self._sync_scope.callback(disposer)

    async def enter_async_context(self, resource: AbstractAsyncContextManager[T]) -> T:
        """Enter an asynchronous context manager and register its exit on async teardown.

        Args:
            resource: Async context manager.

        Returns:
            Entered resource value.

        Raises:
            LifecycleError: If scope is closed.
        """
        if self.closed:
            raise LifecycleError("async effect scope is closed")

        return await self._async_stack.enter_async_context(resource)

    async def aclose(self) -> None:
        """Close the async adapter and the underlying sync scope in order.

        Async context managers are exited first, followed by synchronous scope close.

        Raises:
            LifecycleError: If any async or sync disposers fail.
        """
        if self._closed:
            return

        failures: list[BaseException] = []

        # 1. Close async stack
        try:
            await self._async_stack.aclose()
        except BaseException as exc:
            failures.append(exc)

        # 2. Close sync scope
        try:
            self._sync_scope.close()
        except LifecycleError as exc:
            if exc.failures:
                failures.extend(exc.failures)
            else:
                failures.append(exc)
        except BaseException as exc:
            failures.append(exc)

        self._closed = True

        if failures:
            msg = f"async effect scope cleanup failed: {len(failures)} failure(s)"
            raise LifecycleError(msg, failures=tuple(failures))


__all__ = ("AsyncEffectScopeAdapter",)
