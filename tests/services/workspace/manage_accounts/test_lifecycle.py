"""Lifecycle and removability evidence for FEAT-WS-MANAGE_ACCOUNTS."""

from __future__ import annotations

from typing import Any
from uuid import uuid7

import pytest
from app.contracts.workspace.capabilities import (
    MANAGE_ACCOUNTS_CAPABILITY,
    PERSISTENCE_CAPABILITY,
)
from app.contracts.workspace.models import ManageAccountsRequest, ManageAccountsSuccess
from app.kernel.capability import CapabilityKey, CapabilityUnavailableError
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.workspace.execute_persistence.execute_persistence import (
    ExecutePersistenceService,
)
from app.services.workspace.manage_accounts.feature import feature


def _context(
    instance: Any,
    registry: ServiceRegistry,
    scope: FeatureScope,
) -> DefaultFeatureContext:
    def register(
        capability: CapabilityKey[Any],
        implementation: object,
        owner_scope: FeatureScope,
    ) -> None:
        registry.register(
            capability,
            implementation,
            owner_id=instance.spec.feature_id,
            scope=owner_scope,
        )

    return DefaultFeatureContext(
        spec=instance.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register,
        event_bus=EventBus(),
    )


def _request(operation: str, **values: object) -> ManageAccountsRequest:
    return ManageAccountsRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation=operation,  # type: ignore[arg-type]
        **values,  # type: ignore[arg-type]
    )


@pytest.mark.asyncio
async def test_trc_manage_accounts_nfr_001(tmp_path: Any) -> None:
    """ATN-WS-MANAGE_ACCOUNTS-001: exact withdrawal retains state and siblings."""
    registry = ServiceRegistry()
    persistence = ExecutePersistenceService()
    persistence_scope = FeatureScope(owner_id="FEAT-WS-EXECUTE_PERSISTENCE")
    registry.register(
        PERSISTENCE_CAPABILITY,
        persistence,
        owner_id="FEAT-WS-EXECUTE_PERSISTENCE",
        scope=persistence_scope,
    )
    unrelated_key: CapabilityKey[object] = CapabilityKey("test.unrelated", 1)
    unrelated = object()
    unrelated_scope = FeatureScope(owner_id="TEST-UNRELATED")
    registry.register(
        unrelated_key,
        unrelated,
        owner_id="TEST-UNRELATED",
        scope=unrelated_scope,
    )

    instance = feature()
    account_scope = FeatureScope(owner_id=instance.spec.feature_id)
    await instance.mount(
        _context(instance, registry, account_scope),
        {"database_path": tmp_path / "workspace"},
    )
    provider = registry.require(MANAGE_ACCOUNTS_CAPABILITY)
    registered = await provider.manage_accounts(
        _request(
            "REGISTER",
            username="retained_user",
            password="retained-password",  # pragma: allowlist secret
        )
    )
    assert isinstance(registered, ManageAccountsSuccess)

    await account_scope.close()
    assert registry.resolve(MANAGE_ACCOUNTS_CAPABILITY) is None
    assert registry.resolve(PERSISTENCE_CAPABILITY) is persistence
    assert registry.resolve(unrelated_key) is unrelated
    assert (tmp_path / "workspace" / "metadata" / "workspace.db").is_file()

    replacement = feature()
    replacement_scope = FeatureScope(owner_id=replacement.spec.feature_id)
    await replacement.mount(
        _context(replacement, registry, replacement_scope),
        {"database_path": tmp_path / "workspace"},
    )
    retained_login = await registry.require(MANAGE_ACCOUNTS_CAPABILITY).manage_accounts(
        _request(
            "LOGIN",
            username="retained_user",
            password="retained-password",  # pragma: allowlist secret
        )
    )
    assert isinstance(retained_login, ManageAccountsSuccess)
    await replacement_scope.close()
    await persistence_scope.close()
    await unrelated_scope.close()
    assert replacement_scope.active_effect_count == 0


@pytest.mark.asyncio
async def test_mount_without_persistence_fails_before_effects() -> None:
    """Missing required persistence prevents partial account registration."""
    instance = feature()
    registry = ServiceRegistry()
    scope = FeatureScope(owner_id=instance.spec.feature_id)
    with pytest.raises(CapabilityUnavailableError):
        await instance.mount(_context(instance, registry, scope), {})
    assert registry.resolve(MANAGE_ACCOUNTS_CAPABILITY) is None
    assert scope.active_effect_count == 0
