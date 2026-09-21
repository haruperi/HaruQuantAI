"""Removal tests for gateway command automator feature."""

from __future__ import annotations

import asyncio

import pytest
from app.contracts.gateway import GATEWAY_AUTOMATION
from app.kernel.bootstrapper import Runtime
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.feature import FeatureSpec


def test_command_automator_removal_blocks_dependent_consumer() -> None:
    """Verify that removing command automator feature blocks consumers requiring it."""
    consumer_spec = FeatureSpec(
        name="test.automator_consumer",
        provides=frozenset(),
        requires=frozenset({GATEWAY_AUTOMATION}),
        description="Test consumer requiring command automator.",
    )

    class ConsumerFeature:
        @property
        def spec(self) -> FeatureSpec:
            return consumer_spec

        async def start(self, context: object) -> None:
            pass

        async def stop(self) -> None:
            pass

    async def _run() -> None:
        with pytest.raises(CapabilityUnavailableError):
            async with Runtime((ConsumerFeature,)):
                pass

    asyncio.run(_run())
