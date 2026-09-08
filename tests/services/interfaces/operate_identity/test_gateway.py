"""Translation and lifecycle tests for the operate-identity feature."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import uuid7

import pytest
from app.contracts.interfaces.capabilities import OPERATE_IDENTITY_CAPABILITY
from app.contracts.interfaces.errors import InterfaceFailure
from app.contracts.interfaces.models import (
    OperateIdentityRequest,
    OperateIdentitySuccess,
)
from app.contracts.workspace.capabilities import MANAGE_ACCOUNTS_CAPABILITY
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.interfaces.operate_identity.config import OperateIdentityConfig
from app.services.interfaces.operate_identity.feature import OperateIdentityFeature
from app.services.interfaces.operate_identity.gateway import IdentityGateway
from app.services.interfaces.operate_identity.manifest import SPEC
from app.services.workspace.execute_persistence.execute_persistence import (
    ExecutePersistenceService,
)
from app.services.workspace.manage_accounts.accounts import AccountService
from app.services.workspace.manage_accounts.config import ManageAccountsConfig

if TYPE_CHECKING:
    from pathlib import Path


def _request(operation: str, **kwargs: object) -> OperateIdentityRequest:
    """Build one operation request."""
    return OperateIdentityRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation=operation,  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )


def _context(
    feature: OperateIdentityFeature,
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
    assert SPEC.feature_id == "FEAT-IFACE-OPERATE_IDENTITY"
    (provided,) = SPEC.provides
    assert provided.identifier == "interfaces.operate-identity@1"
    (required,) = SPEC.requires
    assert required.identifier == "workspace.manage-accounts@1"
    SPEC.validate()


@pytest.mark.asyncio
async def test_identity_gateway_translation_flow(tmp_path: Path) -> None:
    """Verify identity gateway translates register, login, me, and logout."""
    store = AccountService(
        ExecutePersistenceService(),
        ManageAccountsConfig(database_path=tmp_path / "identity-workspace"),
    )
    gateway = IdentityGateway(store, OperateIdentityConfig())

    # Register
    reg_req = _request(
        "REGISTER",
        username="charlie",
        password="SecurePassword123",  # pragma: allowlist secret
    )
    reg_res = await gateway.operate_identity(reg_req)
    assert isinstance(reg_res, OperateIdentitySuccess)
    assert reg_res.user is not None
    assert reg_res.user.username == "charlie"
    session_token = reg_res.session_token

    # Me
    me_req = _request("ME", session_token=session_token)
    me_res = await gateway.operate_identity(me_req)
    assert isinstance(me_res, OperateIdentitySuccess)
    assert me_res.user is not None
    assert me_res.user.username == "charlie"

    # Login
    login_req = _request(
        "LOGIN",
        username="charlie",
        password="SecurePassword123",  # pragma: allowlist secret
    )
    login_res = await gateway.operate_identity(login_req)
    assert isinstance(login_res, OperateIdentitySuccess)
    assert login_res.session_token != ""

    # Failure mapping: duplicate registration
    dup_res = await gateway.operate_identity(reg_req)
    assert isinstance(dup_res, InterfaceFailure)
    assert dup_res.code == "INTERFACE_VALIDATION_FAILED"
    assert dup_res.problem.status == 400

    # Logout
    logout_req = _request("LOGOUT", session_token=session_token)
    logout_res = await gateway.operate_identity(logout_req)
    assert isinstance(logout_res, OperateIdentitySuccess)
    assert logout_res.revoked is True

    # Disposal fails closed
    gateway.close()
    closed_res = await gateway.operate_identity(me_req)
    assert isinstance(closed_res, InterfaceFailure)
    assert closed_res.code == "CAPABILITY_UNAVAILABLE"
    assert closed_res.problem.status == 503

    store.close()


@pytest.mark.asyncio
async def test_feature_mount_lifecycle(tmp_path: Path) -> None:
    """Verify feature mount fails when provider is absent and succeeds when present."""
    registry = ServiceRegistry()
    feature = OperateIdentityFeature()

    # Absent provider fails closed
    scope_fail = FeatureScope(owner_id="test_fail")
    context_fail = _context(feature, registry, scope_fail)
    with pytest.raises(CapabilityUnavailableError):
        await feature.mount(context_fail, None)

    # Present provider succeeds
    store = AccountService(
        ExecutePersistenceService(),
        ManageAccountsConfig(database_path=tmp_path / "lifecycle-workspace"),
    )
    store_scope = FeatureScope(owner_id="FEAT-WS-MANAGE_ACCOUNTS")
    registry.register(
        MANAGE_ACCOUNTS_CAPABILITY,
        store,
        owner_id="FEAT-WS-MANAGE_ACCOUNTS",
        scope=store_scope,
    )
    scope_ok = FeatureScope(owner_id="FEAT-IFACE-OPERATE_IDENTITY")
    context_ok = _context(feature, registry, scope_ok)
    await feature.mount(context_ok, None)
    assert feature.gateway is not None
    assert registry.resolve(OPERATE_IDENTITY_CAPABILITY) is feature.gateway

    # Dispose scope cleanly
    await scope_ok.close()
    store.close()
