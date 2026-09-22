"""Run with `uv run python -m tests.examples.telemetry_usage`."""

import asyncio

from app.host.bootstrap import create_runtime
from app.host.telemetry import HOST_TELEMETRY, TelemetryEvent


async def example_telemetry() -> None:
    """Prove observer isolation and explicit subscription cleanup offline."""
    received: list[str] = []
    async with create_runtime() as runtime:
        telemetry = runtime.require(HOST_TELEMETRY)
        healthy = telemetry.subscribe(lambda event: received.append(event.name))

        def failing(_event: TelemetryEvent) -> None:
            raise RuntimeError("example observer failure")

        failed = telemetry.subscribe(failing)
        report = await telemetry.emit(
            TelemetryEvent("example.ready", fields=(("offline", True),))
        )
        assert received == ["example.ready"]
        assert report.delivered == 1
        assert len(report.failures) == 1
        assert report.failures[0].error_type == "RuntimeError"
        healthy.close()
        failed.close()


if __name__ == "__main__":
    asyncio.run(example_telemetry())
