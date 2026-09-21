"""Removal tests for gateway application feature."""

from __future__ import annotations

import asyncio

import pytest
from app.contracts.gateway import GATEWAY_APPLICATION
from app.kernel.bootstrapper import Runtime
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.feature import FeatureSpec


def test_application_removal_blocks_dependent_consumer() -> None:
    """Verify that removing application feature blocks consumers requiring it."""
    consumer_spec = FeatureSpec(
        name="test.app_consumer",
        provides=frozenset(),
        requires=frozenset({GATEWAY_APPLICATION}),
        description="Test consumer requiring gateway application.",
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
