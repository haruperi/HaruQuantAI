"""Lifecycle, removability, and performance test suite for FEAT-WS-SECURE_LOCAL_ACCESS."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid7

import pytest
from app.contracts.workspace.capabilities import (
    MANAGE_ACCOUNTS_CAPABILITY,
    SECURE_LOCAL_ACCESS_CAPABILITY,
)
from app.contracts.workspace.secure_local_access import (
    SecretCreateRequest,
)
from app.kernel.capability import CapabilityKey, CapabilityUnavailableError
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.workspace.secure_local_access.config import (
    SecureLocalAccessConfig,
)
from app.services.workspace.secure_local_access.feature import feature


def _context(
    instance: Any,
    registry: ServiceRegistry,
    scope: FeatureScope,
) -> DefaultFeatureContext:
    """Build DefaultFeatureContext wired to test ServiceRegistry."""

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


@pytest.mark.asyncio
async def test_trc_secure_local_access_nfr_001() -> None:
    """ATN-WS-SECURE_LOCAL_ACCESS-001: Withdrawal, performance, and memory zeroization.

    Verifies:
    1. Mounting feature provides workspace.secure-local-access@1.
    2. Session verification completes within 5ms (NFR-WS-SECURE_LOCAL_ACCESS).
    3. Scope closure withdraws only workspace.secure-local-access@1 without affecting siblings.
    4. Scope closure zeroizes in-memory secret material.
    """
    registry = ServiceRegistry()
    accounts_dummy = object()
    accounts_scope = FeatureScope(owner_id="FEAT-WS-MANAGE_ACCOUNTS")
    registry.register(
        MANAGE_ACCOUNTS_CAPABILITY,
        accounts_dummy,
        owner_id="FEAT-WS-MANAGE_ACCOUNTS",
        scope=accounts_scope,
    )

    unrelated_key: CapabilityKey[object] = CapabilityKey("test.unrelated", 1)
    unrelated_impl = object()
    unrelated_scope = FeatureScope(owner_id="TEST-UNRELATED")
    registry.register(
        unrelated_key,
        unrelated_impl,
        owner_id="TEST-UNRELATED",
        scope=unrelated_scope,
    )

    instance = feature()
    feature_scope = FeatureScope(owner_id=instance.spec.feature_id)
    await instance.mount(
        _context(instance, registry, feature_scope),
        {"default_session_ttl_seconds": 1800, "enforce_loopback": True},
    )

    provider = registry.require(SECURE_LOCAL_ACCESS_CAPABILITY)
    assert provider is not None

    # Verify secret creation and store reference
    _ = provider.create_secret_reference(
        SecretCreateRequest(
            workspace_id=str(uuid7()),
            name="ephemeral_secret",
            secret_value="plaintext-to-zeroize",  # pragma: allowlist secret
            allowed_adapter_generation="v1",
            allowed_purpose="order-signing",
        )
    )

    # Issue session and measure validation latency (< 5ms per validation)
    session = provider.issue_local_session(
        client_id="perf_launcher",
        is_launcher_connected=True,
    )

    # Validation speed benchmark
    start = time.perf_counter()
    for _ in range(10):
        provider.verify_local_session(token=session.token, client_host="127.0.0.1")
    duration = (time.perf_counter() - start) / 10.0
    assert duration < 0.005, (
        f"Validation latency {duration * 1000:.2f}ms exceeds 5ms limit"
    )

    # Close the scope
    await feature_scope.close()

    # Verify capability was withdrawn
    assert registry.resolve(SECURE_LOCAL_ACCESS_CAPABILITY) is None
    # Sibling capabilities remain intact
    assert registry.resolve(MANAGE_ACCOUNTS_CAPABILITY) is accounts_dummy
    assert registry.resolve(unrelated_key) is unrelated_impl

    # Verify zeroization of secret material
    assert len(provider._secrets) == 0
    assert len(provider._sessions) == 0

    await accounts_scope.close()
    await unrelated_scope.close()


@pytest.mark.asyncio
async def test_mount_without_accounts_fails_before_effects() -> None:
    """Missing required manage-accounts capability prevents registration."""
    instance = feature()
    registry = ServiceRegistry()
    scope = FeatureScope(owner_id=instance.spec.feature_id)
    with pytest.raises(CapabilityUnavailableError):
        await instance.mount(_context(instance, registry, scope), {})
    assert registry.resolve(SECURE_LOCAL_ACCESS_CAPABILITY) is None
    assert scope.active_effect_count == 0


def test_config_validation_and_bounds() -> None:
    """Verify strict configuration schema rejection and bounds enforcement."""
    # 1. Unknown keys fail closed
    with pytest.raises(
        ValueError, match="Unknown secure-local-access configuration keys"
    ):
        SecureLocalAccessConfig.from_dict({"unexpected_key": 123})

    # 2. Out of bounds TTL
    with pytest.raises(ValueError, match="default_session_ttl_seconds must be between"):
        SecureLocalAccessConfig.from_dict({"default_session_ttl_seconds": 0})

    with pytest.raises(ValueError, match="default_session_ttl_seconds must be between"):
        SecureLocalAccessConfig.from_dict({"default_session_ttl_seconds": 999999999})

    # 3. Type mismatches
    with pytest.raises(
        TypeError, match="default_session_ttl_seconds must be an integer"
    ):
        SecureLocalAccessConfig.from_dict({"default_session_ttl_seconds": "not_an_int"})

    with pytest.raises(TypeError, match="enforce_loopback must be a boolean"):
        SecureLocalAccessConfig.from_dict({"enforce_loopback": "yes"})

    # 4. Valid defaults and overrides
    cfg = SecureLocalAccessConfig.from_dict(
        {
            "default_session_ttl_seconds": 7200,
            "enforce_loopback": False,
            "allowed_remote_subnets": ["10.0.0.0/24"],
            "require_authenticated_remote_policy": True,
        }
    )
    assert cfg.default_session_ttl_seconds == 7200
    assert cfg.enforce_loopback is False
    assert cfg.allowed_remote_subnets == ("10.0.0.0/24",)
    assert cfg.require_authenticated_remote_policy is True
