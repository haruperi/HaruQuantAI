"""Removal tests for gateway streams feature."""

from __future__ import annotations

import asyncio

import pytest
from app.contracts.gateway import GATEWAY_STREAMS
from app.kernel.bootstrapper import Runtime
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.feature import FeatureSpec


def test_streams_removal_blocks_dependent_consumer() -> None:
    """Verify that removing streams feature blocks consumers requiring it."""
    consumer_spec = FeatureSpec(
        name="test.streams_consumer",
        provides=frozenset(),
        requires=frozenset({GATEWAY_STREAMS}),
        description="Test consumer requiring streams.",
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
