"""Scoped effect management and managed lifecycle."""

from __future__ import annotations

import asyncio
import contextlib
import functools
from collections.abc import Callable, Coroutine
from typing import Any


class EffectScope:
    """Manages asynchronous tasks and registered cleanup handlers."""

    def __init__(self) -> None:
        self._cleanups: list[Callable[[], Any]] = []
        self._tasks: set[asyncio.Task[Any]] = set()
        self._closed = False

    def spawn(self, coro: Coroutine[Any, Any, Any]) -> asyncio.Task[Any]:
        """Spawn a managed background task.

        Args:
            coro: Coroutine to execute.

        Returns:
            Spawned asyncio.Task.
        """
        if self._closed:
            raise RuntimeError("EffectScope is closed.")
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    def on_cleanup(self, cleanup: Callable[[], Any]) -> None:
        """Register a cleanup callback.

        Args:
            cleanup: Callable to run on close.
        """
        if self._closed:
            cleanup()
            return
        self._cleanups.append(cleanup)

    def callback(
        self, callback: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Callable[..., Any]:
        """Register a callback to be called on scope exit.

        Args:
            callback: Callable to run on close.
            *args: Positional arguments for callback.
            **kwargs: Keyword arguments for callback.

        Returns:
            The registered callback.
        """
        cb = (
            functools.partial(callback, *args, **kwargs)
            if (args or kwargs)
            else callback
        )
        self.on_cleanup(cb)
        return callback

    def close(self) -> None:
        """Close the scope, cancel tasks, and run cleanups."""
        self._closed = True
        for task in list(self._tasks):
            if not task.done():
                task.cancel()
        for cleanup in reversed(self._cleanups):
            with contextlib.suppress(Exception):
                cleanup()
        self._tasks.clear()
        self._cleanups.clear()

    async def aclose(self) -> None:
        """Asynchronously close the scope and await tasks."""
        self._closed = True
        tasks = list(self._tasks)
        for task in tasks:
            if not task.done():
                task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        for cleanup in reversed(self._cleanups):
            with contextlib.suppress(Exception):
                res = cleanup()
                if asyncio.iscoroutine(res):
                    await res
        self._tasks.clear()
        self._cleanups.clear()
