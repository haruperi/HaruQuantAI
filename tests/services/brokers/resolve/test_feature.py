"""Feature specification and mount tests for Service-Level Broker Resolver."""

from __future__ import annotations

from typing import Any

import pytest
from app.contracts.broker.capabilities import BROKER_RESOLVER_CAPABILITY
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.kernel.state import RetentionPolicy
from app.services.brokers.resolve.config import ResolveConfig
from app.services.brokers.resolve.feature import (
    ResolveFeature,
    feature,
)
from app.services.brokers.resolve.manifest import SPEC


def _context(
    feature_instance: ResolveFeature,
) -> tuple[DefaultFeatureContext, ServiceRegistry, FeatureScope]:
    """Build a scoped context for testing feature mounting."""
    registry = ServiceRegistry()
    scope = FeatureScope(owner_id=feature_instance.spec.feature_id)

    def register(
        capability: Any,
        provider: Any,
        owner_scope: FeatureScope,
    ) -> None:
        registry.register(
            capability,
            provider,
            owner_id=feature_instance.spec.feature_id,
            scope=owner_scope,
        )

    return (
        DefaultFeatureContext(
            spec=feature_instance.spec,
            scope=scope,
            resolver=registry.resolve,
            provider_registrar=register,
            event_bus=EventBus(),
        ),
        registry,
        scope,
    )


def test_spec_declares_exact_provider_and_retained_state() -> None:
    """Verify specification metadata, capabilities, and state retention."""
    assert SPEC.provides == frozenset({BROKER_RESOLVER_CAPABILITY})
    assert SPEC.requires == frozenset()
    assert SPEC.optional == frozenset()
    assert SPEC.config_keys == frozenset({"database_path"})
    assert SPEC.state is not None
    assert SPEC.state.namespace == "broker.resolve"
    assert SPEC.state.schema_version == 1
    assert SPEC.state.retention_policy == RetentionPolicy.RETAIN


@pytest.mark.asyncio
async def test_mount_stages_provider_and_scope_withdraws_it(tmp_path: Any) -> None:
    """Verify mounting stages BROKER_RESOLVER_CAPABILITY and scope close withdraws it."""
    feature_instance = feature()
    assert isinstance(feature_instance, ResolveFeature)
    context, registry, scope = _context(feature_instance)

    db_path = str(tmp_path / "brokers.db")
    await feature_instance.mount(
        context,
        {"database_path": db_path},
    )
    assert feature_instance.service is not None
    resolved = registry.resolve(BROKER_RESOLVER_CAPABILITY)
    assert resolved is feature_instance.service

    active = resolved.get_broker_module()
    assert active["name"] == "MetaTrader 5"

    await scope.close()
    assert registry.resolve(BROKER_RESOLVER_CAPABILITY) is None


@pytest.mark.asyncio
async def test_mount_with_typed_config(tmp_path: Any) -> None:
    """Verify mounting with a ResolveConfig object."""
    feature_instance = feature()
    context, registry, scope = _context(feature_instance)

    cfg = ResolveConfig(database_path=tmp_path / "typed.db")
    await feature_instance.mount(context, cfg)

    assert registry.resolve(BROKER_RESOLVER_CAPABILITY) is feature_instance.service
    await scope.close()
