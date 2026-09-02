"""Unit tests for kernel EffectScope and lifecycle management."""

from __future__ import annotations

import asyncio

import pytest
from app.kernel.effects import EffectScope


@pytest.mark.asyncio
async def test_effect_scope_spawn_and_done_callback() -> None:
    """Verify EffectScope can spawn coroutines and remove them upon completion."""
    scope = EffectScope()
    executed = False

    async def sample_coro() -> None:
        nonlocal executed
        await asyncio.sleep(0.01)
        executed = True

    task = scope.spawn(sample_coro())
    assert not task.done()
    await task
    assert executed
    assert len(scope._tasks) == 0
    scope.close()


def test_effect_scope_cleanup_callbacks_sync() -> None:
    """Verify on_cleanup and callback run in reverse registration order on close."""
    scope = EffectScope()
    log: list[str] = []

    scope.on_cleanup(lambda: log.append("cleanup1"))
    scope.on_cleanup(lambda: log.append("cleanup2"))

    def custom_fn(val: str) -> None:
        log.append(f"custom:{val}")

    cb = scope.callback(custom_fn, "arg1")
    assert callable(cb)

    scope.close()
    assert log == ["custom:arg1", "cleanup2", "cleanup1"]

    # Calling on_cleanup on a closed scope executes immediately
    scope.on_cleanup(lambda: setattr(scope, "_flag", True))
    assert getattr(scope, "_flag", False) is True


@pytest.mark.asyncio
async def test_effect_scope_spawn_on_closed_raises_error() -> None:
    """Verify spawning on a closed scope raises RuntimeError."""
    scope = EffectScope()
    scope.close()

    async def noop() -> None:
        pass

    coro = noop()
    try:
        with pytest.raises(RuntimeError, match="EffectScope is closed"):
            scope.spawn(coro)
    finally:
        coro.close()


@pytest.mark.asyncio
async def test_effect_scope_aclose_cancels_tasks_and_runs_async_cleanups() -> None:
    """Verify aclose cancels running tasks and handles async/sync cleanups."""
    scope = EffectScope()
    cancelled = False
    async_cleanup_ran = False
    sync_cleanup_ran = False

    async def long_running() -> None:
        nonlocal cancelled
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            cancelled = True
            raise

    scope.spawn(long_running())
    # Yield control to let task start
    await asyncio.sleep(0.01)

    async def async_cleanup() -> None:
        nonlocal async_cleanup_ran
        await asyncio.sleep(0.01)
        async_cleanup_ran = True

    def sync_cleanup() -> None:
        nonlocal sync_cleanup_ran
        sync_cleanup_ran = True

    def failing_cleanup() -> None:
        raise ValueError("cleanup error suppressed")

    scope.on_cleanup(sync_cleanup)
    scope.on_cleanup(async_cleanup)
    scope.on_cleanup(failing_cleanup)

    await scope.aclose()

    assert cancelled
    assert async_cleanup_ran
    assert sync_cleanup_ran
    assert len(scope._tasks) == 0
    assert len(scope._cleanups) == 0
