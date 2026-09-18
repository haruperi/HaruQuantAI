"""Run with `uv run python -m tests.examples.composition`."""

import asyncio
from typing import Protocol

from app.kernel.bootstrapper import Runtime
from app.kernel.capability import Capability
from app.kernel.context import FeatureContext
from app.kernel.feature import FeatureSpec


class Greeting(Protocol):
    """Public greeting capability."""

    def greet(self, name: str) -> str:
        """Create a greeting."""
        ...


class Metrics(Protocol):
    """Optional telemetry capability."""

    def record(self, metric: str) -> None:
        """Record an event."""
        ...


GREETING = Capability[Greeting]("greetings.greet")
METRICS = Capability[Metrics]("telemetry.metrics")
MESSAGE = Capability[str]("welcome.message")


class GreetingFeature:
    """Provide an offline greeting service."""

    spec = FeatureSpec("greeting", provides=frozenset({GREETING}))

    def greet(self, name: str) -> str:
        """Return the requested greeting."""
        return f"Hello, {name}!"

    async def start(self, context: FeatureContext) -> None:
        """Publish the service through its public protocol."""
        context.provide(GREETING, self)


class MetricsFeature:
    """Provide an optional telemetry tracking service."""

    spec = FeatureSpec("metrics", provides=frozenset({METRICS}))

    def __init__(self) -> None:
        self.events: list[str] = []

    def record(self, metric: str) -> None:
        """Record a telemetry event."""
        self.events.append(metric)

    async def start(self, context: FeatureContext) -> None:
        """Publish the telemetry service."""
        context.provide(METRICS, self)


class WelcomeFeature:
    """Consume a mandatory greeting and an optional telemetry service."""

    spec = FeatureSpec(
        "welcome",
        provides=frozenset({MESSAGE}),
        requires=frozenset({GREETING}),
        optional=frozenset({METRICS}),
    )

    async def start(self, context: FeatureContext) -> None:
        """Build a message and progressively enhance with telemetry if present."""
        greeting_service = context.require(GREETING)
        message = greeting_service.greet("template")

        metrics = context.optional(METRICS)
        if metrics is not None:
            metrics.record("greeting_composed")

        context.provide(MESSAGE, message)


async def example_composition() -> None:
    """Demonstrate dependency ordering, optional enhancements, and dynamic subsets."""
    # 1. Full composition with optional metrics active:
    async with Runtime((WelcomeFeature, GreetingFeature, MetricsFeature)) as runtime:
        message = runtime.require(MESSAGE)
        assert message == "Hello, template!"
        print(f"Full composition with telemetry: {message}")

    # 2. Dynamic subset (progressive enhancement when metrics is excluded):
    async with Runtime(
        (WelcomeFeature, GreetingFeature, MetricsFeature),
        enabled={"welcome", "greeting"},
    ) as runtime:
        message = runtime.require(MESSAGE)
        assert message == "Hello, template!"
        print(f"Dynamic subset without telemetry: {message}")


if __name__ == "__main__":
    asyncio.run(example_composition())
