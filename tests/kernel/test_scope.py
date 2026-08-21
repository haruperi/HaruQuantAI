"""Tests for temporal scopes and reversible effect lifecycles."""

import asyncio
from contextlib import asynccontextmanager, contextmanager
from typing import Any

import pytest

from app.kernel.scope import EffectType, FeatureScope, cancel_and_wait


@pytest.mark.asyncio
async def test_scope_sync_callback_reverse_order() -> None:
    """Test that synchronous callbacks execute in reverse registration order."""
    scope = FeatureScope(owner_id="FEAT-TEST-RUN_CALLBACK")
    order: list[str] = []

    scope.callback(lambda: order.append("first"), name="cb1")
    scope.callback(lambda: order.append("second"), name="cb2")
    scope.callback(lambda: order.append("third"), name="cb3")

    assert not scope.is_closed
    await scope.close()

    assert scope.is_closed
    assert order == ["third", "second", "first"]

    # Idempotent close
    await scope.close()
    assert order == ["third", "second", "first"]


@pytest.mark.asyncio
async def test_scope_async_callback() -> None:
    """Test asynchronous callback execution and effect status."""
    scope = FeatureScope(owner_id="FEAT-TEST-RUN_ASYNC")
    cleaned: list[str] = []

    async def async_cleanup(name: str) -> None:
        await asyncio.sleep(0.01)
        cleaned.append(name)

    scope.async_callback(async_cleanup, "async_resource", name="async_cleaner")
    assert len(scope.effects) == 1
    assert not scope.effects[0].cleaned_up

    await scope.close()

    assert cleaned == ["async_resource"]
    assert scope.effects[0].cleaned_up


@pytest.mark.asyncio
async def test_scope_spawn_task_cancellation() -> None:
    """Test background task spawned in scope is cancelled and awaited on close."""
    scope = FeatureScope(owner_id="FEAT-TASK-RUN_BACKGROUND")
    cancelled = False

    async def background_worker() -> None:
        nonlocal cancelled
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled = True
            raise

    task = scope.spawn(background_worker(), name="worker")
    assert not task.done()

    await asyncio.sleep(0.02)
    assert not task.done()

    await scope.close()

    assert task.done()
    assert task.cancelled()
    assert cancelled
    assert scope.effects[0].cleaned_up


@pytest.mark.asyncio
async def test_scope_context_managers() -> None:
    """Test sync and async context managers entered in scope exit on close."""
    scope = FeatureScope(owner_id="FEAT-TEST-ENTER_CONTEXT")
    exited_sync = False
    exited_async = False

    @contextmanager
    def sync_resource() -> Any:
        try:
            yield "sync_val"
        finally:
            nonlocal exited_sync
            exited_sync = True

    @asynccontextmanager
    async def async_resource() -> Any:
        try:
            yield "async_val"
        finally:
            nonlocal exited_async
            exited_async = True

    val1 = scope.enter_context(sync_resource(), name="sync_res")
    val2 = await scope.enter_async_context(async_resource(), name="async_res")

    assert val1 == "sync_val"
    assert val2 == "async_val"
    assert not exited_sync
    assert not exited_async

    await scope.close()

    assert exited_sync
    assert exited_async


@pytest.mark.asyncio
async def test_scope_effect_records_metadata() -> None:
    """Test effect records contain correct diagnostic metadata."""
    scope = FeatureScope(owner_id="FEAT-TEST-TRACK_EFFECTS")
    scope.callback(lambda: None, name="meta_cb", effect_type=EffectType.SERVICE_BINDING)

    effects = scope.effects
    assert len(effects) == 1
    record = effects[0]
    assert record.owner_id == "FEAT-TEST-TRACK_EFFECTS"
    assert record.effect_type == EffectType.SERVICE_BINDING
    assert record.resource_name == "meta_cb"
    assert not record.cleaned_up

    await scope.close()
    assert record.cleaned_up


@pytest.mark.asyncio
async def test_cancel_and_wait_done_task() -> None:
    """Test cancel_and_wait handles already completed tasks gracefully."""

    async def done_coro() -> str:
        return "finished"

    task = asyncio.create_task(done_coro())
    await task
    await cancel_and_wait(task)
    assert task.done()


@pytest.mark.asyncio
async def test_scope_sync_callback_error_recording() -> None:
    """Test sync callback exception is captured in effect record."""
    scope = FeatureScope(owner_id="FEAT-TEST-FAIL_SYNC")

    def failing_cleanup() -> None:
        msg = "Cleanup failed"
        raise RuntimeError(msg)

    scope.callback(failing_cleanup, name="fail_cb")
    with pytest.raises(RuntimeError, match="Cleanup failed"):
        await scope.close()

    assert scope.effects[0].cleaned_up
    assert scope.effects[0].last_error == "Cleanup failed"


@pytest.mark.asyncio
async def test_scope_async_callback_error_recording() -> None:
    """Test async callback exception is captured in effect record."""
    scope = FeatureScope(owner_id="FEAT-TEST-FAIL_ASYNC")

    async def failing_async_cleanup() -> None:
        msg = "Async cleanup failed"
        raise RuntimeError(msg)

    scope.async_callback(failing_async_cleanup, name="fail_async_cb")
    with pytest.raises(RuntimeError, match="Async cleanup failed"):
        await scope.close()

    assert scope.effects[0].cleaned_up
    assert scope.effects[0].last_error == "Async cleanup failed"


@pytest.mark.asyncio
async def test_scope_registration_on_closed_scope_raises_error() -> None:
    """Characterization test: registering effects on a closed scope must raise an explicit error."""
    scope = FeatureScope(owner_id="FEAT-TEST-CLOSED_SCOPE")
    await scope.close()
    with pytest.raises((RuntimeError, ValueError), match=r"(?i)closed|scope"):
        scope.callback(lambda: None, name="late_callback")

    async def dummy_async_cb() -> None:
        pass

    with pytest.raises((RuntimeError, ValueError), match=r"(?i)closed|scope"):
        scope.async_callback(dummy_async_cb, name="late_async_cb")

    async def dummy() -> None:
        pass

    d_coro = dummy()
    with pytest.raises((RuntimeError, ValueError), match=r"(?i)closed|scope"):
        scope.spawn(d_coro, name="late_task")
    d_coro.close()

    @contextmanager
    def sync_cm() -> Any:
        yield

    @asynccontextmanager
    async def async_cm() -> Any:
        yield

    with pytest.raises((RuntimeError, ValueError), match=r"(?i)closed|scope"):
        scope.enter_context(sync_cm(), name="late_sync_cm")

    with pytest.raises((RuntimeError, ValueError), match=r"(?i)closed|scope"):
        await scope.enter_async_context(async_cm(), name="late_async_cm")
