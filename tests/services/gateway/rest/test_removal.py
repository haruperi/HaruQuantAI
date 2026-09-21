"""Removal tests for gateway REST feature."""

from __future__ import annotations

import asyncio

import pytest
from app.contracts.gateway import GATEWAY_REST
from app.kernel.bootstrapper import Runtime
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.feature import FeatureSpec


def test_rest_removal_blocks_dependent_consumer() -> None:
    """Verify that removing REST feature blocks consumers requiring it."""
    consumer_spec = FeatureSpec(
        name="test.rest_consumer",
        provides=frozenset(),
        requires=frozenset({GATEWAY_REST}),
        description="Test consumer requiring REST.",
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
