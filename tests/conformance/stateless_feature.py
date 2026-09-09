"""Shared conformance checks for one-provider stateless backend features."""

from __future__ import annotations

import importlib.metadata
from dataclasses import dataclass
from typing import Any

from app.kernel.capability import CapabilityKey
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.feature import FeatureSpec
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope


@dataclass(frozen=True, slots=True)
class StatelessFeatureCase:
    """Feature-specific inputs for shared structural and lifecycle assertions."""

    factory: Any
    feature_type: type[Any]
    spec: FeatureSpec
    capability: CapabilityKey[Any]
    entry_point_name: str


def assert_factory_spec(case: StatelessFeatureCase) -> Any:
    """Assert factory identity, exact immutable spec, and discovery registration."""
    instance = case.factory()
    assert isinstance(instance, case.feature_type)
    assert instance.spec == case.spec
    assert case.capability in instance.spec.provides
    entry_points = importlib.metadata.entry_points(group="haruquantai.features")
    matching = [item for item in entry_points if item.name == case.entry_point_name]
    assert len(matching) == 1
    assert isinstance(matching[0].load()(), case.feature_type)
    return instance


async def mount_stateless_feature(
    case: StatelessFeatureCase, config: dict[str, Any] | None = None
) -> tuple[Any, ServiceRegistry, FeatureScope, Any]:
    """Mount a feature through its real scope and return the resolved provider."""
    instance = case.factory()
    registry = ServiceRegistry()
    scope = FeatureScope(owner_id=instance.spec.feature_id)

    def registrar(
        capability: CapabilityKey[Any], implementation: object, owner: FeatureScope
    ) -> None:
        registry.register(
            capability,
            implementation,
            owner_id=instance.spec.feature_id,
            scope=owner,
        )

    context = DefaultFeatureContext(
        spec=instance.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=registrar,
        event_bus=EventBus(),
    )
    await instance.mount(context, config or {})
    assert registry.is_available(case.capability)
    return instance, registry, scope, registry.require(case.capability)


async def assert_scoped_withdrawal(case: StatelessFeatureCase) -> None:
    """Assert closing the owner scope withdraws only the feature capability."""
    instance, registry, scope, _provider = await mount_stateless_feature(case)
    unrelated = CapabilityKey[str](name="conformance.unrelated", major=1)
    unrelated_scope = FeatureScope(owner_id="FEAT-CONFORMANCE-UNRELATED")
    registry.register(
        unrelated,
        "retained",
        owner_id=unrelated_scope.owner_id,
        scope=unrelated_scope,
    )

    await scope.close()

    assert not registry.is_available(case.capability)
    assert registry.resolve(case.capability) is None
    assert registry.resolve(unrelated) == "retained"
    assert instance.spec == case.spec
    await unrelated_scope.close()
