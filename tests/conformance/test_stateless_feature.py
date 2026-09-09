"""Self-tests proving the shared stateless lifecycle harness detects leaks."""

from __future__ import annotations

from contextlib import AsyncExitStack
from typing import Any

import pytest
from app.kernel.capability import CapabilityKey
from app.kernel.feature import FeatureSpec

from tests.conformance.stateless_feature import (
    StatelessFeatureCase,
    assert_scoped_withdrawal,
)

LEAK_CAPABILITY: CapabilityKey[object] = CapabilityKey(
    name="conformance.leaky", major=1
)
LEAK_SPEC = FeatureSpec(
    feature_id="FEAT-CONFORMANCE-LEAK",
    domain="conformance",
    provides=frozenset({LEAK_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Deliberately defective test fixture.",
    config_keys=frozenset(),
)


class LeakyFeature:
    """Defective fixture that detaches the registered cleanup stack."""

    spec = LEAK_SPEC

    async def mount(self, context: Any, _config: object) -> None:
        context.provide(LEAK_CAPABILITY, object())
        context.scope._stack = AsyncExitStack()


@pytest.mark.asyncio
async def test_injected_scope_leak_fails_shared_harness() -> None:
    """A resource-withdrawal defect must fail, not pass, the common harness."""
    case = StatelessFeatureCase(
        factory=LeakyFeature,
        feature_type=LeakyFeature,
        spec=LEAK_SPEC,
        capability=LEAK_CAPABILITY,
        entry_point_name="unused",
    )

    with pytest.raises(AssertionError):
        await assert_scoped_withdrawal(case)
