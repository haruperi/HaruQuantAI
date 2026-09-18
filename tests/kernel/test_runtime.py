"""Behavioral evidence for composition, boundaries, and lifecycle failures."""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass

import pytest
from app.kernel.bootstrapper import Runtime
from app.kernel.capability import Capability, CapabilityUnavailableError
from app.kernel.context import FeatureContext
from app.kernel.events import EventBus
from app.kernel.feature import Feature, FeatureSpec

VALUE = Capability[int]("example.value")
RESULT = Capability[str]("example.result")


@dataclass
class FixtureFeature:
    """Supply a test startup implementation with a real manifest."""

    spec: FeatureSpec
    action: Callable[[FeatureContext], Awaitable[None]]

    async def start(self, context: FeatureContext) -> None:
        """Delegate startup to the scenario."""
        await self.action(context)


def test_composition_order_exports_and_reverse_cleanup() -> None:
    async def scenario() -> None:
        history: list[str] = []

        async def provider(ctx: FeatureContext) -> None:
            history.append("provider")
            ctx.on_close(lambda: history.append("close provider"))
            ctx.provide(VALUE, 7)

        async def consumer(ctx: FeatureContext) -> None:
            history.append("consumer")
            ctx.on_close(lambda: history.append("close consumer"))
            ctx.provide(RESULT, str(ctx.require(VALUE)))

        runtime = Runtime(
            [
                lambda: FixtureFeature(
                    FeatureSpec("consumer", frozenset({RESULT}), frozenset({VALUE})),
                    consumer,
                ),
                lambda: FixtureFeature(
                    FeatureSpec("provider", frozenset({VALUE})), provider
                ),
            ]
        )
        async with runtime:
            assert runtime.require(RESULT) == "7"
            with pytest.raises(CapabilityUnavailableError):
                runtime.require(Capability[int]("absent"))
        assert history == ["provider", "consumer", "close consumer", "close provider"]
        await runtime.close()
        with pytest.raises(CapabilityUnavailableError):
            runtime.require(VALUE)
        with pytest.raises(RuntimeError, match="single-use"):
            await runtime.__aenter__()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "kind", ["duplicate_name", "duplicate_export", "missing", "cycle"]
)
def test_invalid_graph_never_starts_features(kind: str) -> None:
    async def scenario() -> None:
        started: list[bool] = []

        async def start(ctx: FeatureContext) -> None:
            started.append(True)

        first = FeatureSpec("a", frozenset({VALUE}))
        second = FeatureSpec("a")
        expected: type[Exception] = ValueError
        if kind == "duplicate_export":
            second = FeatureSpec("b", frozenset({VALUE}))
        elif kind == "missing":
            first = FeatureSpec("a", requires=frozenset({RESULT}))
            second = FeatureSpec("b")
            expected = CapabilityUnavailableError
        elif kind == "cycle":
            first = FeatureSpec("a", frozenset({VALUE}), frozenset({RESULT}))
            second = FeatureSpec("b", frozenset({RESULT}), frozenset({VALUE}))
        with pytest.raises(expected):
            async with Runtime(
                [
                    lambda: FixtureFeature(first, start),
                    lambda: FixtureFeature(second, start),
                ]
            ):
                pytest.fail("Invalid graph was admitted")
        assert not started

    asyncio.run(scenario())


@pytest.mark.parametrize("failure", ["raise", "incomplete", "cancel"])
def test_failed_start_unwinds_current_and_previous_scopes(failure: str) -> None:
    async def scenario() -> None:
        closed: list[str] = []

        async def good(ctx: FeatureContext) -> None:
            ctx.on_close(lambda: closed.append("good"))
            ctx.provide(VALUE, 1)

        async def bad(ctx: FeatureContext) -> None:
            ctx.on_close(lambda: closed.append("bad"))
            if failure == "raise":
                ctx.provide(RESULT, "staged")
                raise RuntimeError("startup failure")
            if failure == "cancel":
                raise asyncio.CancelledError

        expected = {
            "raise": RuntimeError,
            "incomplete": ValueError,
            "cancel": asyncio.CancelledError,
        }[failure]
        runtime = Runtime(
            [
                lambda: FixtureFeature(FeatureSpec("good", frozenset({VALUE})), good),
                lambda: FixtureFeature(
                    FeatureSpec("bad", frozenset({RESULT}), frozenset({VALUE})), bad
                ),
            ]
        )
        with pytest.raises(expected):
            await runtime.__aenter__()
        assert closed == ["bad", "good"]
        with pytest.raises(CapabilityUnavailableError):
            runtime.require(VALUE)

    asyncio.run(scenario())


