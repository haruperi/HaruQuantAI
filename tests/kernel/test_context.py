"""Behavioral evidence for restricted feature scopes."""

import asyncio
import inspect
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager

import pytest
from app.kernel.capability import Capability, CapabilityUnavailableError
from app.kernel.context import FeatureContext, KernelDiagnostic
from app.kernel.feature import FeatureSpec

INPUT = Capability[str]("test.input")
OUTPUT = Capability[str]("test.output")


def test_context_exposes_no_ambient_lookup_or_observation() -> None:
    context = FeatureContext(FeatureSpec("restricted"), {})

    for forbidden in (
        "available_capabilities",
        "has",
        "get",
        "optional",
        "subscribe",
        "publish",
    ):
        assert not hasattr(context, forbidden)


def test_require_is_limited_to_declared_dependencies() -> None:
    context = FeatureContext(
        FeatureSpec("consumer", requires=frozenset({INPUT})), {INPUT: "value"}
    )
    assert context.require(INPUT) == "value"

    with pytest.raises(ValueError, match="Undeclared dependency"):
        context.require(OUTPUT)
    missing = FeatureContext(FeatureSpec("consumer", requires=frozenset({INPUT})), {})
    with pytest.raises(CapabilityUnavailableError) as captured:
        missing.require(INPUT)
    assert captured.value.blocked_by == "consumer"


def test_exports_are_exact_and_committed_once() -> None:
    context = FeatureContext(FeatureSpec("provider", provides=frozenset({OUTPUT})), {})
    with pytest.raises(ValueError, match="undeclared"):
        context.provide(INPUT, "wrong")
    with pytest.raises(ValueError, match="exact export"):
        context.commit_exports()

    context.provide(OUTPUT, "result")
    with pytest.raises(ValueError, match="duplicate"):
        context.provide(OUTPUT, "again")
    assert context.staged_capabilities == frozenset({OUTPUT})
    assert context.commit_exports() == {OUTPUT: "result"}
    with pytest.raises(ValueError, match="exact export"):
        context.commit_exports()


def test_owned_resources_and_callbacks_close_in_reverse_order() -> None:
    async def scenario() -> None:
        events: list[str] = []
        context = FeatureContext(FeatureSpec("owner"), {})

        @contextmanager
        def sync_resource() -> Iterator[str]:
            events.append("sync-enter")
            try:
                yield "sync"
            finally:
                events.append("sync-exit")

        @asynccontextmanager
        async def async_resource() -> AsyncIterator[str]:
            events.append("async-enter")
            try:
                yield "async"
            finally:
                events.append("async-exit")

        assert context.enter_context(sync_resource()) == "sync"
        assert await context.enter(async_resource()) == "async"
        context.on_close(lambda: events.append("callback"))
        await context.close()
        await context.close()
        assert events == [
            "sync-enter",
            "async-enter",
            "callback",
            "async-exit",
            "sync-exit",
        ]

    asyncio.run(scenario())


def test_cleanup_aggregates_independent_failures_and_diagnoses_them() -> None:
    async def scenario() -> None:
        diagnostics: list[KernelDiagnostic] = []
        context = FeatureContext(
            FeatureSpec("owner"), {}, diagnostic_sink=diagnostics.append
        )

        def fail_value() -> None:
            raise ValueError("first")

        async def fail_runtime() -> None:
            raise RuntimeError("second")

        context.on_close(fail_value)
        context.on_close(fail_runtime)
        with pytest.raises(BaseExceptionGroup) as captured:
            await context.close()
        assert {type(error) for error in captured.value.exceptions} == {
            ValueError,
            RuntimeError,
        }
        assert len(diagnostics) == 2

    asyncio.run(scenario())


def test_managed_tasks_are_cancelled_and_task_failures_surface() -> None:
    async def scenario() -> None:
        context = FeatureContext(FeatureSpec("tasks"), {})
        started = asyncio.Event()

        async def waiting() -> None:
            started.set()
            await asyncio.Event().wait()

        task = context.spawn(waiting(), name="waiting")
        await started.wait()
        await context.close()
        assert task.cancelled()

        failing = FeatureContext(FeatureSpec("failing-task"), {})

        async def fail() -> None:
            raise KeyError("failed")

        failed_task = failing.spawn(fail())
        await asyncio.wait({failed_task})
        with pytest.raises(BaseExceptionGroup) as captured:
            await failing.close()
        assert isinstance(captured.value.exceptions[0], KeyError)

    asyncio.run(scenario())


def test_closed_context_rejects_operations_and_closes_rejected_coroutine() -> None:
    async def scenario() -> None:
        context = FeatureContext(
            FeatureSpec(
                "closed", provides=frozenset({OUTPUT}), requires=frozenset({INPUT})
            ),
            {INPUT: "value"},
        )
        await context.close()
        with pytest.raises(RuntimeError, match="is closed"):
            context.require(INPUT)
        with pytest.raises(RuntimeError, match="is closed"):
            context.provide(OUTPUT, "value")
        with pytest.raises(RuntimeError, match="is closed"):
            context.commit_exports()
        with pytest.raises(RuntimeError, match="is closed"):
            context.on_close(lambda: None)

        async def unused() -> None:
            return None

        coroutine = unused()
        with pytest.raises(RuntimeError, match="is closed"):
            context.spawn(coroutine)
        assert inspect.getcoroutinestate(coroutine) == inspect.CORO_CLOSED

    asyncio.run(scenario())


def test_diagnostic_sink_failure_never_changes_cleanup_result() -> None:
    async def scenario() -> None:
        def broken_sink(_diagnostic: KernelDiagnostic) -> None:
            raise RuntimeError("observer")

        context = FeatureContext(FeatureSpec("owner"), {}, diagnostic_sink=broken_sink)
        context.on_close(lambda: (_ for _ in ()).throw(ValueError("cleanup")))
        with pytest.raises(BaseExceptionGroup) as captured:
            await context.close()
        assert isinstance(captured.value.exceptions[0], ValueError)

    asyncio.run(scenario())
