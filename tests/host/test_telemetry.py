"""Behavioral evidence for the owner-local telemetry contract."""

import asyncio
import math

import pytest
from app.host.bootstrap import create_runtime
from app.host.telemetry import (
    HOST_TELEMETRY,
    TelemetryCapacityError,
    TelemetryClosedError,
    TelemetryEvent,
    TelemetryLevel,
    TelemetrySubscription,
)


def test_event_values_are_immutable_portable_and_bounded() -> None:
    event = TelemetryEvent(
        "host.ready",
        TelemetryLevel.INFO,
        (("count", 2), ("healthy", True), ("detail", None)),
    )
    assert event.fields[0] == ("count", 2)

    with pytest.raises(ValueError, match="nonempty"):
        TelemetryEvent(" ")
    with pytest.raises(TypeError, match="TelemetryLevel"):
        TelemetryEvent("level", "info")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unique"):
        TelemetryEvent("duplicate", fields=(("key", 1), ("key", 2)))
    with pytest.raises(TypeError, match="portable"):
        TelemetryEvent("mutable", fields=(("value", []),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="finite"):
        TelemetryEvent("nan", fields=(("value", math.nan),))


def test_delivery_is_ordered_snapshot_isolated_and_failure_safe() -> None:
    async def scenario() -> None:
        async with create_runtime() as runtime:
            telemetry = runtime.require(HOST_TELEMETRY)
            seen: list[str] = []
            first_handles: list[TelemetrySubscription] = []

            def first(event: TelemetryEvent) -> None:
                seen.append(f"first:{event.name}")
                first_handles[0].close()
                telemetry.subscribe(lambda later: seen.append(f"late:{later.name}"))

            def failing(_event: TelemetryEvent) -> None:
                raise ValueError("observer failed")

            first_handles.append(telemetry.subscribe(first))
            telemetry.subscribe(failing)
            telemetry.subscribe(lambda event: seen.append(f"last:{event.name}"))

            first_report = await telemetry.emit(TelemetryEvent("first"))
            assert first_report.delivered == 2
            assert len(first_report.failures) == 1
            assert first_report.failures[0].error_type == "ValueError"
            assert seen == ["first:first", "last:first"]

            second_report = await telemetry.emit(TelemetryEvent("second"))
            assert second_report.delivered == 2
            assert len(second_report.failures) == 1
            assert seen[-2:] == ["last:second", "late:second"]

    asyncio.run(scenario())


def test_subscription_capacity_and_handles_are_explicit() -> None:
    async def scenario() -> None:
        async with create_runtime(telemetry_max_subscribers=1) as runtime:
            telemetry = runtime.require(HOST_TELEMETRY)
            handle = telemetry.subscribe(lambda _event: None)
            with pytest.raises(TelemetryCapacityError):
                telemetry.subscribe(lambda _event: None)
            handle.close()
            handle.close()
            replacement = telemetry.subscribe(lambda _event: None)
            replacement.close()

    asyncio.run(scenario())


def test_provider_shutdown_closes_emission_and_subscriptions() -> None:
    async def scenario() -> None:
        runtime = create_runtime()
        async with runtime:
            telemetry = runtime.require(HOST_TELEMETRY)
            handle = telemetry.subscribe(lambda _event: None)
        handle.close()
        with pytest.raises(TelemetryClosedError):
            telemetry.subscribe(lambda _event: None)
        with pytest.raises(TelemetryClosedError):
            await telemetry.emit(TelemetryEvent("after-close"))

    asyncio.run(scenario())


def test_real_publisher_cancellation_is_not_swallowed() -> None:
    async def scenario() -> None:
        entered = asyncio.Event()
        async with create_runtime() as runtime:
            telemetry = runtime.require(HOST_TELEMETRY)

            async def waiting(_event: TelemetryEvent) -> None:
                entered.set()
                await asyncio.Event().wait()

            telemetry.subscribe(waiting)
            task = asyncio.create_task(telemetry.emit(TelemetryEvent("waiting")))
            await entered.wait()
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    asyncio.run(scenario())


def test_diagnostic_history_is_bounded_and_immutable() -> None:
    async def scenario() -> None:
        async with create_runtime(diagnostic_capacity=2) as runtime:
            telemetry = runtime.require(HOST_TELEMETRY)

            def failing(_event: TelemetryEvent) -> None:
                raise RuntimeError("failure")

            telemetry.subscribe(failing)
            for index in range(3):
                await telemetry.emit(TelemetryEvent(f"event.{index}"))
            assert len(telemetry.diagnostics) == 2
            assert all(
                item.code == "host.telemetry.subscriber_failed"
                for item in telemetry.diagnostics
            )

    asyncio.run(scenario())
