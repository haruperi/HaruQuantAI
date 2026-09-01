"""Integration tests for FEAT-WS-SECURE_LOCAL_ACCESS (Workflow WF-WS-003)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from app.contracts.workspace.capabilities import (
    MANAGE_WORKSPACES_CAPABILITY,
    SECURE_LOCAL_ACCESS_CAPABILITY,
)
from app.contracts.workspace.errors import (
    NonLoopbackAccessDeniedError,
)
from app.contracts.workspace.models import (
    HealthStatus,
    LocalSession,
    WorkspaceRef,
)
from app.contracts.workspace.ports import SecureLocalAccessCapability
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.workspace.local_access_health.feature import (
    feature as local_access_feature,
)
from app.services.workspace.runtime_configuration.feature import (
    feature as runtime_config_feature,
)
from app.services.workspace.workspace_lifecycle.feature import (
    feature as workspace_lifecycle_feature,
)

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey


async def _mount_feature(
    feat: Any,
    registry: ServiceRegistry,
    event_bus: EventBus,
) -> None:
    """Mount a feature into the test registry with a dedicated context."""
    scope = FeatureScope(owner_id=feat.spec.feature_id)

    def registrar(cap: CapabilityKey[Any], impl: object, sc: FeatureScope) -> None:
        registry.register(cap, impl, owner_id=feat.spec.feature_id, scope=sc)

    context = DefaultFeatureContext(
        spec=feat.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=registrar,
        event_bus=event_bus,
    )
    await feat.mount(context, {})


@pytest.mark.asyncio
async def test_workflow_ws_003_secure_local_access_and_health(
    tmp_path: Path,
) -> None:
    """End-to-end integration test for WF-WS-003 Local Access and Health workflow."""
    registry = ServiceRegistry()
    event_bus = EventBus()

    # Mount lifecycle, runtime config, and local access features
    await _mount_feature(workspace_lifecycle_feature(), registry, event_bus)
    await _mount_feature(runtime_config_feature(), registry, event_bus)
    await _mount_feature(local_access_feature(), registry, event_bus)

    # Resolve capability
    secure_access = registry.resolve(SECURE_LOCAL_ACCESS_CAPABILITY)
    assert isinstance(secure_access, SecureLocalAccessCapability)

    # Check pre-workspace health
    health = secure_access.check_system_health()
    assert health.healthy is True
    assert health.status == HealthStatus.HEALTHY

    # Issue ephemeral local session
    session = secure_access.issue_local_session(
        client_id="wf_launcher",
        is_launcher_connected=True,
        client_host="127.0.0.1",
        ttl_seconds=1800,
    )
    assert isinstance(session, LocalSession)
    assert session.is_loopback is True

    # Verify session
    verified = secure_access.verify_local_session(
        token=session.token,
        client_host="127.0.0.1",
    )
    assert verified.client_id == "wf_launcher"

    # Test rejection of non-loopback caller
    with pytest.raises(NonLoopbackAccessDeniedError):
        secure_access.verify_local_session(
            token=session.token,
            client_host="172.16.0.4",
        )

    # Test readiness across workspace lifecycle
    unloaded_readiness = secure_access.report_system_readiness(workspace=None)
    assert unloaded_readiness.ready is False

    manage_ws = registry.resolve(MANAGE_WORKSPACES_CAPABILITY)
    assert manage_ws is not None
    ws_ref = manage_ws.initialize_workspace(
        tmp_path / "integration_ws",
        name="Integration WS",
    )

    assert isinstance(ws_ref, WorkspaceRef)

    ready_readiness = secure_access.report_system_readiness(workspace=ws_ref)
    assert ready_readiness.ready is True
    assert ready_readiness.schema_version == 1
    assert ready_readiness.worker_capacity >= 1

    # Redaction checks
    dumped_reasons = " ".join(ready_readiness.reasons)
    assert str(tmp_path) not in dumped_reasons
    assert session.token not in dumped_reasons
