"""Removal tests for gateway authorization feature."""

from __future__ import annotations

import asyncio

import pytest
from app.contracts.gateway import GATEWAY_AUTHORIZATION
from app.kernel.bootstrapper import Runtime
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.feature import FeatureSpec


def test_authorization_removal_blocks_dependent_consumer() -> None:
    """Verify that removing authorization feature blocks consumers requiring it."""
    consumer_spec = FeatureSpec(
        name="test.auth_consumer",
        provides=frozenset(),
        requires=frozenset({GATEWAY_AUTHORIZATION}),
        description="Test consumer requiring authorization.",
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
        # Runtime with only ConsumerFeature (authorization removed) must fail startup
        with pytest.raises(CapabilityUnavailableError):
            async with Runtime((ConsumerFeature,)):
                pass

    asyncio.run(_run())
