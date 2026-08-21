"""Temporal scope ownership for reversible feature runtime effects."""

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
    """Raised when attempting to register an effect onto a closed FeatureScope."""


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
    """Diagnostic tracking record for an active effect owned by a scope.

    Attributes:
        owner_id: Feature ID that owns this effect.
        effect_type: Classification of the effect.
        resource_name: Descriptive name of the registered resource.
        created_at: Timestamp when effect was registered.
        cleaned_up: Whether the effect disposal has completed.
        last_error: Error message if cleanup failed.
    """

    owner_id: str
    effect_type: EffectType
    resource_name: str
    created_at: datetime
    cleaned_up: bool = False
    last_error: str | None = None


async def cancel_and_wait(task: asyncio.Task[Any]) -> None:
    """Cancel an asyncio task and await its completion safely.

    Args:
        task: The task to cancel and await.
    """
    if not task.done():
        task.cancel()
    await asyncio.gather(task, return_exceptions=True)


class FeatureScope:
    """Owns and tracks all reversible runtime effects of one mounted feature."""

    def __init__(
        self,
        owner_id: str,
        on_failure: TaskFailureCallback | None = None,
    ) -> None:
        """Initialize a new feature scope.

        Args:
            owner_id: Unique identifier of the owning feature.
            on_failure: Optional callback triggered on unexpected background task crash.
        """
        self.owner_id = owner_id
        self._stack = AsyncExitStack()
        self._effects: list[EffectRecord] = []
        self._closed = False
        self._on_failure = on_failure
        self._tracked_failure_tasks: set[asyncio.Task[Any]] = set()

    def set_failure_callback(self, callback: TaskFailureCallback | None) -> None:
        """Set or update the runtime failure callback.

        Args:
            callback: Failure handler callback.
        """
        self._on_failure = callback

    @property
    def is_closed(self) -> bool:
        """Return whether this scope has been closed and disposed.

        Returns:
            True if closed, False otherwise.
        """
        return self._closed

    @property
    def effects(self) -> Sequence[EffectRecord]:
        """Return an immutable snapshot of all tracked effect records.

        Returns:
            Sequence of effect records registered in this scope.
        """
        return tuple(self._effects)

    def callback(
        self,
        callback_fn: Callable[..., Any],
        *args: object,
        name: str = "",
        effect_type: EffectType = EffectType.CLEANUP_CALLBACK,
    ) -> None:
        """Register a synchronous cleanup callback.

        Args:
            callback_fn: Callable to invoke on scope closure.
            *args: Positional arguments to pass to the callback.
            name: Optional descriptive resource name.
            effect_type: Category of this effect.

        Raises:
            ScopeClosedError: If this scope has already been closed.
        """
        if self._closed:
            msg = f"Cannot register callback on closed FeatureScope '{self.owner_id}'"
            raise ScopeClosedError(msg)

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
                record.cleaned_up = True
            except Exception as err:
                record.last_error = str(err)
                record.cleaned_up = True
                raise

        self._stack.callback(wrapped_disposer)

    def async_callback(
        self,
        callback_fn: Callable[..., Awaitable[Any]],
        *args: object,
        name: str = "",
        effect_type: EffectType = EffectType.CLEANUP_CALLBACK,
    ) -> None:
        """Register an asynchronous cleanup callback.

        Args:
            callback_fn: Coroutine function to invoke on scope closure.
            *args: Positional arguments to pass to the callback.
            name: Optional descriptive resource name.
            effect_type: Category of this effect.

        Raises:
            ScopeClosedError: If this scope has already been closed.
        """
        if self._closed:
            msg = f"Cannot register callback on closed FeatureScope '{self.owner_id}'"
            raise ScopeClosedError(msg)

        record = EffectRecord(
            owner_id=self.owner_id,
            effect_type=effect_type,
            resource_name=name or getattr(callback_fn, "__name__", "async_callback"),
            created_at=datetime.now(UTC),
        )
        self._effects.append(record)

        async def wrapped_async_disposer() -> None:
            try:
                await callback_fn(*args)
                record.cleaned_up = True
            except Exception as err:
                record.last_error = str(err)
                record.cleaned_up = True
                raise

        self._stack.push_async_callback(wrapped_async_disposer)

    def spawn(
        self,
        coroutine: Coroutine[Any, Any, T],
        *,
        name: str,
    ) -> asyncio.Task[T]:
        """Spawn a managed background task that will be cancelled on unmount.

        Args:
            coroutine: Coroutine to execute.
            name: Diagnostic name for the task.

        Returns:
            Tracked asyncio Task.

        Raises:
            ScopeClosedError: If this scope has already been closed.
        """
        if self._closed:
            msg = f"Cannot spawn task on closed FeatureScope '{self.owner_id}'"
            raise ScopeClosedError(msg)

        task_name = f"{self.owner_id}:{name}"
        task = asyncio.create_task(coroutine, name=task_name)
        record = EffectRecord(
            owner_id=self.owner_id,
            effect_type=EffectType.BACKGROUND_TASK,
            resource_name=task_name,
            created_at=datetime.now(UTC),
        )
        self._effects.append(record)

        def _on_task_done(t: asyncio.Task[Any]) -> None:
            if self._closed or t.cancelled():
                return
            exc = t.exception()
            if exc is not None and self._on_failure is not None:
                coro = self._on_failure(self.owner_id, name, exc)
                if coro is not None:
                    bg_task = asyncio.create_task(coro)
                    self._tracked_failure_tasks.add(bg_task)
                    bg_task.add_done_callback(self._tracked_failure_tasks.discard)

        task.add_done_callback(_on_task_done)

        async def teardown_task() -> None:
            try:
                await cancel_and_wait(task)
                record.cleaned_up = True
            except Exception as err:
                record.last_error = str(err)
                record.cleaned_up = True
                raise

        self._stack.push_async_callback(teardown_task)
        return task

    def enter_context[ContextT](
        self,
        cm: AbstractContextManager[ContextT],
        *,
        name: str = "",
    ) -> ContextT:
        """Enter a synchronous context manager and track its cleanup.

        Args:
            cm: Context manager to enter.
            name: Optional descriptive resource name.

        Returns:
            Resource yielded by the context manager.

        Raises:
            ScopeClosedError: If this scope has already been closed.
        """
        if self._closed:
            msg = (
                f"Cannot enter context manager on closed FeatureScope '{self.owner_id}'"
            )
            raise ScopeClosedError(msg)

        record = EffectRecord(
            owner_id=self.owner_id,
            effect_type=EffectType.CONTEXT_MANAGER,
            resource_name=name or type(cm).__name__,
            created_at=datetime.now(UTC),
        )
        self._effects.append(record)
        res = self._stack.enter_context(cm)
        self._stack.callback(lambda: setattr(record, "cleaned_up", True))
        return res

    async def enter_async_context[ContextT](
        self,
        cm: AbstractAsyncContextManager[ContextT],
        *,
        name: str = "",
    ) -> ContextT:
        """Enter an asynchronous context manager and track its cleanup.

        Args:
            cm: Async context manager to enter.
            name: Optional descriptive resource name.

        Returns:
            Resource yielded by the context manager.

        Raises:
            ScopeClosedError: If this scope has already been closed.
        """
        if self._closed:
            msg = f"Cannot enter async context on closed FeatureScope '{self.owner_id}'"
            raise ScopeClosedError(msg)

        record = EffectRecord(
            owner_id=self.owner_id,
            effect_type=EffectType.CONTEXT_MANAGER,
            resource_name=name or type(cm).__name__,
            created_at=datetime.now(UTC),
        )
        self._effects.append(record)
        res = await self._stack.enter_async_context(cm)

        async def mark_done() -> None:
            record.cleaned_up = True

        self._stack.push_async_callback(mark_done)
        return res

    async def close(self) -> None:
        """Close this scope and invoke all disposers in reverse order.

        This method is idempotent.
        """
        if self._closed:
            return
        self._closed = True
        await self._stack.aclose()
