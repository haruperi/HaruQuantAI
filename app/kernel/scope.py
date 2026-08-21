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
TaskFailureHandler = Callable[[str, BaseException], Awaitable[None] | None]


class ScopeClosedError(RuntimeError):
    """Raised when a closed feature scope attempts to acquire a new effect."""


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
    """Diagnostic tracking record for an effect owned by a scope."""

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
    """Own and track all reversible runtime effects of one mounted feature."""

    def __init__(
        self,
        owner_id: str,
        *,
        on_task_failure: TaskFailureHandler | None = None,
    ) -> None:
        self.owner_id = owner_id
        self._stack = AsyncExitStack()
        self._effects: list[EffectRecord] = []
        self._closed = False
        self._on_task_failure = on_task_failure

    @property
    def is_closed(self) -> bool:
        return self._closed

    @property
    def effects(self) -> Sequence[EffectRecord]:
        return tuple(self._effects)

    @property
    def active_effect_count(self) -> int:
        """Return the number of effects not yet cleaned up."""
        return sum(not effect.cleaned_up for effect in self._effects)

    @property
    def cleaned_effect_count(self) -> int:
        """Return the number of effects already cleaned up."""
        return sum(effect.cleaned_up for effect in self._effects)

    def _ensure_open(self) -> None:
        if self._closed:
            raise ScopeClosedError(
                f"Feature scope '{self.owner_id}' is already closed"
            )

    def callback(
        self,
        callback_fn: Callable[..., Any],
        *args: object,
        name: str = "",
        effect_type: EffectType = EffectType.CLEANUP_CALLBACK,
    ) -> None:
        """Register a synchronous cleanup callback."""
        self._ensure_open()
        record = EffectRecord(
            owner_id=self.owner_id,
            effect_type=effect_type,
            resource_name=name or callback_fn.__name__,
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
        self._ensure_open()
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
            except Exception as error:
                record.last_error = str(error)
                raise
            finally:
                record.cleaned_up = True

        self._stack.push_async_callback(wrapped_async_disposer)

    def spawn(
        self,
        coroutine: Coroutine[Any, Any, T],
        *,
        name: str,
    ) -> asyncio.Task[T]:
        """Spawn a managed background task and supervise unexpected failures."""
        self._ensure_open()
        task_name = f"{self.owner_id}:{name}"
        task = asyncio.create_task(coroutine, name=task_name)
        record = EffectRecord(
            owner_id=self.owner_id,
            effect_type=EffectType.BACKGROUND_TASK,
            resource_name=task_name,
            created_at=datetime.now(UTC),
        )
        self._effects.append(record)

        def task_done(done_task: asyncio.Task[T]) -> None:
            if done_task.cancelled() or self._closed:
                return
            error = done_task.exception()
            if error is None:
                return
            record.last_error = str(error)
            if self._on_task_failure is None:
                return
            result = self._on_task_failure(self.owner_id, error)
            if result is not None:
                asyncio.create_task(
                    result,
                    name=f"{self.owner_id}:runtime-failure",
                )

        task.add_done_callback(task_done)

        async def teardown_task() -> None:
            try:
                await cancel_and_wait(task)
            finally:
                record.cleaned_up = True

        self._stack.push_async_callback(teardown_task)
        return task

    def enter_context[ContextT](
        self,
        cm: AbstractContextManager[ContextT],
        *,
        name: str = "",
    ) -> ContextT:
        """Enter a synchronous context manager and track its cleanup."""
        self._ensure_open()
        record = EffectRecord(
            owner_id=self.owner_id,
            effect_type=EffectType.CONTEXT_MANAGER,
            resource_name=name or type(cm).__name__,
            created_at=datetime.now(UTC),
        )
        self._effects.append(record)
        resource = self._stack.enter_context(cm)
        self._stack.callback(lambda: setattr(record, "cleaned_up", True))
        return resource

    async def enter_async_context[ContextT](
        self,
        cm: AbstractAsyncContextManager[ContextT],
        *,
        name: str = "",
    ) -> ContextT:
        """Enter an asynchronous context manager and track its cleanup."""
        self._ensure_open()
        record = EffectRecord(
            owner_id=self.owner_id,
            effect_type=EffectType.CONTEXT_MANAGER,
            resource_name=name or type(cm).__name__,
            created_at=datetime.now(UTC),
        )
        self._effects.append(record)
        resource = await self._stack.enter_async_context(cm)

        async def mark_done() -> None:
            record.cleaned_up = True

        self._stack.push_async_callback(mark_done)
        return resource

    async def close(self) -> None:
        """Close this scope and invoke all disposers in reverse order idempotently."""
        if self._closed:
            return
        self._closed = True
        await self._stack.aclose()
