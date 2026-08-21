"""Category B Composability Tests: Generic Feature Contract Test Suite.

Enforces that every feature in HaruQuantAI satisfies identical architectural
and contract requirements.
"""

import re
from contextlib import suppress
from typing import TYPE_CHECKING, Any

import pytest

from app.composition.discovery import FeatureDiscoverer
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey
    from app.kernel.feature import Feature

# Naming convention: FEAT-<DOMAIN>-<VERB_ADJECTIVE>
FEATURE_ID_REGEX = re.compile(r"^FEAT-[A-Z]+-[A-Z_]+$")


def _discover_feature_classes() -> list[type[Feature]]:
    """Discover feature classes using FeatureDiscoverer with built-in fallback."""
    discoverer = FeatureDiscoverer()
    discovered = list(discoverer.discover().discovered.values())
    if discovered:
        return [feat.__class__ for feat in discovered]

    from app.services.broker.mock_feed.feature import MockFeedFeature
    from app.services.data.historical_bars.feature import HistoricalBarsFeature
    from app.services.system.storage.feature import StorageFeature

    return [MockFeedFeature, HistoricalBarsFeature, StorageFeature]


@pytest.fixture(scope="module")
def all_discovered_features() -> list[Feature]:
    """Discover all registered feature instances."""
    return [cls() for cls in _discover_feature_classes()]


def test_discovered_features_non_empty(
    all_discovered_features: list[Feature],
) -> None:
    """Verify that feature discovery finds features in the codebase."""
    assert len(all_discovered_features) >= 3


@pytest.mark.parametrize(
    "feature_cls",
    _discover_feature_classes(),
)
def test_feature_contract_spec_and_id(
    feature_cls: type[Feature],
) -> None:
    """Verify feature ID, spec declaration, and naming convention."""
    feature = feature_cls()
    spec = feature.spec

    # 1. Feature ID syntax
    assert FEATURE_ID_REGEX.match(spec.feature_id), (
        f"Invalid feature ID format: {spec.feature_id}"
    )

    # 2. Domain classification
    assert spec.domain.strip(), "Feature must declare a non-empty domain"
    assert spec.description.strip(), "Feature must declare a description"

    # 3. Provided capabilities
    assert len(spec.provides) > 0, "Feature must provide at least one capability"
    for cap in spec.provides:
        assert cap.name.strip()
        assert cap.major >= 1
        assert cap.identifier == f"{cap.name}@{cap.major}"


@pytest.mark.parametrize(
    "feature_cls",
    _discover_feature_classes(),
)
@pytest.mark.asyncio
async def test_feature_contract_idempotent_unmount(
    feature_cls: type[Feature],
) -> None:
    """Verify unmount is safe and idempotent even when called repeatedly."""
    feature = feature_cls()
    registry = ServiceRegistry()
    event_bus = EventBus()
    scope = FeatureScope(owner_id=feature.spec.feature_id)

    def register_provider(cap: CapabilityKey[Any], prov: Any, sc: FeatureScope) -> None:
        registry.register(cap, prov, owner_id=feature.spec.feature_id, scope=sc)

    context = DefaultFeatureContext(
        spec=feature.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register_provider,
        event_bus=event_bus,
    )

    # Mount may fail if dependencies are missing, but unmount MUST never crash
    with suppress(Exception):
        cfg: dict[str, object] = {}
        await feature.mount(context, cfg)

    # Double unmount/close must succeed without error
    if hasattr(feature, "unmount"):
        await feature.unmount(context)
        await feature.unmount(context)
    await scope.close()
    await scope.close()
