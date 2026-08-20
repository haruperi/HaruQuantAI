"""Unit tests for asynchronous effect scope adapter.

Traces to: P5-T04, Gate G5
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import pytest
from app.kernel.async_effects import AsyncEffectScopeAdapter
from app.kernel.effects import EffectScope
from app.kernel.errors import LifecycleError


def test_cannot_adapt_closed_sync_scope() -> None:
    """Verify attempting to adapt an already closed sync scope raises LifecycleError."""
    sync_scope = EffectScope()
    sync_scope.close()

    with pytest.raises(LifecycleError, match="cannot adapt a closed effect scope"):
        AsyncEffectScopeAdapter(sync_scope)


@pytest.mark.anyio
async def test_async_then_sync_cleanup_order() -> None:
    """Verify async context managers unwind before synchronous callbacks execute."""
    events: list[str] = []

    @asynccontextmanager
    async def _async_cm() -> AsyncGenerator[str]:
        events.append("enter_async")
        try:
            yield "async_val"
        finally:
            events.append("exit_async")

    sync_scope = EffectScope()
    adapter = AsyncEffectScopeAdapter(sync_scope)

    val = await adapter.enter_async_context(_async_cm())
    adapter.callback(lambda: events.append("sync_disposer"))

    assert val == "async_val"
    assert events == ["enter_async"]

    await adapter.aclose()
    assert events == ["enter_async", "exit_async", "sync_disposer"]
    assert adapter.closed is True
    assert sync_scope.closed is True


@pytest.mark.anyio
async def test_async_double_close_is_idempotent() -> None:
    """Verify calling aclose twice is completely safe and executes disposers once."""
    calls: list[int] = []
    sync_scope = EffectScope()
    adapter = AsyncEffectScopeAdapter(sync_scope)
    adapter.callback(lambda: calls.append(1))

    await adapter.aclose()
    assert calls == [1]
    await adapter.aclose()
    assert calls == [1]


@pytest.mark.anyio
async def test_async_and_sync_failures_aggregated() -> None:
    """Verify both async exit failures and sync disposer failures are aggregated."""

    @asynccontextmanager
    async def _failing_async_cm() -> AsyncGenerator[None]:
        try:
            yield
        finally:
            raise RuntimeError("async_failure")

    sync_scope = EffectScope()
    adapter = AsyncEffectScopeAdapter(sync_scope)

    await adapter.enter_async_context(_failing_async_cm())
    adapter.callback(lambda: (_ for _ in ()).throw(ValueError("sync_failure")))

    with pytest.raises(
        LifecycleError, match="async effect scope cleanup failed: 2 failure\\(s\\)"
    ) as exc_info:
        await adapter.aclose()

    assert len(exc_info.value.failures) == 2  # type: ignore[attr-defined]
    assert isinstance(exc_info.value.failures[0], RuntimeError)  # type: ignore[attr-defined]
    assert isinstance(exc_info.value.failures[1], ValueError)  # type: ignore[attr-defined]


@pytest.mark.anyio
async def test_genuine_coroutine_resource_no_runtime_warnings() -> None:
    """Verify async adapter executes with genuine coroutines and emits zero runtime warnings."""
    cleaned_up = False

    @asynccontextmanager
    async def _real_async_resource() -> AsyncGenerator[dict[str, str]]:
        nonlocal cleaned_up
        state = {"status": "open"}
        try:
            yield state
        finally:
            state["status"] = "closed"
            cleaned_up = True

    sync_scope = EffectScope()
    adapter = AsyncEffectScopeAdapter(sync_scope)
    res = await adapter.enter_async_context(_real_async_resource())
    assert res["status"] == "open"

    await adapter.aclose()
    assert res["status"] == "closed"
    assert cleaned_up is True
