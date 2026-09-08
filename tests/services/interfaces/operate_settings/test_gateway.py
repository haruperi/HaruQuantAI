"""Translation and lifecycle tests for the operate-settings feature."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import uuid7

import pytest
from app.contracts.interfaces.capabilities import OPERATE_SETTINGS_CAPABILITY
from app.contracts.interfaces.errors import InterfaceFailure
from app.contracts.interfaces.models import (
    OperateSettingsRequest,
    OperateSettingsSuccess,
)
from app.contracts.workspace.capabilities import ADMINISTER_SETTINGS_CAPABILITY
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.interfaces.operate_settings.config import OperateSettingsConfig
from app.services.interfaces.operate_settings.feature import OperateSettingsFeature
from app.services.interfaces.operate_settings.gateway import SettingsGateway
from app.services.interfaces.operate_settings.manifest import SPEC
from app.services.workspace.administer_settings.administer_settings import (
    SettingsService,
)
from app.services.workspace.administer_settings.config import AdministerSettingsConfig

from tests.services.interfaces.workspace_shared import init_settings_db

if TYPE_CHECKING:
    from pathlib import Path


def _request(operation: str, **kwargs: object) -> OperateSettingsRequest:
    """Build one operation request."""
    return OperateSettingsRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation=operation,  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )


def _context(
    feature: OperateSettingsFeature,
    registry: ServiceRegistry,
    scope: FeatureScope,
) -> DefaultFeatureContext:
    def register(capability: Any, provider: Any, owner_scope: FeatureScope) -> None:
        registry.register(
            capability,
            provider,
            owner_id=feature.spec.feature_id,
            scope=owner_scope,
        )

    return DefaultFeatureContext(
        spec=feature.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register,
        event_bus=EventBus(),
    )


def test_manifest_spec() -> None:
    """Verify feature specification and declared dependencies."""
    assert SPEC.feature_id == "FEAT-IFACE-OPERATE_SETTINGS"
    (provided,) = SPEC.provides
    assert provided.identifier == "interfaces.operate-settings@1"
    (required,) = SPEC.requires
    assert required.identifier == "workspace.administer-settings@1"
    SPEC.validate()


@pytest.mark.asyncio
async def test_settings_gateway_translation_flow(tmp_path: Path) -> None:
    """Verify settings gateway translates system read/update, manifest, credentials, and bridge."""
    db_file = tmp_path / "test_settings_gw.db"
    init_settings_db(db_file)
    store = SettingsService(AdministerSettingsConfig(database_path=db_file))
    gateway = SettingsGateway(store, OperateSettingsConfig())

    # Read system
    sys_res = await gateway.administer_settings(_request("READ_SYSTEM"))
    assert isinstance(sys_res, OperateSettingsSuccess)
    assert sys_res.system is not None
    assert sys_res.system.scope == "system"

    # Update system
    up_res = await gateway.administer_settings(
        _request(
            "UPDATE_SYSTEM",
            settings={"ACCOUNT_MODE": "demo"},
        )
    )
    assert isinstance(up_res, OperateSettingsSuccess)
    assert up_res.system is not None
    assert up_res.system.settings["ACCOUNT_MODE"] == "demo"

    # Read manifest
    man_res = await gateway.administer_settings(_request("READ_MANIFEST"))
    assert isinstance(man_res, OperateSettingsSuccess)
    assert len(man_res.manifest) == 59

    # Read credentials
    cred_res = await gateway.administer_settings(_request("READ_CREDENTIALS"))
    assert isinstance(cred_res, OperateSettingsSuccess)
    assert len(cred_res.credentials) > 0

    # Update credential
    up_cred_res = await gateway.administer_settings(
        _request(
            "UPDATE_CREDENTIAL",
            slot="google",
            material={
                "credentials.google_api_key": "NewGoogleKey",  # pragma: allowlist secret
            },
        )
    )
    assert isinstance(up_cred_res, OperateSettingsSuccess)
    assert up_cred_res.credential_updated is True

    # Read bridge runtime
    bridge_res = await gateway.administer_settings(_request("READ_BRIDGE_RUNTIME"))
    assert isinstance(bridge_res, OperateSettingsSuccess)
    assert bridge_res.bridge is not None
    assert bridge_res.bridge.host == "127.0.0.1"

    # Disposal fails closed
    gateway.close()
    closed_res = await gateway.administer_settings(_request("READ_SYSTEM"))
    assert isinstance(closed_res, InterfaceFailure)
    assert closed_res.code == "CAPABILITY_UNAVAILABLE"
    assert closed_res.problem.status == 503


@pytest.mark.asyncio
async def test_feature_mount_lifecycle(tmp_path: Path) -> None:
    """Verify feature mount fails when provider is absent and succeeds when present."""
    registry = ServiceRegistry()
    feature = OperateSettingsFeature()

    # Absent provider fails closed
    scope_fail = FeatureScope(owner_id="test_fail")
    context_fail = _context(feature, registry, scope_fail)
    with pytest.raises(CapabilityUnavailableError):
        await feature.mount(context_fail, None)

    # Present provider succeeds
    db_file = tmp_path / "test_lifecycle.db"
    init_settings_db(db_file)
    store = SettingsService(AdministerSettingsConfig(database_path=db_file))
    store_scope = FeatureScope(owner_id="FEAT-WS-ADMINISTER_SETTINGS")
    registry.register(
        ADMINISTER_SETTINGS_CAPABILITY,
        store,
        owner_id="FEAT-WS-ADMINISTER_SETTINGS",
        scope=store_scope,
    )
    scope_ok = FeatureScope(owner_id="FEAT-IFACE-OPERATE_SETTINGS")
    context_ok = _context(feature, registry, scope_ok)
    await feature.mount(context_ok, None)
    assert feature.gateway is not None
    assert registry.resolve(OPERATE_SETTINGS_CAPABILITY) is feature.gateway

    # Dispose scope cleanly
    await scope_ok.close()
