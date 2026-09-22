"""Behavioral evidence for graph validation and transactional lifecycle."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import pytest
from app.kernel.bootstrapper import Runtime
from app.kernel.capability import Capability, CapabilityUnavailableError
from app.kernel.context import FeatureContext, KernelDiagnostic
from app.kernel.feature import FeatureSpec

VALUE = Capability[int]("test.value")
RESULT = Capability[str]("test.result")


@dataclass(slots=True)
class FixtureFeature:
    spec: FeatureSpec
    action: Callable[[FeatureContext], Awaitable[None]]

    async def start(self, context: FeatureContext) -> None:
        await self.action(context)


def factory(
    spec: FeatureSpec, action: Callable[[FeatureContext], Awaitable[None]]
) -> Callable[[], FixtureFeature]:
    return lambda: FixtureFeature(spec, action)


async def noop(_context: FeatureContext) -> None:
    return None


def test_canonical_startup_and_reverse_dependency_cleanup() -> None:
    async def scenario() -> None:
        history: list[str] = []
        provider_closed = False

        async def provider(context: FeatureContext) -> None:
            def close_provider() -> None:
                nonlocal provider_closed
                provider_closed = True
                history.append("close-provider")

            context.on_close(close_provider)
            context.provide(VALUE, 7)
            history.append("start-provider")

        async def consumer(context: FeatureContext) -> None:
            assert context.require(VALUE) == 7

            def close_consumer() -> None:
                assert not provider_closed
                history.append("close-consumer")

            context.on_close(close_consumer)
            context.provide(RESULT, "ok")
            history.append("start-consumer")

        async def alpha(context: FeatureContext) -> None:
            history.append("start-alpha")

        runtime = Runtime(
            (
                factory(
                    FeatureSpec(
                        "consumer",
                        provides=frozenset({RESULT}),
                        requires=frozenset({VALUE}),
                    ),
                    consumer,
                ),
                factory(FeatureSpec("provider", provides=frozenset({VALUE})), provider),
                factory(FeatureSpec("alpha"), alpha),
            )
        )
        async with runtime:
            assert runtime.active_features == ("alpha", "provider", "consumer")
            assert runtime.require(RESULT) == "ok"
        assert history == [
            "start-alpha",
            "start-provider",
            "start-consumer",
            "close-consumer",
            "close-provider",
        ]
        with pytest.raises(CapabilityUnavailableError):
            runtime.require(RESULT)

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "case", ["duplicate-name", "duplicate-provider", "missing", "cycle"]
)
def test_invalid_graphs_fail_before_any_start(case: str) -> None:
    async def scenario() -> None:
        starts = 0
        factories: tuple[Callable[[], FixtureFeature], ...]

        async def started(context: FeatureContext) -> None:
            nonlocal starts
            starts += 1
            if VALUE in context.staged_capabilities:
                return

        if case == "duplicate-name":
            factories = (
                factory(FeatureSpec("same"), started),
                factory(FeatureSpec("same"), started),
            )
        elif case == "duplicate-provider":
            factories = (
                factory(FeatureSpec("a", provides=frozenset({VALUE})), started),
                factory(FeatureSpec("b", provides=frozenset({VALUE})), started),
            )
        elif case == "missing":
            factories = (
                factory(FeatureSpec("a", requires=frozenset({VALUE})), started),
            )
        else:
            factories = (
                factory(
                    FeatureSpec(
                        "a",
                        provides=frozenset({VALUE}),
                        requires=frozenset({RESULT}),
                    ),
                    started,
                ),
                factory(
                    FeatureSpec(
                        "b",
                        provides=frozenset({RESULT}),
                        requires=frozenset({VALUE}),
                    ),
                    started,
                ),
            )
        with pytest.raises((ValueError, CapabilityUnavailableError)):
            async with Runtime(factories):
                pytest.fail("invalid graph started")
        assert starts == 0

    asyncio.run(scenario())


def test_failed_start_closes_current_and_prior_scopes() -> None:
    async def scenario() -> None:
        closed: list[str] = []

        async def first(context: FeatureContext) -> None:
            context.on_close(lambda: closed.append("first"))
            context.provide(VALUE, 1)

        async def second(context: FeatureContext) -> None:
            context.on_close(lambda: closed.append("second"))
            raise RuntimeError("startup")

        runtime = Runtime(
            (
                factory(FeatureSpec("first", provides=frozenset({VALUE})), first),
                factory(FeatureSpec("second", requires=frozenset({VALUE})), second),
            )
        )
        with pytest.raises(RuntimeError, match="startup"):
            async with runtime:
                pytest.fail("startup should fail")
        assert closed == ["second", "first"]
        assert runtime.active_features == ()

    asyncio.run(scenario())


def test_cancelled_start_unwinds_acquired_scope() -> None:
    async def scenario() -> None:
        started = asyncio.Event()
        closed: list[str] = []

        async def blocking(context: FeatureContext) -> None:
            context.on_close(lambda: closed.append("closed"))
            started.set()
            await asyncio.Event().wait()

        async def run() -> None:
            async with Runtime((factory(FeatureSpec("blocking"), blocking),)):
                pytest.fail("startup cannot finish")

        task = asyncio.create_task(run())
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert closed == ["closed"]

    asyncio.run(scenario())


def test_cleanup_failures_are_aggregated_without_skipping_scopes() -> None:
    async def scenario() -> None:
        closed: list[str] = []

        def fail(name: str) -> None:
            closed.append(name)
            raise RuntimeError(name)

        async def first(context: FeatureContext) -> None:
            context.on_close(lambda: fail("first"))

        async def second(context: FeatureContext) -> None:
            context.on_close(lambda: fail("second"))

        runtime = Runtime(
            (
                factory(FeatureSpec("first"), first),
                factory(FeatureSpec("second"), second),
            )
        )
        with pytest.raises(BaseExceptionGroup) as captured:
            async with runtime:
                pass
        assert closed == ["second", "first"]
        assert len(captured.value.exceptions) == 2
        await runtime.close()

    asyncio.run(scenario())


def test_subset_validation_single_use_and_diagnostics() -> None:
    async def scenario() -> None:
        diagnostics: list[KernelDiagnostic] = []
        runtime = Runtime(
            (factory(FeatureSpec("alpha"), noop),),
            enabled=("alpha",),
            diagnostic_sink=diagnostics.append,
        )
        async with runtime:
            assert runtime.active_features == ("alpha",)
        with pytest.raises(RuntimeError, match="single-use"):
            async with runtime:
                pass

        with pytest.raises(ValueError, match="Unknown enabled"):
            async with Runtime(
                (factory(FeatureSpec("alpha"), noop),), enabled=("missing",)
            ):
                pass
        assert diagnostics == []

    asyncio.run(scenario())


def test_start_and_cleanup_failure_preserve_both_errors() -> None:
    async def scenario() -> None:
        async def broken(context: FeatureContext) -> None:
            context.on_close(lambda: (_ for _ in ()).throw(ValueError("cleanup")))
            raise RuntimeError("startup")

        with pytest.raises(BaseExceptionGroup) as captured:
            async with Runtime((factory(FeatureSpec("broken"), broken),)):
                pass
        assert isinstance(captured.value.exceptions[0], RuntimeError)
        assert isinstance(captured.value.exceptions[1], BaseExceptionGroup)

    asyncio.run(scenario())
