# cspell:words awaitables awaitable unregisters
"""Comprehensive unit tests for FeatureContext."""

import asyncio
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager

import pytest
from app.kernel.capability import Capability, CapabilityUnavailableError
from app.kernel.context import FeatureContext
from app.kernel.events import EventBus
from app.kernel.feature import FeatureSpec

CAP_A = Capability[str]("service.a")
CAP_B = Capability[int]("service.b")
CAP_OPT = Capability[str]("service.opt")
CAP_OUT = Capability[str]("service.out")


def test_context_properties_and_introspection() -> None:
    """Verify spec, is_open, has, and capability property helpers."""
    spec = FeatureSpec(
        name="test_feature",
        provides=frozenset({CAP_OUT}),
        requires=frozenset({CAP_A}),
        optional=frozenset({CAP_OPT}),
    )
    bus = EventBus()
    ctx = FeatureContext(spec, {CAP_A: "hello"}, bus)

    assert ctx.spec is spec
    assert ctx.is_open is True
    assert ctx.has(CAP_A) is True
    assert ctx.has(CAP_OPT) is False
    assert ctx.available_capabilities == frozenset({CAP_A})
    assert ctx.staged_capabilities == frozenset()

    ctx.provide(CAP_OUT, "export")
    assert ctx.staged_capabilities == frozenset({CAP_OUT})


def test_require_and_optional_lookups() -> None:
    """Verify strict declaration checks and default fallback behavior."""
    spec = FeatureSpec(
        name="test_feature",
        requires=frozenset({CAP_A, CAP_B}),
        optional=frozenset({CAP_OPT}),
    )
    bus = EventBus()
    ctx = FeatureContext(spec, {CAP_A: "service_a"}, bus)

    # 1. Successful require
    assert ctx.require(CAP_A) == "service_a"

    # 2. Missing required capability
    with pytest.raises(CapabilityUnavailableError) as exc_info:
        ctx.require(CAP_B)
    assert exc_info.value.capability == "test_feature: service.b"

    # 3. Undeclared require
    undeclared = Capability[str]("service.undeclared")
    with pytest.raises(ValueError, match="Undeclared dependency"):
        ctx.require(undeclared)

    # 4. Optional missing returns default
    assert ctx.optional(CAP_OPT) is None
    assert ctx.optional(CAP_OPT, default="custom_default") == "custom_default"

    # 5. Optional present returns service
    ctx_with_opt = FeatureContext(spec, {CAP_OPT: "present"}, bus)
    assert ctx_with_opt.optional(CAP_OPT) == "present"

    # 6. Undeclared optional
    with pytest.raises(ValueError, match="Undeclared optional dependency"):
        ctx.optional(undeclared)


def test_provide_and_commit_exports() -> None:
    """Verify export staging and commit validation rules."""
    spec = FeatureSpec(
        name="test_feature",
        provides=frozenset({CAP_OUT}),
    )
    bus = EventBus()
    ctx = FeatureContext(spec, {}, bus)

    # Undeclared export
    with pytest.raises(ValueError, match="Export is undeclared"):
        ctx.provide(CAP_A, "not_in_provides")

    # Staging valid export
    ctx.provide(CAP_OUT, "service_out")

    # Duplicate staging
    with pytest.raises(ValueError, match="Export is undeclared, duplicate"):
        ctx.provide(CAP_OUT, "duplicate")

    # Commit successfully
    exports = ctx.commit_exports()
    assert exports == {CAP_OUT: "service_out"}

    # Second commit disallowed
    with pytest.raises(ValueError, match="Feature did not stage"):
        ctx.commit_exports()

    # Provide after commit disallowed
    with pytest.raises(ValueError, match="Export is undeclared"):
        ctx.provide(CAP_OUT, "after_commit")


def test_commit_incomplete_exports_raises() -> None:
    """Verify commit fails if not all declared exports are staged."""
    spec = FeatureSpec(
        name="test_feature",
        provides=frozenset({CAP_A, CAP_OUT}),
    )
    bus = EventBus()
    ctx = FeatureContext(spec, {}, bus)
    ctx.provide(CAP_A, "only_one")

    with pytest.raises(ValueError, match="Feature did not stage"):
        ctx.commit_exports()


def test_sync_and_async_on_close_callbacks() -> None:
    """Verify both sync and async cleanup callbacks execute in LIFO order."""

    async def scenario() -> None:
        spec = FeatureSpec(name="cleanup_feature")
        bus = EventBus()
        ctx = FeatureContext(spec, {}, bus)
        events: list[str] = []

        def sync_cleanup() -> None:
            events.append("sync_cleanup")

        async def async_cleanup() -> None:
            await asyncio.sleep(0.001)
            events.append("async_cleanup")

        ctx.on_close(sync_cleanup)
        ctx.on_close(async_cleanup)

        await ctx.close()
        # LIFO: async_cleanup (registered 2nd) runs before sync_cleanup (registered 1st)
        assert events == ["async_cleanup", "sync_cleanup"]
        assert ctx.is_open is False

    asyncio.run(scenario())


