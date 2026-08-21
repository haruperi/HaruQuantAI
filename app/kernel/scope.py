"""Temporal scope ownership for reversible feature runtime effects."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Coroutine, Sequence
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    AsyncExitStack,
)
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, TypeVar

T = TypeVar("T")
TaskFailureCallback = Callable[
    [str, str, BaseException], Coroutine[Any, Any, None] | None
]


class ScopeClosedError(RuntimeError):
    """Raised when a closed feature scope attempts to acquire an effect."""


class EffectType(StrEnum):
    """Categorization of runtime effects owned by a feature scope."""

    SERVICE_BINDING = "SERVICE_BINDING"
    EVENT_LISTENER = "EVENT_LISTENER"
    BACKGROUND_TASK = "BACKGROUND_TASK"
    CONTEXT_MANAGER = "CONTEXT_MANAGER"
    CLEANUP_CALLBACK = "CLEANUP_CALLBACK"
    CUSTOM = "CUSTOM"


@dataclass(slots=True)
class EffectRecord:
    """Diagnostic record for one lifecycle-managed effect."""

    owner_id: str
    effect_type: EffectType
    resource_name: str
    created_at: datetime
    cleaned_up: bool = False
    last_error: str | None = None


async def cancel_and_wait(task: asyncio.Task[Any]) -> None:
    """Cancel an asyncio task and await its completion safely."""
    if not task.done():
        task.cancel()
    await asyncio.gather(task, return_exceptions=True)


class FeatureScope:
    """Own and dispose all reversible effects of one mounted feature."""

    def __init__(
        self,
        owner_id: str,
        on_failure: TaskFailureCallback | None = None,
    ) -> None:
        """Initialize an open scope for a feature."""
        self.owner_id = owner_id
        self._stack = AsyncExitStack()
        self._effects: list[EffectRecord] = []
        self._closed = False
        self._on_failure = on_failure
        self._tracked_failure_tasks: set[asyncio.Task[Any]] = set()

    @property
    def is_closed(self) -> bool:
        """Return whether the scope has been closed."""
        return self._closed

    @property
    def effects(self) -> Sequence[EffectRecord]:
        """Return an immutable snapshot of tracked effects."""
        return tuple(self._effects)

    @property
    def active_effect_count(self) -> int:
        """Return the number of effects not yet cleaned up."""
        return sum(not effect.cleaned_up for effect in self._effects)

    @property
    def cleaned_effect_count(self) -> int:
        """Return the number of effects already cleaned up."""
        return sum(effect.cleaned_up for effect in self._effects)

    def set_failure_callback(self, callback: TaskFailureCallback | None) -> None:
        """Set the callback used for unexpected background-task failures."""
        self._on_failure = callback

    def ensure_open(self) -> None:
        """Raise ScopeClosedError when the scope is already closed."""
        if self._closed:
            msg = f"Feature scope '{self.owner_id}' is already closed"
            raise ScopeClosedError(msg)

    def callback(
        self,
        callback_fn: Callable[..., Any],
        *args: object,
        name: str = "",
        effect_type: EffectType = EffectType.CLEANUP_CALLBACK,
    ) -> None:
        """Register a synchronous cleanup callback."""
        self.ensure_open()
        record = EffectRecord(
            owner_id=self.owner_id,
            effect_type=effect_type,
            resource_name=name or getattr(callback_fn, "__name__", "callback"),
            created_at=datetime.now(UTC),
        )
        self._effects.append(record)

        def wrapped_disposer() -> None:
            try:
                callback_fn(*args)
            except Exception as error:
                record.last_error = str(error)
                raise
            finally:
                record.cleaned_up = True

        self._stack.callback(wrapped_disposer)

    def async_callback(
        self,
        callback_fn: Callable[..., Awaitable[Any]],
        *args: object,
        name: str = "",
        effect_type: EffectType = EffectType.CLEANUP_CALLBACK,
    ) -> None:
        """Register an asynchronous cleanup callback."""
        self.ensure_open()
        record = EffectRecord(
            owner_id=self.owner_id,
            effect_type=effect_type,
            resource_name=name or getattr(callback_fn, "__name__", "async_callback"),
            created_at=datetime.now(UTC),
        )
        self._effects.append(record)

        async def wrapped_disposer() -> None:
            try:
                await callback_fn(*args)
            except Exception as error:
                record.last_error = str(error)
                raise
            finally:
                record.cleaned_up = True

        self._stack.push_async_callback(wrapped_disposer)

    def spawn(
        self,
        coroutine: Coroutine[Any, Any, T],
        *,
        name: str,
    ) -> asyncio.Task[T]:
        """Spawn and supervise a background task owned by this scope."""
        try:
            self.ensure_open()
        except ScopeClosedError:
            coroutine.close()
            raise

        task_name = f"{self.owner_id}:{name}"
        task = asyncio.create_task(coroutine, name=task_name)
        record = EffectRecord(
            owner_id=self.owner_id,
            effect_type=EffectType.BACKGROUND_TASK,
            resource_name=task_name,
            created_at=datetime.now(UTC),
        )
        self._effects.append(record)

        def on_task_done(done_task: asyncio.Task[T]) -> None:
            if self._closed or done_task.cancelled():
                return
            error = done_task.exception()
            if error is None:
                return
            record.last_error = str(error)
            if self._on_failure is None:
                return
            failure_coro = self._on_failure(self.owner_id, name, error)
            if failure_coro is None:
                return
            failure_task = asyncio.create_task(
                failure_coro,
                name=f"{self.owner_id}:runtime-failure",
            )
            self._tracked_failure_tasks.add(failure_task)
            failure_task.add_done_callback(self._tracked_failure_tasks.discard)

        task.add_done_callback(on_task_done)

        async def teardown_task() -> None:
            try:
                await cancel_and_wait(task)
            except Exception as error:
                record.last_error = str(error)
                raise
            finally:
                record.cleaned_up = True

        self._stack.push_async_callback(teardown_task)
        return task

    def enter_context[ContextT](
        self,
        context_manager: AbstractContextManager[ContextT],
        *,
        name: str = "",
    ) -> ContextT:
        """Enter a synchronous context manager owned by this scope."""
        self.ensure_open()
        record = EffectRecord(
            owner_id=self.owner_id,
            effect_type=EffectType.CONTEXT_MANAGER,
            resource_name=name or type(context_manager).__name__,
            created_at=datetime.now(UTC),
        )
        self._effects.append(record)
        resource = self._stack.enter_context(context_manager)
        self._stack.callback(lambda: setattr(record, "cleaned_up", True))
        return resource

    async def enter_async_context[ContextT](
        self,
        context_manager: AbstractAsyncContextManager[ContextT],
        *,
        name: str = "",
    ) -> ContextT:
        """Enter an asynchronous context manager owned by this scope."""
        self.ensure_open()
        record = EffectRecord(
            owner_id=self.owner_id,
            effect_type=EffectType.CONTEXT_MANAGER,
            resource_name=name or type(context_manager).__name__,
            created_at=datetime.now(UTC),
        )
        self._effects.append(record)
        resource = await self._stack.enter_async_context(context_manager)

        async def mark_cleaned() -> None:
            record.cleaned_up = True

        self._stack.push_async_callback(mark_cleaned)
        return resource

    async def close(self) -> None:
        """Close the scope and run every disposer in reverse order."""
        if self._closed:
            return
        self._closed = True
        await self._stack.aclose()

        current = asyncio.current_task()
        pending_failures = [
            task
            for task in tuple(self._tracked_failure_tasks)
            if task is not current and not task.done()
        ]
        if pending_failures:
            await asyncio.gather(*pending_failures, return_exceptions=True)
