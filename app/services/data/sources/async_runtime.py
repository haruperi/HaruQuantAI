"""Persistent serialized event-loop ownership for provider sessions."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Coroutine
from concurrent.futures import Future
from typing import Any


class _PersistentAsyncRunner:
    """Run provider coroutines on one lazily started, thread-owned event loop."""

    def __init__(self, *, thread_name: str) -> None:
        """Initialize an inactive runner.

        Args:
            thread_name: Diagnostic name assigned to the loop-owner thread.
        """
        self._thread_name = thread_name
        self._lock = threading.RLock()
        self._ready = threading.Event()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._closed = False

    def _start_locked(self) -> asyncio.AbstractEventLoop:
        """Start the owner thread while the caller holds ``self._lock``.

        Returns:
            The running persistent event loop.

        Raises:
            RuntimeError: If the owner thread cannot initialize its loop.
        """
        if self._thread is None:
            self._thread = threading.Thread(
                target=self._run_loop,
                name=self._thread_name,
                daemon=True,
            )
            self._thread.start()
            self._ready.wait()
        if self._loop is None:
            raise RuntimeError("provider event loop failed to initialize")
        return self._loop

    def _run_loop(self) -> None:
        """Own and deterministically release the provider event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        self._ready.set()
        try:
            loop.run_forever()
        finally:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True)
                )
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(loop.shutdown_default_executor())
            loop.close()

    def run[T](self, operation: Coroutine[Any, Any, T]) -> T:
        """Run one coroutine serially on the persistent loop.

        Args:
            operation: Provider coroutine to execute.

        Returns:
            The coroutine result.

        Raises:
            RuntimeError: If the runner has already closed.
            Exception: Any exception raised by the submitted coroutine.
        """
        with self._lock:
            if self._closed:
                operation.close()
                raise RuntimeError("provider event-loop runner is closed")
            loop = self._start_locked()
            future: Future[T] = asyncio.run_coroutine_threadsafe(operation, loop)
            return future.result()

    def close(self) -> None:
        """Stop and join the loop-owner thread idempotently."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            loop = self._loop
            thread = self._thread
            if loop is None or thread is None:
                return
            loop.call_soon_threadsafe(loop.stop)
            thread.join()


__all__: tuple[str, ...] = ()
