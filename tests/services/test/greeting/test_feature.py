"""Lifecycle and mounting tests for GreetingFeature."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from app.contracts.test.greeting import (
    GREETING_SERVICE,
    GreetingRequest,
    GreetingService,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.feature import Feature
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.test.greeting.feature import GreetingFeature, create_feature

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey


def test_create_feature_returns_feature_instance() -> None:
    feature = create_feature()
    assert isinstance(feature, GreetingFeature)
    assert isinstance(feature, Feature)


def test_feature_spec_invariants() -> None:
    feature = create_feature()
    spec = feature.spec
    spec.validate()
    assert spec.feature_id == "FEAT-TEST-GREETING"
    assert spec.domain == "test"
    assert spec.provides == frozenset({GREETING_SERVICE})
    assert spec.requires == frozenset()
    assert spec.optional == frozenset()
    assert spec.conflicts == frozenset()
    assert spec.config_keys == frozenset({"default_salutation", "max_name_length"})
    assert spec.state is None


@pytest.mark.asyncio
async def test_feature_mount_default_config() -> None:
    feature = create_feature()
    registry = ServiceRegistry()
    event_bus = EventBus()
    scope = FeatureScope(owner_id=feature.spec.feature_id)

    def register_provider(
        capability: CapabilityKey[Any],
        provider: Any,
        owner_scope: FeatureScope,
    ) -> None:
        registry.register(
            capability,
            provider,
            owner_id=feature.spec.feature_id,
            scope=owner_scope,
        )

    context = DefaultFeatureContext(
        spec=feature.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register_provider,
        event_bus=event_bus,
    )

    await feature.mount(context, {})

    service = registry.resolve(GREETING_SERVICE)
    assert isinstance(service, GreetingService)

    response = await service.generate_greeting(GreetingRequest(name="Bob"))
    assert response.message == "Hello, Bob!"

    await scope.close()


@pytest.mark.asyncio
async def test_feature_mount_custom_config() -> None:
    feature = create_feature()
    registry = ServiceRegistry()
    event_bus = EventBus()
    scope = FeatureScope(owner_id=feature.spec.feature_id)

    def register_provider(
        capability: CapabilityKey[Any],
        provider: Any,
        owner_scope: FeatureScope,
    ) -> None:
        registry.register(
            capability,
            provider,
            owner_id=feature.spec.feature_id,
            scope=owner_scope,
        )

    context = DefaultFeatureContext(
        spec=feature.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register_provider,
        event_bus=event_bus,
    )

    await feature.mount(
        context,
        {"default_salutation": "Welcome", "max_name_length": 10},
    )

    service = registry.resolve(GREETING_SERVICE)
    assert service is not None
    response = await service.generate_greeting(GreetingRequest(name="Carol"))
    assert response.message == "Welcome, Carol!"

    with pytest.raises(ValueError, match="Caller name exceeds maximum allowed length"):
        await service.generate_greeting(GreetingRequest(name="VeryLongNameExceeding10"))

    await scope.close()


@pytest.mark.asyncio
async def test_feature_mount_invalid_config_raises() -> None:
    feature = create_feature()
    registry = ServiceRegistry()
    event_bus = EventBus()
    scope = FeatureScope(owner_id=feature.spec.feature_id)

    context = DefaultFeatureContext(
        spec=feature.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=lambda cap, prov, sc: None,
        event_bus=event_bus,
    )

    with pytest.raises(ValueError, match="Unknown Greeting configuration keys"):
        await feature.mount(context, {"unknown_key": 42})

    await scope.close()