def test_scope_boundaries_and_owned_resources() -> None:
    async def scenario() -> None:
        bus = EventBus()
        seen: list[str] = []
        ctx = FeatureContext(
            FeatureSpec("test", frozenset({VALUE}), frozenset({RESULT})), {}, bus
        )
        with pytest.raises(ValueError, match="Undeclared"):
            ctx.require(VALUE)
        with pytest.raises(CapabilityUnavailableError):
            ctx.require(RESULT)
        with pytest.raises(ValueError):
            ctx.provide(RESULT, "bad")
        ctx.provide(VALUE, 1)
        with pytest.raises(ValueError):
            ctx.provide(VALUE, 2)
        assert ctx.commit_exports() == {VALUE: 1}
        with pytest.raises(ValueError):
            ctx.commit_exports()
        ctx.subscribe(str, seen.append)
        await ctx.publish("observed")

        @asynccontextmanager
        async def resource() -> AsyncIterator[int]:
            try:
                yield 42
            finally:
                seen.append("resource closed")

        assert await ctx.enter(resource()) == 42
        started = asyncio.Event()

        async def worker() -> None:
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                seen.append("task closed")

        task = ctx.spawn(worker())
        await started.wait()
        await ctx.close()
        assert task.cancelled()
        await bus.publish("not delivered")
        assert seen == ["observed", "task closed", "resource closed"]
        await ctx.close()
        with pytest.raises(RuntimeError):
            ctx.require(RESULT)
        with pytest.raises(RuntimeError):
            ctx.spawn(worker())

    asyncio.run(scenario())


def test_cleanup_continues_after_callback_and_task_failures() -> None:
    async def scenario() -> None:
        closed: list[bool] = []
        ctx = FeatureContext(FeatureSpec("cleanup"), {}, EventBus())
        ctx.on_close(lambda: closed.append(True))

        def fail() -> None:
            raise ValueError("cleanup failed")

        ctx.on_close(fail)

        async def broken() -> None:
            raise RuntimeError("worker failed")

        task = ctx.spawn(broken())
        await asyncio.wait({task})
        with pytest.raises(ExceptionGroup, match="Feature cleanup failed") as caught:
            await ctx.close()
        assert [type(error) for error in caught.value.exceptions] == [
            RuntimeError,
            ValueError,
        ]
        assert closed == [True]

    asyncio.run(scenario())


def test_event_handlers_await_futures_and_dispose_independently() -> None:
    async def scenario() -> None:
        bus = EventBus()
        seen: list[str] = []
        first = bus.subscribe(str, seen.append)
        second = bus.subscribe(str, seen.append)
        first()
        first()
        await bus.publish("one")
        assert seen == ["one"]
        second()
        future = asyncio.get_running_loop().create_future()
        future.set_result(None)

        def handler(event: int) -> Awaitable[None]:
            return future

        bus.subscribe(int, handler)
        await bus.publish(1)

    asyncio.run(scenario())


def test_identity_and_manifest_validation() -> None:
    assert VALUE == Capability[int]("example.value")
    assert VALUE != Capability[int]("example.value", 2)
    for name, version in [("", 1), ("valid", 0)]:
        with pytest.raises(ValueError):
            Capability[int](name, version)
    with pytest.raises(ValueError):
        FeatureSpec("")
    with pytest.raises(ValueError):
        FeatureSpec("self", frozenset({VALUE}), frozenset({VALUE}))


@pytest.mark.parametrize("failure_phase", ["startup", "body", "shutdown"])
def test_runtime_retains_all_failures_across_scopes(failure_phase: str) -> None:
    async def scenario() -> None:
        closed: list[str] = []

        def fail_cleanup(name: str) -> None:
            closed.append(name)
            raise ValueError(name)

        async def first(ctx: FeatureContext) -> None:
            ctx.on_close(lambda: fail_cleanup("first"))

        async def second(ctx: FeatureContext) -> None:
            ctx.on_close(lambda: fail_cleanup("second"))
            if failure_phase == "startup":
                raise RuntimeError("startup")

        runtime = Runtime(
            [
                lambda: FixtureFeature(FeatureSpec("first"), first),
                lambda: FixtureFeature(FeatureSpec("second"), second),
            ]
        )
        with pytest.raises(BaseExceptionGroup) as caught:
            async with runtime:
                if failure_phase == "body":
                    raise RuntimeError("body")

        def leaves(error: BaseException) -> list[str]:
            if isinstance(error, BaseExceptionGroup):
                return [
                    message for child in error.exceptions for message in leaves(child)
                ]
            return [str(error)]

        expected = ["second", "first"]
        if failure_phase != "shutdown":
            expected.insert(0, failure_phase)
        assert leaves(caught.value) == expected
        assert closed == ["second", "first"]
        await runtime.close()

    asyncio.run(scenario())


