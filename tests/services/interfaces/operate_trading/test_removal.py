"""Removal and isolation tests for operate-trading."""

from typing import Any

import pytest
from app.contracts.interfaces.capabilities import (
    OPERATE_TRADING_CAPABILITY,
    SERVE_API_EVENTS_CAPABILITY,
)
from app.kernel.capability import CapabilityUnavailableError
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
async def test_feature_removal_withdraws_capability() -> None:
    """Verify withdrawing operate-trading isolates other features."""
    feature_instance = OperateTradingFeature()
    registry = ServiceRegistry()
    scope = FeatureScope(owner_id="FEAT-IFACE-OPERATE_TRADING")
    context = _context(feature_instance, registry, scope)

    # Register an unrelated sentinel capability
    sentinel = object()
    registry.register(
        SERVE_API_EVENTS_CAPABILITY,
        sentinel,  # type: ignore[arg-type]
        owner_id="FEAT-IFACE-SERVE_API_EVENTS",
        scope=FeatureScope(owner_id="FEAT-IFACE-SERVE_API_EVENTS"),
    )

    await feature_instance.mount(context, None)
    assert registry.resolve(OPERATE_TRADING_CAPABILITY) is not None

    # Withdraw operate-trading via scope close
    await scope.close()

    with pytest.raises(CapabilityUnavailableError):
        registry.require(OPERATE_TRADING_CAPABILITY)

    # Sentinel remains unaffected
    assert registry.require(SERVE_API_EVENTS_CAPABILITY) is sentinel
