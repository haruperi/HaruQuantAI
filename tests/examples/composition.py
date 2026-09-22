"""Run with `uv run python -m tests.examples.composition`."""

import asyncio
from typing import Protocol

from app.kernel.bootstrapper import Runtime
from app.kernel.capability import Capability
from app.kernel.context import FeatureContext
from app.kernel.feature import FeatureSpec


class Greeting(Protocol):
    """Public greeting capability used only by this offline example."""

    def greet(self, name: str) -> str:
        """Create a greeting."""
        ...


GREETING = Capability[Greeting]("example.greeting")
MESSAGE = Capability[str]("example.message")


class GreetingFeature:
    """Provide a deterministic in-memory greeting service."""

    spec = FeatureSpec("greeting", provides=frozenset({GREETING}))

    def greet(self, name: str) -> str:
        """Return the requested greeting."""
        return f"Hello, {name}!"

    async def start(self, context: FeatureContext) -> None:
        """Publish the service through its typed capability."""
        context.provide(GREETING, self)


class WelcomeFeature:
    """Consume the declared greeting dependency."""

    spec = FeatureSpec(
        "welcome",
        provides=frozenset({MESSAGE}),
        requires=frozenset({GREETING}),
    )

    async def start(self, context: FeatureContext) -> None:
        """Build and publish one deterministic message."""
        context.provide(MESSAGE, context.require(GREETING).greet("template"))


async def example_composition() -> None:
    """Demonstrate required-edge ordering and explicit subset composition."""
    async with Runtime((WelcomeFeature, GreetingFeature)) as runtime:
        assert runtime.active_features == ("greeting", "welcome")
        assert runtime.require(MESSAGE) == "Hello, template!"

    async with Runtime(
        (WelcomeFeature, GreetingFeature), enabled={"greeting"}
    ) as runtime:
        assert runtime.require(GREETING).greet("subset") == "Hello, subset!"


if __name__ == "__main__":
    asyncio.run(example_composition())