def test_optional_dependency_resolved_when_provider_present() -> None:
    async def scenario() -> None:
        optional_cap = Capability[int]("example.optional")
        observed: list[int | None] = []

        async def provider(ctx: FeatureContext) -> None:
            ctx.provide(optional_cap, 42)

        async def consumer(ctx: FeatureContext) -> None:
            observed.append(ctx.optional(optional_cap))
            ctx.provide(RESULT, "done")

        runtime = Runtime(
            [
                lambda: FixtureFeature(
                    FeatureSpec(
                        "consumer",
                        provides=frozenset({RESULT}),
                        optional=frozenset({optional_cap}),
                    ),
                    consumer,
                ),
                lambda: FixtureFeature(
                    FeatureSpec("provider", provides=frozenset({optional_cap})),
                    provider,
                ),
            ]
        )
        async with runtime:
            assert runtime.require(RESULT) == "done"
            assert observed == [42]

    asyncio.run(scenario())


def test_optional_dependency_returns_none_when_provider_absent() -> None:
    async def scenario() -> None:
        optional_cap = Capability[int]("example.optional")
        observed: list[int | None] = []

        async def consumer(ctx: FeatureContext) -> None:
            observed.append(ctx.optional(optional_cap))
            ctx.provide(RESULT, "done")

        runtime = Runtime(
            [
                lambda: FixtureFeature(
                    FeatureSpec(
                        "consumer",
                        provides=frozenset({RESULT}),
                        optional=frozenset({optional_cap}),
                    ),
                    consumer,
                ),
            ]
        )
        async with runtime:
            assert runtime.require(RESULT) == "done"
            assert observed == [None]

    asyncio.run(scenario())


def test_optional_dependency_undeclared_raises_value_error() -> None:
    async def scenario() -> None:
        optional_cap = Capability[int]("example.optional")
        ctx = FeatureContext(FeatureSpec("test"), {}, EventBus())
        with pytest.raises(ValueError, match="Undeclared optional dependency"):
            ctx.optional(optional_cap)

    asyncio.run(scenario())


def test_optional_dependency_avoids_cycle_with_required() -> None:
    async def scenario() -> None:
        observed_b_optional: list[int | None] = []
        observed_a_required: list[str] = []

        async def feature_a(ctx: FeatureContext) -> None:
            observed_a_required.append(ctx.require(RESULT))
            ctx.provide(VALUE, 99)

        async def feature_b(ctx: FeatureContext) -> None:
            observed_b_optional.append(ctx.optional(VALUE))
            ctx.provide(RESULT, "result_from_b")

        runtime = Runtime(
            [
                lambda: FixtureFeature(
                    FeatureSpec(
                        "feature_a",
                        provides=frozenset({VALUE}),
                        requires=frozenset({RESULT}),
                    ),
                    feature_a,
                ),
                lambda: FixtureFeature(
                    FeatureSpec(
                        "feature_b",
                        provides=frozenset({RESULT}),
                        optional=frozenset({VALUE}),
                    ),
                    feature_b,
                ),
            ]
        )
        async with runtime:
            assert runtime.require(VALUE) == 99
            assert runtime.require(RESULT) == "result_from_b"
            assert observed_b_optional == [None]
            assert observed_a_required == ["result_from_b"]

    asyncio.run(scenario())


def test_feature_spec_validates_optional_contracts() -> None:
    with pytest.raises(TypeError, match="must be frozensets"):
        FeatureSpec("bad", optional={VALUE})  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cannot depend on its own exports"):
        FeatureSpec("bad", provides=frozenset({VALUE}), optional=frozenset({VALUE}))
    with pytest.raises(ValueError, match="cannot be both required and optional"):
        FeatureSpec("bad", requires=frozenset({VALUE}), optional=frozenset({VALUE}))


