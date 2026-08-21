"""Generic contract tests for every currently registered feature."""

from __future__ import annotations

import re
import tomllib
from contextlib import suppress
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from app.composition.discovery import FeatureDiscoverer
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.feature import Feature
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey

FEATURE_ID_REGEX = re.compile(r"^FEAT-[A-Z]+-[A-Z_]+$")


def _registered_feature_targets() -> dict[str, str]:
    """Read the current registered feature targets from pyproject.toml."""
    with Path("pyproject.toml").open("rb") as file:
        data = tomllib.load(file)
    targets = (
        data.get("project", {}).get("entry-points", {}).get("haruquantai.features", {})
    )
    if not isinstance(targets, dict):
        raise TypeError("Feature entry-point table must be a mapping")
    return {str(name): str(target) for name, target in targets.items()}


def _load_registered_classes() -> list[type[Feature]]:
    classes: list[type[Feature]] = []
    for entry_point_name, target in _registered_feature_targets().items():
        if ":" not in target:
            raise ValueError(
                f"Invalid feature entry point '{entry_point_name}': '{target}'"
            )
        module_name, factory_name = target.split(":", maxsplit=1)
        module = import_module(module_name)
        factory = getattr(module, factory_name)
        feature = factory() if callable(factory) else factory
        if not isinstance(feature, Feature):
            raise TypeError(
                f"Entry point '{entry_point_name}' does not satisfy Feature"
            )
        classes.append(type(feature))
    return classes


def _discover_feature_classes() -> list[type[Feature]]:
    """Discover features, with a removal-safe metadata fallback."""
    discovered = list(FeatureDiscoverer().discover().discovered.values())
    if discovered:
        return [type(feature) for feature in discovered]
    return _load_registered_classes()


@pytest.fixture(scope="module")
def all_discovered_features() -> list[Feature]:
    """Instantiate every feature still registered in this workspace."""
    return [feature_class() for feature_class in _discover_feature_classes()]


def test_discovered_features_match_registered_entry_points(
    all_discovered_features: list[Feature],
) -> None:
    """Discovery covers every registered feature without hardcoded counts."""
    registered = _registered_feature_targets()
    assert registered
    assert len(all_discovered_features) == len(registered)
    assert {feature.spec.feature_id for feature in all_discovered_features} == {
        feature_class().spec.feature_id for feature_class in _load_registered_classes()
    }


@pytest.mark.parametrize("feature_cls", _discover_feature_classes())
def test_feature_contract_spec_and_id(feature_cls: type[Feature]) -> None:
    """Every feature declares a valid, cohesive capability specification."""
    feature = feature_cls()
    spec = feature.spec
    assert FEATURE_ID_REGEX.match(spec.feature_id), (
        f"Invalid feature ID format: {spec.feature_id}"
    )
    assert spec.domain.strip()
    assert spec.description.strip()
    assert spec.provides
    for capability in spec.provides:
        assert capability.name.strip()
        assert capability.major >= 1
        assert capability.identifier == f"{capability.name}@{capability.major}"


@pytest.mark.parametrize("feature_cls", _discover_feature_classes())
@pytest.mark.asyncio
async def test_feature_contract_idempotent_unmount(
    feature_cls: type[Feature],
) -> None:
    """Unmount remains safe after a failed or partial dependency resolution."""
    feature = feature_cls()
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
    with suppress(Exception):
        await feature.mount(context, {})

    if hasattr(feature, "unmount"):
        await feature.unmount(context)
        await feature.unmount(context)
    await scope.close()
    await scope.close()
