"""Tests for ServiceRegistry capability registration, generations, and exact-token revocation."""

import pytest

from app.kernel.capability import CapabilityUnavailableError
from app.kernel.registry import (
    BindingToken,
    CapabilityAlreadyBoundError,
    ServiceRegistry,
)
from app.kernel.scope import FeatureScope
from tests._support.composability import (
    CONSUMER_CAPABILITY,
    PROVIDER_CAPABILITY,
    ROOT_CAPABILITY,
)


def test_registry_register_and_resolve() -> None:
    """Test registering and resolving capability providers."""
    registry = ServiceRegistry()
    dummy_service = object()

    assert not registry.is_available(CONSUMER_CAPABILITY)
    assert not registry.is_available(CONSUMER_CAPABILITY.identifier)
    assert registry.resolve(CONSUMER_CAPABILITY) is None

    token = registry.register(
        capability=CONSUMER_CAPABILITY,
        provider=dummy_service,
        owner_id="FEAT-TEST-CONSUME_SERVICE",
    )

    assert token.capability == "test.consumer@1"
    assert token.owner_id == "FEAT-TEST-CONSUME_SERVICE"
    assert token.generation == 1

    assert registry.is_available(CONSUMER_CAPABILITY)
    assert registry.is_available(CONSUMER_CAPABILITY.identifier)
    assert registry.resolve(CONSUMER_CAPABILITY) is dummy_service
    assert registry.require(CONSUMER_CAPABILITY) is dummy_service

    binding = registry.get_binding(CONSUMER_CAPABILITY.identifier)
    assert binding is not None
    assert binding.token == token
    assert binding.provider is dummy_service


def test_registry_register_duplicate_raises_error() -> None:
    """Test that ordinary register() raises CapabilityAlreadyBoundError if already bound."""
    registry = ServiceRegistry()
    registry.register(
        capability=CONSUMER_CAPABILITY,
        provider=object(),
        owner_id="FEAT-TEST-CONSUME_SERVICE",
    )

    with pytest.raises(
        CapabilityAlreadyBoundError,
        match=r"(?i)already registered to 'FEAT-TEST-CONSUME_SERVICE'",
    ):
        registry.register(
            capability=CONSUMER_CAPABILITY,
            provider=object(),
            owner_id="FEAT-TEST-PROVIDE_ALTERNATE",
        )


def test_registry_require_missing_raises() -> None:
    """Test require raises CapabilityUnavailableError when no provider exists."""
    registry = ServiceRegistry()
    with pytest.raises(
        CapabilityUnavailableError,
        match=r"Capability 'test\.provider@1' is unavailable",
    ):
        registry.require(PROVIDER_CAPABILITY)


def test_registry_revoke_active_token() -> None:
    """Test revoking an active provider binding."""
    registry = ServiceRegistry()
    token = registry.register(
        capability=CONSUMER_CAPABILITY,
        provider=object(),
        owner_id="FEAT-TEST-CONSUME_SERVICE",
    )
    assert registry.is_available(CONSUMER_CAPABILITY)

    assert registry.revoke(token) is True
    assert not registry.is_available(CONSUMER_CAPABILITY)
    assert registry.resolve(CONSUMER_CAPABILITY) is None

    # Revoking again returns False
    assert registry.revoke(token) is False


def test_registry_generation_stale_token_protection() -> None:
    """Test that a stale disposer token cannot revoke a newer replacement provider."""
    registry = ServiceRegistry()
    service_v1 = object()
    service_v2 = object()

    token_v1 = registry.register(
        capability=CONSUMER_CAPABILITY,
        provider=service_v1,
        owner_id="FEAT-TEST-CONSUME_SERVICE",
    )
    assert token_v1.generation == 1

    # Replace via explicit replace_binding
    token_v2 = registry.replace_binding(
        capability=CONSUMER_CAPABILITY,
        provider=service_v2,
        owner_id="FEAT-TEST-PROVIDE_ALTERNATE",
    )
    assert token_v2.generation == 2
    assert registry.resolve(CONSUMER_CAPABILITY) is service_v2

    # Old disposer for token_v1 attempts revocation
    revoked = registry.revoke(token_v1)
    assert revoked is False
    # Newer provider is still active and safe
    assert registry.resolve(CONSUMER_CAPABILITY) is service_v2

    # New disposer revokes successfully
    assert registry.revoke(token_v2) is True
    assert registry.resolve(CONSUMER_CAPABILITY) is None


@pytest.mark.asyncio
async def test_registry_scope_automatic_revocation() -> None:
    """Test passing scope to register automatically revokes binding on scope close."""
    registry = ServiceRegistry()
    scope = FeatureScope("FEAT-TEST-CONSUME_SERVICE")
    service = object()

    token = registry.register(
        capability=CONSUMER_CAPABILITY,
        provider=service,
        owner_id="FEAT-TEST-CONSUME_SERVICE",
        scope=scope,
    )
    assert isinstance(token, BindingToken)
    assert registry.is_available(CONSUMER_CAPABILITY)

    await scope.close()
    assert not registry.is_available(CONSUMER_CAPABILITY)
    assert registry.resolve(CONSUMER_CAPABILITY) is None


def test_registry_register_many_atomic() -> None:
    """Test register_many atomically binds multiple capabilities or raises on conflict."""
    registry = ServiceRegistry()
    clock_service = object()
    market_service = object()

    tokens = registry.register_many(
        [
            (ROOT_CAPABILITY, clock_service, "FEAT-TEST-PROVIDE_ROOT"),
            (PROVIDER_CAPABILITY, market_service, "FEAT-TEST-PROVIDE_SERVICE"),
        ]
    )
    assert len(tokens) == 2
    assert registry.resolve(ROOT_CAPABILITY) is clock_service
    assert registry.resolve(PROVIDER_CAPABILITY) is market_service

    # Attempt register_many with one conflicting capability
    with pytest.raises(CapabilityAlreadyBoundError):
        registry.register_many(
            [
                (CONSUMER_CAPABILITY, object(), "FEAT-TEST-CONSUME_SERVICE"),
                (ROOT_CAPABILITY, object(), "FEAT-ANOTHER-CLOCK"),
            ]
        )

    # Historical bars should NOT have been registered due to all-or-nothing validation
    assert not registry.is_available(CONSUMER_CAPABILITY)


def test_registry_active_capabilities_and_clear() -> None:
    """Test active_capabilities snapshot and registry clear."""
    registry = ServiceRegistry()
    token1 = registry.register(
        CONSUMER_CAPABILITY, object(), "FEAT-TEST-CONSUME_SERVICE"
    )
    token2 = registry.register(
        PROVIDER_CAPABILITY, object(), "FEAT-TEST-PROVIDE_SERVICE"
    )

    active = registry.active_capabilities()
    assert active[CONSUMER_CAPABILITY.identifier] == token1
    assert active[PROVIDER_CAPABILITY.identifier] == token2

    registry.clear()
    assert len(registry.active_capabilities()) == 0
    assert not registry.is_available(CONSUMER_CAPABILITY)
