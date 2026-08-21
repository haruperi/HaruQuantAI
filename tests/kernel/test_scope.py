"""Tests for temporal scopes and reversible effect lifecycles."""

import asyncio
from contextlib import asynccontextmanager, contextmanager
from typing import Any

import pytest

from app.kernel.scope import EffectType, FeatureScope, cancel_and_wait


@pytest.mark.asyncio
async def test_scope_sync_callback_reverse_order() -> None:
    scope = FeatureScope(owner_id="FEAT-TEST-RUN_CALLBACK")
    order: list[str] = []
    scope.callback(lambda: order.append("first"), name="cb1")
    scope.callback(lambda: order.append("second"), name="cb2")
    scope.callback(lambda: order.append("third"), name="cb3")
    await scope.close()
    assert order == ["third", "second", "first"]
    await scope.close()
    assert order == ["third", "second", "first"]


@pytest.mark.asyncio
async def test_scope_async_callback() -> None:
    scope = FeatureScope(owner_id="FEAT-TEST-RUN_ASYNC")
    cleaned: list[str] = []

    async def async_cleanup(name: str) -> None:
        await asyncio.sleep(0.01)
        cleaned.append(name)

    scope.async_callback(async_cleanup, "resource", name="async_cleaner")
    await scope.close()
    assert cleaned == ["resource"]
    assert scope.effects[0].cleaned_up


@pytest.mark.asyncio
async def test_scope_spawn_task_cancellation() -> None:
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
    await asyncio.sleep(0.02)
    await scope.close()
    assert task.cancelled()
    assert cancelled
    assert scope.effects[0].cleaned_up


@pytest.mark.asyncio
async def test_scope_reports_unexpected_task_failure() -> None:
    failures: list[tuple[str, str]] = []

    async def on_failure(owner_id: str, error: BaseException) -> None:
        failures.append((owner_id, str(error)))

    scope = FeatureScope(
        owner_id="FEAT-TEST-CRASH",
        on_task_failure=on_failure,
    )

    async def crashing_worker() -> None:
        await asyncio.sleep(0)
        raise RuntimeError("worker crashed")

    task = scope.spawn(crashing_worker(), name="worker")
    with pytest.raises(RuntimeError, match="worker crashed"):
        await task
    await asyncio.sleep(0)
    assert failures == [("FEAT-TEST-CRASH", "worker crashed")]
    await scope.close()


@pytest.mark.asyncio
async def test_scope_rejects_late_effect_registration() -> None:
    scope = FeatureScope(owner_id="FEAT-TEST-CLOSED")
    await scope.close()
    with pytest.raises(RuntimeError, match="already closed"):
        scope.callback(lambda: None)
    with pytest.raises(RuntimeError, match="already closed"):
        scope.spawn(asyncio.sleep(0), name="late")


@pytest.mark.asyncio
async def test_scope_context_managers() -> None:
    scope = FeatureScope(owner_id="FEAT-TEST-ENTER_CONTEXT")
    exited_sync = False
    exited_async = False

    @contextmanager
    def sync_resource() -> Any:
        nonlocal exited_sync
        try:
            yield "sync_val"
        finally:
            exited_sync = True

    @asynccontextmanager
    async def async_resource() -> Any:
        nonlocal exited_async
        try:
            yield "async_val"
        finally:
            exited_async = True

    assert scope.enter_context(sync_resource(), name="sync_res") == "sync_val"
    assert await scope.enter_async_context(async_resource(), name="async_res") == "async_val"
    await scope.close()
    assert exited_sync
    assert exited_async


@pytest.mark.asyncio
async def test_scope_effect_records_metadata() -> None:
    scope = FeatureScope(owner_id="FEAT-TEST-TRACK_EFFECTS")
    scope.callback(lambda: None, name="meta_cb", effect_type=EffectType.SERVICE_BINDING)
    record = scope.effects[0]
    assert record.owner_id == "FEAT-TEST-TRACK_EFFECTS"
    assert record.effect_type == EffectType.SERVICE_BINDING
    assert not record.cleaned_up
    await scope.close()
    assert record.cleaned_up


@pytest.mark.asyncio
async def test_cancel_and_wait_done_task() -> None:
    async def done_coro() -> str:
        return "finished"

    task = asyncio.create_task(done_coro())
    await task
    await cancel_and_wait(task)
    assert task.done()


@pytest.mark.asyncio
async def test_cleanup_errors_are_recorded() -> None:
    scope = FeatureScope(owner_id="FEAT-TEST-FAIL_SYNC")

    def failing_cleanup() -> None:
        raise RuntimeError("Cleanup failed")

    scope.callback(failing_cleanup, name="fail_cb")
    with pytest.raises(RuntimeError, match="Cleanup failed"):
        await scope.close()
    assert scope.effects[0].cleaned_up
    assert scope.effects[0].last_error == "Cleanup failed"
