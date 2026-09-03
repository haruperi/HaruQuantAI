"""Gateway and lifecycle tests for observe-market-catalogue."""

from __future__ import annotations

from typing import Any
from uuid import uuid7

import pytest
from app.contracts.catalogue.capabilities import CATALOG_INSTRUMENTS_CAPABILITY
from app.contracts.interfaces.capabilities import OBSERVE_MARKET_CATALOGUE_CAPABILITY
from app.contracts.interfaces.errors import InterfaceFailure
from app.contracts.interfaces.models import (
    ObserveMarketCatalogueRequest,
    ObserveMarketCatalogueSuccess,
)
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.interfaces.observe_market_catalogue.config import (
    ObserveMarketCatalogueConfig,
)
from app.services.interfaces.observe_market_catalogue.feature import (
    ObserveMarketCatalogueFeature,
    feature,
)
from app.services.interfaces.observe_market_catalogue.gateway import (
    MarketCatalogueGateway,
)
from app.services.interfaces.observe_market_catalogue.manifest import SPEC

from tests.services.interfaces.observe_market_catalogue.fakes import (
    FakeCatalogueProvider,
    make_instrument,
)


def _request(
    page_size: int = 100, cursor: str | None = None
) -> ObserveMarketCatalogueRequest:
    """Build a LIST request."""
    return ObserveMarketCatalogueRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation="LIST",
        page_size=page_size,
        page_cursor=cursor,
    )


def _page(result: object) -> ObserveMarketCatalogueSuccess:
    """Narrow a successful gateway result."""
    assert isinstance(result, ObserveMarketCatalogueSuccess)
    return result


def test_manifest_spec() -> None:
    """Verify feature specification constants and declarations."""
    assert SPEC.feature_id == "FEAT-IFACE-OBSERVE_MARKET_CATALOGUE"
    assert SPEC.domain == "interfaces"
    (provided,) = SPEC.provides
    (required,) = SPEC.requires
    assert provided.identifier == "interfaces.observe-market-catalogue@1"
    assert required.identifier == "catalogue.catalog-instruments@1"
    assert SPEC.config_keys == frozenset({"default_page_size", "max_page_size"})
    SPEC.validate()


def test_config_defaults_and_rejection() -> None:
    """Verify strict configuration parsing."""
    assert ObserveMarketCatalogueConfig().default_page_size == 100
    assert ObserveMarketCatalogueConfig().max_page_size == 200
    with pytest.raises(ValueError, match="Unknown observe-market-catalogue"):
        ObserveMarketCatalogueConfig.from_dict({"page": 10})
    with pytest.raises(ValueError, match="max_page_size"):
        ObserveMarketCatalogueConfig(default_page_size=300, max_page_size=200)
    with pytest.raises(TypeError, match="default_page_size"):
        ObserveMarketCatalogueConfig.from_dict({"default_page_size": "many"})


@pytest.mark.asyncio
async def test_gateway_projects_pages_and_clamps_size() -> None:
    """Verify page projection, cursor flow, and page-size clamping."""
    provider = FakeCatalogueProvider(
        {
            "": (
                make_instrument("EURUSD", "Euro vs US Dollar"),
                make_instrument("GBPUSD"),
            )
        }
    )
    gateway = MarketCatalogueGateway(
        provider,
        ObserveMarketCatalogueConfig(default_page_size=2, max_page_size=2),
    )

    first = _page(await gateway.observe_market_catalogue(_request(page_size=500)))
    assert [entry.symbol for entry in first.entries] == ["EURUSD", "GBPUSD"]
    assert provider.requests[0].page_size == 2
    assert first.entries[0].name == "Euro vs US Dollar"
    assert first.entries[0].asset_class == "FOREX"
    assert first.entries[0].digits == 5
    assert first.entries[0].bid is None
    assert first.next_cursor == "-page2"
    assert first.revision
    assert first.generated_at

    second = _page(await gateway.observe_market_catalogue(_request(2, "-page2")))
    assert second.entries == ()
    assert second.next_cursor is None


