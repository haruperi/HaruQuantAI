"""Removal tests for gateway errors feature."""

from __future__ import annotations

import asyncio

import pytest
from app.contracts.gateway import GATEWAY_ERRORS
from app.kernel.bootstrapper import Runtime
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.feature import FeatureSpec


def test_errors_removal_blocks_dependent_consumer() -> None:
    """Verify that removing errors feature blocks consumers requiring it."""
    consumer_spec = FeatureSpec(
        name="test.errors_consumer",
        provides=frozenset(),
        requires=frozenset({GATEWAY_ERRORS}),
        description="Test consumer requiring errors.",
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
