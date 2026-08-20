"""Synchronous effect scope for managing reversible resources and clean teardown.

Traces to: P5-T01, Gate G5
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import TypeVar

from app.kernel.errors import LifecycleError

T = TypeVar("T")


class EffectScope:
    """Owner of synchronous resources, context managers, and disposer callbacks."""

    def __init__(self, *, can_dispose: Callable[[], bool] | None = None) -> None:
        """Initialize an EffectScope.

        Args:
            can_dispose: Optional predicate deciding if scope is eligible for disposal.
        """
        self._can_dispose_pred = can_dispose
        self._disposers: list[Callable[[], object]] = []
        self._closed = False

    @property
    def closed(self) -> bool:
        """Return True if this effect scope has been closed."""
        return self._closed

    def can_dispose(self) -> bool:
        """Check if this scope can be safely disposed."""
        if self._can_dispose_pred is not None:
            return bool(self._can_dispose_pred())
        return True

    def callback(self, disposer: Callable[[], object]) -> None:
        """Register a zero-argument callable to be executed on scope close.

        Args:
            disposer: Zero-argument callable.

        Raises:
            LifecycleError: If the scope is already closed.
        """
        if self._closed:
            raise LifecycleError("effect scope is closed")
        self._disposers.append(disposer)

    def enter_context(self, resource: AbstractContextManager[T]) -> T:
        """Enter a context manager and register its exit on scope close.

        Args:
            resource: Context manager to enter.

        Returns:
            Entered context value.

        Raises:
            LifecycleError: If the scope is already closed.
        """
        if self._closed:
            raise LifecycleError("effect scope is closed")

        val = resource.__enter__()
        self._disposers.append(lambda: resource.__exit__(None, None, None))
        return val

    def close(self) -> None:
        """Close this effect scope and execute all disposers in reverse registration order.

        Raises:
            LifecycleError: If disposal was refused by can_dispose predicate, or if disposers failed.
        """
        if self._closed:
            return

        if not self.can_dispose():
            raise LifecycleError("effect scope refused disposal")

        failures: list[BaseException] = []

        while self._disposers:
            disposer = self._disposers.pop()
            try:
                disposer()
            except BaseException as exc:
                failures.append(exc)

        self._closed = True

        if failures:
            msg = f"effect scope cleanup failed: {len(failures)} disposer(s)"
            raise LifecycleError(msg, failures=tuple(failures))


__all__ = ("EffectScope",)
