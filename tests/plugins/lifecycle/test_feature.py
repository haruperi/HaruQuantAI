"""Feature-spec and mount tests for Plugin Lifecycle."""

from typing import Any

import pytest
from app.contracts.plugins.capabilities import (
    DECLARE_MANIFESTS_CAPABILITY,
    MANAGE_LIFECYCLE_CAPABILITY,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.kernel.state import RetentionPolicy
from app.services.plugins.lifecycle.feature import PluginLifecycleFeature, feature
from app.services.plugins.lifecycle.manifest import SPEC


def _context(
    feature_instance: PluginLifecycleFeature,
) -> tuple[DefaultFeatureContext, ServiceRegistry, FeatureScope]:
    """Build a scoped context with the required manifest provider."""
    registry = ServiceRegistry()
    scope = FeatureScope(owner_id=feature_instance.spec.feature_id)
    registry.register(
        DECLARE_MANIFESTS_CAPABILITY,
        object(),
        owner_id="FEAT-PLUG-DECLARE_MANIFESTS",
    )

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


def test_spec_declares_exact_provider_dependency_and_retained_state() -> None:
    """Verify lifecycle ownership is declared through the standard feature spec."""
    assert SPEC.provides == frozenset({MANAGE_LIFECYCLE_CAPABILITY})
    assert SPEC.requires == frozenset({DECLARE_MANIFESTS_CAPABILITY})
    assert SPEC.config_keys == frozenset({"database_path"})
    assert SPEC.state is not None
    assert SPEC.state.namespace == "plugins.lifecycle"
    assert SPEC.state.schema_version == 1
    assert SPEC.state.retention_policy == RetentionPolicy.RETAIN


@pytest.mark.asyncio
async def test_mount_stages_provider_and_scope_withdraws_it(tmp_path: Any) -> None:
    """Verify successful mount publishes one provider and scope cleanup revokes it."""
    feature_instance = feature()
    assert isinstance(feature_instance, PluginLifecycleFeature)
    context, registry, scope = _context(feature_instance)

    await feature_instance.mount(context, {"database_path": str(tmp_path / "state.db")})
    assert feature_instance.service is not None
    assert registry.resolve(MANAGE_LIFECYCLE_CAPABILITY) is feature_instance.service
    await scope.close()
    assert registry.resolve(MANAGE_LIFECYCLE_CAPABILITY) is None


@pytest.mark.asyncio
async def test_mount_failure_publishes_nothing(tmp_path: Any) -> None:
    """Verify strict configuration failure cannot publish a partial provider."""
    feature_instance = feature()
    context, registry, scope = _context(feature_instance)
    with pytest.raises(TypeError, match="non-blank string"):
        await feature_instance.mount(context, {})
    assert registry.resolve(MANAGE_LIFECYCLE_CAPABILITY) is None
    await scope.close()