def test_dynamic_subset_enabled_filtering() -> None:
    async def scenario() -> None:
        started: list[str] = []

        async def a_start(ctx: FeatureContext) -> None:
            started.append("a")
            ctx.provide(VALUE, 1)

        async def b_start(ctx: FeatureContext) -> None:
            started.append("b")
            ctx.provide(RESULT, "b")

        async def c_start(ctx: FeatureContext) -> None:
            started.append("c")

        runtime = Runtime(
            [
                lambda: FixtureFeature(
                    FeatureSpec("a", provides=frozenset({VALUE})), a_start
                ),
                lambda: FixtureFeature(
                    FeatureSpec("b", provides=frozenset({RESULT})), b_start
                ),
                lambda: FixtureFeature(FeatureSpec("c"), c_start),
            ],
            enabled={"a", "b"},
        )
        async with runtime:
            assert runtime.require(VALUE) == 1
            assert runtime.require(RESULT) == "b"
            assert started == ["a", "b"]

    asyncio.run(scenario())


def test_dynamic_subset_unknown_name_fails_fast() -> None:
    async def noop(ctx: FeatureContext) -> None:
        pass

    runtime = Runtime(
        [lambda: FixtureFeature(FeatureSpec("a"), noop)],
        enabled={"nonexistent"},
    )
    with pytest.raises(ValueError, match="Unknown enabled feature"):
        asyncio.run(runtime.__aenter__())


def test_dynamic_subset_missing_required_dependency_fails_fast() -> None:
    async def noop(ctx: FeatureContext) -> None:
        pass

    runtime = Runtime(
        [
            lambda: FixtureFeature(FeatureSpec("a", provides=frozenset({VALUE})), noop),
            lambda: FixtureFeature(
                FeatureSpec(
                    "b",
                    provides=frozenset({RESULT}),
                    requires=frozenset({VALUE}),
                ),
                noop,
            ),
        ],
        enabled={"b"},
    )
    with pytest.raises(CapabilityUnavailableError, match=r"b: example\.value"):
        asyncio.run(runtime.__aenter__())


def test_registry_profile_resolution() -> None:
    from app.registry import get_features

    factories, enabled = get_features(profile="default")
    assert enabled == frozenset()
    factories, enabled = get_features(enabled=["feat_a", "feat_b"])
    assert enabled == frozenset({"feat_a", "feat_b"})
    factories, enabled = get_features()
    assert enabled is None

    with pytest.raises(ValueError, match="Cannot specify both"):
        get_features(profile="default", enabled=["feat_a"])
    with pytest.raises(ValueError, match="Unknown profile"):
        get_features(profile="nonexistent_profile")


def test_runtime_convenience_inspection_methods() -> None:
    async def scenario() -> None:
        async def provide_val(ctx: FeatureContext) -> None:
            ctx.provide(VALUE, 100)

        runtime = Runtime(
            [
                lambda: FixtureFeature(
                    FeatureSpec("provider", provides=frozenset({VALUE})),
                    provide_val,
                ),
            ]
        )
        assert not runtime.has(VALUE)
        assert runtime.get(VALUE) is None
        assert not runtime.active_features

        async with runtime:
            assert runtime.has(VALUE)
            assert runtime.get(VALUE) == 100
            assert runtime.get(RESULT, "default_val") == "default_val"
            assert not runtime.has(RESULT)
            assert runtime.active_features == ("provider",)

        assert not runtime.has(VALUE)
        assert runtime.get(VALUE) is None
        assert not runtime.active_features

    asyncio.run(scenario())


def test_capability_token_properties_and_error_details() -> None:
    token = Capability[int](
        "service.counter",
        major=2,
        description="A monotonic counter service",
    )
    assert token.name == "service.counter"
    assert token.major == 2
    assert token.description == "A monotonic counter service"
    assert token.identifier == "service.counter@2"
    assert repr(token) == "Capability('service.counter', major=2)"

    # Description does not affect equality or hash
    same_token = Capability[int]("service.counter", major=2, description="Different")
    assert token == same_token
    assert hash(token) == hash(same_token)

    # CapabilityUnavailableError attributes
    err = CapabilityUnavailableError("service.counter", blocked_by="database")
    assert err.capability == "service.counter"
    assert err.blocked_by == "database"
    assert "service.counter" in str(err)
    assert "(blocked by 'database')" in str(err)


def test_feature_spec_and_protocol_invariants() -> None:
    spec = FeatureSpec(
        "auth",
        provides=frozenset({VALUE}),
        requires=frozenset({RESULT}),
        description="Auth service provider",
    )
    assert spec.name == "auth"
    assert spec.description == "Auth service provider"
    assert spec.dependencies == frozenset({RESULT})

    async def noop(ctx: FeatureContext) -> None:
        pass

    feature = FixtureFeature(spec, noop)
    assert isinstance(feature, Feature)
