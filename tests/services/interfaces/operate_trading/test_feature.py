"""Unit tests for the operate-trading feature lifecycle."""

from typing import Any

import pytest
from app.contracts.interfaces.capabilities import OPERATE_TRADING_CAPABILITY
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.interfaces.operate_trading.feature import OperateTradingFeature


def _context(
    feature_instance: OperateTradingFeature,
    registry: ServiceRegistry,
    scope: FeatureScope,
) -> DefaultFeatureContext:
    def register(capability: Any, provider: Any, owner_scope: FeatureScope) -> None:
        registry.register(
            capability,
            provider,
            owner_id=feature_instance.spec.feature_id,
            scope=owner_scope,
        )

    return DefaultFeatureContext(
        spec=feature_instance.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register,
        event_bus=EventBus(),
    )


@pytest.mark.asyncio
async def test_feature_mount_and_provide() -> None:
    """Verify feature mounts, provides capability, and registers disposal."""
    feature_instance = OperateTradingFeature()
    registry = ServiceRegistry()
    scope = FeatureScope(owner_id="FEAT-IFACE-OPERATE_TRADING")
    context = _context(feature_instance, registry, scope)

    await feature_instance.mount(context, None)
    assert feature_instance.gateway is not None

    # Check registered capability
    provided = registry.resolve(OPERATE_TRADING_CAPABILITY)
    assert provided is feature_instance.gateway

    # Run scope cleanup
    await scope.close()
    assert feature_instance.gateway.closed is True
