"""Feature specification and mount tests for Instrument Catalogue."""

from typing import Any

import pytest
from app.contracts.catalogue.capabilities import CATALOG_INSTRUMENTS_CAPABILITY
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.kernel.state import RetentionPolicy
from app.services.catalogue.instrument_catalogue.feature import (
    InstrumentCatalogueFeature,
    feature,
)
from app.services.catalogue.instrument_catalogue.manifest import SPEC


def _context(
    feature_instance: InstrumentCatalogueFeature,
) -> tuple[DefaultFeatureContext, ServiceRegistry, FeatureScope]:
    """Build a scoped context for testing feature mounting."""
    registry = ServiceRegistry()
    scope = FeatureScope(owner_id=feature_instance.spec.feature_id)

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


def test_spec_declares_exact_provider_and_retained_state() -> None:
    """Verify specification metadata, capabilities, and state retention."""
    assert SPEC.provides == frozenset({CATALOG_INSTRUMENTS_CAPABILITY})
    assert SPEC.requires == frozenset()
    assert SPEC.config_keys == frozenset({"database_path"})
    assert SPEC.state is not None
    assert SPEC.state.namespace == "catalogue.instruments"
    assert SPEC.state.schema_version == 1
    assert SPEC.state.retention_policy == RetentionPolicy.RETAIN


@pytest.mark.asyncio
async def test_mount_stages_provider_and_scope_withdraws_it(tmp_path: Any) -> None:
    """Verify mounting stages CATALOG_INSTRUMENTS_CAPABILITY and scope close withdraws it."""
    feature_instance = feature()
    assert isinstance(feature_instance, InstrumentCatalogueFeature)
    context, registry, scope = _context(feature_instance)

    await feature_instance.mount(
        context,
        {"database_path": str(tmp_path / "instruments.db")},
    )
    assert feature_instance.service is not None
    assert registry.resolve(CATALOG_INSTRUMENTS_CAPABILITY) is feature_instance.service

    await scope.close()
    assert registry.resolve(CATALOG_INSTRUMENTS_CAPABILITY) is None


@pytest.mark.asyncio
async def test_mount_invalid_config_type_fails() -> None:
    """Verify non-string database_path fails with TypeError."""
    feature_instance = feature()
    context, registry, scope = _context(feature_instance)

    with pytest.raises(TypeError, match="database_path must be a string"):
        await feature_instance.mount(context, {"database_path": 12345})

    assert registry.resolve(CATALOG_INSTRUMENTS_CAPABILITY) is None
    await scope.close()
