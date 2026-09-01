"""Unit tests for DiagnosticBundleFeature lifecycle and mounting."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from app.contracts.workspace.capabilities import (
    BUILD_DIAGNOSTICS_CAPABILITY,
    CONFIGURE_RUNTIME_CAPABILITY,
    MANAGE_WORKSPACES_CAPABILITY,
)
from app.contracts.workspace.ports import (
    BuildDiagnosticsCapability,
    ConfigureRuntimeCapability,
    ManageWorkspacesCapability,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.workspace.diagnostic_bundle.feature import (
    DiagnosticBundleFeature,
    feature,
)
from app.services.workspace.diagnostic_bundle.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey


@pytest.mark.asyncio
async def test_feature_mount_and_discovery() -> None:
    """Test feature factory, mounting, and capability registration."""
    feat = feature()
    assert isinstance(feat, DiagnosticBundleFeature)
    assert feat.spec == SPEC

    registry = ServiceRegistry()
    event_bus = EventBus()
    scope = FeatureScope(owner_id=feat.spec.feature_id)

    # Register required dependencies
    mock_lifecycle = MagicMock(spec=ManageWorkspacesCapability)
    lifecycle_scope = FeatureScope(owner_id="FEAT-WS-MANAGE_WORKSPACES")
    registry.register(
        MANAGE_WORKSPACES_CAPABILITY,
        mock_lifecycle,
        owner_id="FEAT-WS-MANAGE_WORKSPACES",
        scope=lifecycle_scope,
    )

    mock_config = MagicMock(spec=ConfigureRuntimeCapability)
    config_scope = FeatureScope(owner_id="FEAT-WS-CONFIGURE_RUNTIME")
    registry.register(
        CONFIGURE_RUNTIME_CAPABILITY,
        mock_config,
        owner_id="FEAT-WS-CONFIGURE_RUNTIME",
        scope=config_scope,
    )

    def registrar(
        cap: CapabilityKey[Any],
        impl: object,
        sc: FeatureScope,
    ) -> None:
        registry.register(cap, impl, owner_id=feat.spec.feature_id, scope=sc)

    context = DefaultFeatureContext(
        spec=feat.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=registrar,
        event_bus=event_bus,
    )

    await feat.mount(context, config={})
    resolved = registry.resolve(BUILD_DIAGNOSTICS_CAPABILITY)
    assert resolved is not None
    assert isinstance(resolved, BuildDiagnosticsCapability)
    assert feat.service is not None
    await scope.close()