@pytest.mark.asyncio
async def test_gateway_maps_provider_failure_closed() -> None:
    """Verify provider failures map to the stable unavailable failure."""
    provider = FakeCatalogueProvider({}, fail=True)
    gateway = MarketCatalogueGateway(provider, ObserveMarketCatalogueConfig())

    result = await gateway.observe_market_catalogue(_request())

    assert isinstance(result, InterfaceFailure)
    assert result.code == "CAPABILITY_UNAVAILABLE"
    assert "catalogue store is not reachable" in result.problem.detail


@pytest.mark.asyncio
async def test_gateway_fails_closed_after_disposal() -> None:
    """Verify disposal fails subsequent browse requests."""
    gateway = MarketCatalogueGateway(
        FakeCatalogueProvider({}),
        ObserveMarketCatalogueConfig(),
    )
    gateway.close()
    gateway.close()

    result = await gateway.observe_market_catalogue(_request())
    assert isinstance(result, InterfaceFailure)
    assert result.code == "CAPABILITY_UNAVAILABLE"


def _context_for(
    spec: Any,
    registry: ServiceRegistry,
    scope: FeatureScope,
) -> DefaultFeatureContext:
    """Build a scoped context wired to the shared registry."""

    def register(
        capability: Any,
        provider: Any,
        owner_scope: FeatureScope,
    ) -> None:
        registry.register(
            capability,
            provider,
            owner_id=spec.feature_id,
            scope=owner_scope,
        )

    return DefaultFeatureContext(
        spec=spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register,
        event_bus=EventBus(),
    )


@pytest.mark.asyncio
async def test_feature_mount_and_removal_semantics() -> None:
    """Verify mount blocking, publication, and withdrawal."""
    registry = ServiceRegistry()
    feat = feature()
    scope = FeatureScope(owner_id=feat.spec.feature_id)

    with pytest.raises(CapabilityUnavailableError):
        await feat.mount(_context_for(feat.spec, registry, scope), None)
    assert feat.gateway is None

    registry.register(
        CATALOG_INSTRUMENTS_CAPABILITY,
        FakeCatalogueProvider({"": (make_instrument("EURUSD"),)}),
        owner_id="FEAT-CATALOGUE-INSTRUMENT_CATALOGUE",
        scope=FeatureScope(owner_id="FEAT-CATALOGUE-INSTRUMENT_CATALOGUE"),
    )
    observe_scope = FeatureScope(owner_id=feat.spec.feature_id)
    await feat.mount(_context_for(feat.spec, registry, observe_scope), None)

    gateway = feat.gateway
    assert gateway is not None
    assert registry.resolve(OBSERVE_MARKET_CATALOGUE_CAPABILITY) is gateway

    await observe_scope.close()
    assert registry.resolve(OBSERVE_MARKET_CATALOGUE_CAPABILITY) is None
    assert registry.resolve(CATALOG_INSTRUMENTS_CAPABILITY) is not None
    disposed = await gateway.observe_market_catalogue(_request())
    assert isinstance(disposed, InterfaceFailure)


@pytest.mark.asyncio
async def test_feature_mount_invalid_config_rolls_back() -> None:
    """Verify invalid configuration leaves no provider or gateway."""
    registry = ServiceRegistry()
    registry.register(
        CATALOG_INSTRUMENTS_CAPABILITY,
        FakeCatalogueProvider({}),
        owner_id="FEAT-CATALOGUE-INSTRUMENT_CATALOGUE",
        scope=FeatureScope(owner_id="FEAT-CATALOGUE-INSTRUMENT_CATALOGUE"),
    )
    feat = ObserveMarketCatalogueFeature()
    scope = FeatureScope(owner_id=feat.spec.feature_id)

    with pytest.raises(ValueError, match="Unknown observe-market-catalogue"):
        await feat.mount(_context_for(feat.spec, registry, scope), {"page": 1})
    assert feat.gateway is None
    assert registry.resolve(OBSERVE_MARKET_CATALOGUE_CAPABILITY) is None