def test_enter_sync_and_async_context_managers() -> None:
    """Verify enter_context and enter manage resource lifecycles."""

    async def scenario() -> None:
        spec = FeatureSpec(name="context_feature")
        bus = EventBus()
        ctx = FeatureContext(spec, {}, bus)
        events: list[str] = []

        @contextmanager
        def sync_resource() -> Iterator[str]:
            events.append("sync_enter")
            try:
                yield "sync_val"
            finally:
                events.append("sync_exit")

        @asynccontextmanager
        async def async_resource() -> AsyncIterator[str]:
            events.append("async_enter")
            try:
                yield "async_val"
            finally:
                events.append("async_exit")

        val1 = ctx.enter_context(sync_resource())
        assert val1 == "sync_val"

        val2 = await ctx.enter(async_resource())
        assert val2 == "async_val"

        assert events == ["sync_enter", "async_enter"]
        await ctx.close()
        # LIFO: async_exit runs before sync_exit
        assert events == ["sync_enter", "async_enter", "async_exit", "sync_exit"]

    asyncio.run(scenario())


def test_context_manager_exit_errors_captured() -> None:
    """Verify exceptions during context exit are accumulated into exception group."""

    async def scenario() -> None:
        spec = FeatureSpec(name="error_feature")
        bus = EventBus()
        ctx = FeatureContext(spec, {}, bus)

        @contextmanager
        def failing_sync() -> Iterator[None]:
            yield
            raise ValueError("sync exit failure")

        @asynccontextmanager
        async def failing_async() -> AsyncIterator[None]:
            yield
            raise RuntimeError("async exit failure")

        ctx.enter_context(failing_sync())
        await ctx.enter(failing_async())

        with pytest.raises(BaseExceptionGroup) as exc_info:
            await ctx.close()

        errors = exc_info.value.exceptions
        assert len(errors) == 2
        assert any(isinstance(e, RuntimeError) for e in errors)
        assert any(isinstance(e, ValueError) for e in errors)

    asyncio.run(scenario())


def test_spawn_task_lifecycle_and_error_capture() -> None:
    """Verify task spawning, naming, cancellation, and error capture."""

    async def scenario() -> None:
        spec = FeatureSpec(name="task_feature")
        bus = EventBus()
        ctx = FeatureContext(spec, {}, bus)
        started = asyncio.Event()

        async def worker() -> None:
            started.set()
            await asyncio.sleep(10)

        task = ctx.spawn(worker(), name="my_worker")
        assert task.get_name() == "my_worker"

        await started.wait()
        await ctx.close()
        assert task.cancelled()

    asyncio.run(scenario())


def test_spawn_task_exception_captured_on_close() -> None:
    """Verify that a crashed background task is surfaced during close."""

    async def scenario() -> None:
        spec = FeatureSpec(name="crash_feature")
        bus = EventBus()
        ctx = FeatureContext(spec, {}, bus)

        async def failing_task() -> None:
            raise KeyError("task died")

        task = ctx.spawn(failing_task())
        await asyncio.wait({task})

        with pytest.raises(BaseExceptionGroup) as exc_info:
            await ctx.close()

        assert any(isinstance(e, KeyError) for e in exc_info.value.exceptions)

    asyncio.run(scenario())


def test_subscribe_and_publish_with_auto_cleanup() -> None:
    """Verify event subscription is automatically cleaned up when context closes."""

    async def scenario() -> None:
        spec = FeatureSpec(name="pubsub_feature")
        bus = EventBus()
        ctx = FeatureContext(spec, {}, bus)
        received: list[str] = []

        ctx.subscribe(str, received.append)
        await ctx.publish("message_1")
        assert received == ["message_1"]

        await ctx.close()

        # Publishing on bus after ctx.close() should NOT deliver to ctx's subscriber
        await bus.publish("message_2")
        assert received == ["message_1"]

    asyncio.run(scenario())


def test_operations_on_closed_context_raise_runtime_error() -> None:
    """Verify that every operation on a closed context raises RuntimeError."""

    async def scenario() -> None:
        spec = FeatureSpec(
            name="closed_feature",
            provides=frozenset({CAP_OUT}),
            requires=frozenset({CAP_A}),
            optional=frozenset({CAP_OPT}),
        )
        bus = EventBus()
        ctx = FeatureContext(spec, {CAP_A: "val"}, bus)
        await ctx.close()

        with pytest.raises(RuntimeError, match="is closed"):
            ctx.require(CAP_A)

        with pytest.raises(RuntimeError, match="is closed"):
            ctx.optional(CAP_OPT)

        with pytest.raises(RuntimeError, match="is closed"):
            ctx.provide(CAP_OUT, "val")

        with pytest.raises(RuntimeError, match="is closed"):
            ctx.commit_exports()

        with pytest.raises(RuntimeError, match="is closed"):
            ctx.on_close(lambda: None)

        with pytest.raises(RuntimeError, match="is closed"):
            ctx.enter_context(contextmanager(lambda: iter([""]))())

        @asynccontextmanager
        async def dummy() -> AsyncIterator[str]:
            yield ""

        with pytest.raises(RuntimeError, match="is closed"):
            await ctx.enter(dummy())

        async def coroutine() -> None:
            pass

        with pytest.raises(RuntimeError, match="is closed"):
            ctx.spawn(coroutine())

        with pytest.raises(RuntimeError, match="is closed"):
            ctx.subscribe(str, lambda _: None)

        with pytest.raises(RuntimeError, match="is closed"):
            await ctx.publish("event")

    asyncio.run(scenario())
