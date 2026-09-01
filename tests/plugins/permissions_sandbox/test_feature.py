from pathlib import Path
from typing import Any

import pytest
from app.contracts.plugins.capabilities import SANDBOX_PERMISSIONS_CAPABILITY
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.plugins.permissions_sandbox.feature import (
    PluginPermissionsSandboxFeature,
    feature,
)
from app.services.plugins.permissions_sandbox.manifest import SPEC


def _context(
    instance: PluginPermissionsSandboxFeature,
) -> tuple[DefaultFeatureContext, ServiceRegistry, FeatureScope]:
    registry = ServiceRegistry()
    scope = FeatureScope(owner_id=instance.spec.feature_id)

    def register(capability: Any, provider: Any, owner_scope: FeatureScope) -> None:
        registry.register(
            capability,
            provider,
            owner_id=instance.spec.feature_id,
            scope=owner_scope,
        )

    return (
        DefaultFeatureContext(
            spec=instance.spec,
            scope=scope,
            resolver=registry.resolve,
            provider_registrar=register,
            event_bus=EventBus(),
        ),
        registry,
        scope,
    )


def test_spec_declares_one_stateless_provider() -> None:
    assert SPEC.provides == frozenset({SANDBOX_PERMISSIONS_CAPABILITY})
    assert not SPEC.requires
    assert SPEC.state is None
    assert "package_roots" in SPEC.config_keys


@pytest.mark.asyncio
async def test_mount_failure_publishes_nothing() -> None:
    instance = feature()
    context, registry, scope = _context(instance)
    with pytest.raises(TypeError):
        await instance.mount(context, None)
    assert registry.resolve(SANDBOX_PERMISSIONS_CAPABILITY) is None
    await scope.close()


@pytest.mark.asyncio
async def test_mount_and_scope_withdrawal_clear_grants(tmp_path: Path) -> None:
    instance = feature()
    context, registry, scope = _context(instance)
    await instance.mount(
        context,
        {"package_roots": {"a" * 64: str(tmp_path)}},
    )
    assert registry.resolve(SANDBOX_PERMISSIONS_CAPABILITY) is instance.service
    await scope.close()
    assert registry.resolve(SANDBOX_PERMISSIONS_CAPABILITY) is None
