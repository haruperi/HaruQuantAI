"""Dependency graph construction, cycle detection, and deterministic provider selection."""

from collections import deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.kernel.feature import FeatureSpec


class DependencyError(RuntimeError):
    """Base exception for dependency graph errors."""


class DependencyCycleError(DependencyError):
    """Raised when a circular required-capability dependency is detected."""

    def __init__(self, cycle: Sequence[str]) -> None:
        self.cycle = tuple(cycle)
        super().__init__(
            f"Circular required dependency detected: {' -> '.join(self.cycle)}"
        )


class AmbiguousProviderError(DependencyError):
    """Raised when multiple enabled providers exist without explicit selection."""

    def __init__(self, capability: str, providers: Sequence[str]) -> None:
        self.capability = capability
        self.providers = tuple(sorted(providers))
        super().__init__(
            f"Capability '{capability}' has multiple enabled providers: "
            f"{', '.join(self.providers)}. Configure an explicit provider selection."
        )


class InvalidProviderSelectionError(DependencyError):
    """Raised when configured provider selection cannot be honored safely."""


@dataclass(frozen=True, slots=True)
class GraphResolution:
    """Calculated dependency resolution and execution orders."""

    eligible_features: tuple[str, ...]
    start_order: tuple[str, ...]
    stop_order: tuple[str, ...]
    blocked_features: dict[str, str]
    provider_map: dict[str, str]


class DependencyGraph:
    """Analyze feature capability dependencies deterministically."""

    def __init__(self, specs: Mapping[str, FeatureSpec]) -> None:
        self._specs = dict(specs)

    def resolve(
        self,
        enabled_feature_ids: Iterable[str],
        provider_selection: Mapping[str, str] | None = None,
    ) -> GraphResolution:
        """Calculate eligible features and deterministic start/stop order."""
        enabled_set = set(enabled_feature_ids)
        available_specs = {
            feature_id: self._specs[feature_id]
            for feature_id in enabled_set
            if feature_id in self._specs
        }
        blocked_features = {
            feature_id: "Feature specification not found (MISSING)"
            for feature_id in enabled_set
            if feature_id not in self._specs
        }

        candidates, conflict_blocks = self._filter_conflicts(available_specs)
        blocked_features.update(conflict_blocks)

        provider_map = self._build_provider_map(
            candidates,
            provider_selection or {},
        )
        candidates, selection_blocks = self._suppress_unselected_providers(
            candidates,
            provider_map,
        )
        blocked_features.update(selection_blocks)
        provider_map = {
            capability: provider
            for capability, provider in provider_map.items()
            if provider in candidates
        }

        self._detect_required_cycles(candidates, provider_map)
        eligible_set, eligibility_blocks = self._resolve_eligibility(
            candidates,
            provider_map,
        )
        blocked_features.update(eligibility_blocks)
        start_order = self._topological_sort_required(
            eligible_set,
            candidates,
            provider_map,
        )
        return GraphResolution(
            eligible_features=start_order,
            start_order=start_order,
            stop_order=tuple(reversed(start_order)),
            blocked_features=blocked_features,
            provider_map={
                capability: provider
                for capability, provider in provider_map.items()
                if provider in eligible_set
            },
        )

    def _filter_conflicts(
        self,
        available_specs: Mapping[str, FeatureSpec],
    ) -> tuple[dict[str, FeatureSpec], dict[str, str]]:
        conflicted: set[str] = set()
        blocks: dict[str, str] = {}
        for feature_id, spec in available_specs.items():
            for conflict_id in spec.conflicts:
                if conflict_id in available_specs and conflict_id != feature_id:
                    conflicted.add(feature_id)
                    blocks[feature_id] = (
                        f"Conflicts with active feature '{conflict_id}'"
                    )
        return (
            {
                feature_id: spec
                for feature_id, spec in available_specs.items()
                if feature_id not in conflicted
            },
            blocks,
        )

    def _build_provider_map(
        self,
        candidates: Mapping[str, FeatureSpec],
        provider_selection: Mapping[str, str],
    ) -> dict[str, str]:
        providers: dict[str, list[str]] = {}
        for feature_id in sorted(candidates):
            for capability in candidates[feature_id].provides:
                providers.setdefault(capability.identifier, []).append(feature_id)

        result: dict[str, str] = {}
        for capability, feature_ids in providers.items():
            configured = provider_selection.get(capability)
            if configured is not None:
                if configured not in feature_ids:
                    msg = (
                        f"Configured provider '{configured}' does not provide enabled "
                        f"capability '{capability}'"
                    )
                    raise InvalidProviderSelectionError(msg)
                result[capability] = configured
            elif len(feature_ids) == 1:
                result[capability] = feature_ids[0]
            else:
                raise AmbiguousProviderError(capability, feature_ids)

        for capability, configured in provider_selection.items():
            if capability not in providers:
                msg = (
                    f"Configured provider '{configured}' targets unavailable capability "
                    f"'{capability}'"
                )
                raise InvalidProviderSelectionError(msg)
        return result

    def _suppress_unselected_providers(
        self,
        candidates: Mapping[str, FeatureSpec],
        provider_map: Mapping[str, str],
    ) -> tuple[dict[str, FeatureSpec], dict[str, str]]:
        """Prevent unselected providers from mounting and overwriting registry bindings."""
        suppressed: set[str] = set()
        blocks: dict[str, str] = {}
        for feature_id, spec in candidates.items():
            provided = {cap.identifier for cap in spec.provides}
            selected = {cap for cap in provided if provider_map.get(cap) == feature_id}
            unselected = {
                cap
                for cap in provided
                if cap in provider_map and provider_map[cap] != feature_id
            }
            if not unselected:
                continue
            if selected:
                msg = (
                    f"Feature '{feature_id}' is selected for {sorted(selected)} but "
                    f"unselected for {sorted(unselected)}. Provider bundles are atomic; "
                    "select one feature consistently for every overlapping capability."
                )
                raise InvalidProviderSelectionError(msg)
            suppressed.add(feature_id)
            blocks[feature_id] = (
                "Provider not selected for capability bundle: "
                + ", ".join(sorted(unselected))
            )
        return (
            {
                feature_id: spec
                for feature_id, spec in candidates.items()
                if feature_id not in suppressed
            },
            blocks,
        )

    def _required_edges(
        self,
        candidates: Mapping[str, FeatureSpec],
        provider_map: Mapping[str, str],
    ) -> dict[str, set[str]]:
        edges: dict[str, set[str]] = {feature_id: set() for feature_id in candidates}
        for consumer_id, spec in candidates.items():
            for capability in spec.requires:
                provider_id = provider_map.get(capability.identifier)
                if provider_id is not None and provider_id != consumer_id:
                    edges[provider_id].add(consumer_id)
        return edges

    def _detect_required_cycles(
        self,
        candidates: Mapping[str, FeatureSpec],
        provider_map: Mapping[str, str],
    ) -> None:
        edges = self._required_edges(candidates, provider_map)
        visiting: set[str] = set()
        visited: set[str] = set()
        stack: list[str] = []

        def visit(node: str) -> None:
            if node in visited:
                return
            if node in visiting:
                start = stack.index(node)
                raise DependencyCycleError((*stack[start:], node))
            visiting.add(node)
            stack.append(node)
            for child in sorted(edges[node]):
                visit(child)
            stack.pop()
            visiting.remove(node)
            visited.add(node)

        for node in sorted(edges):
            visit(node)

    def _resolve_eligibility(
        self,
        candidates: Mapping[str, FeatureSpec],
        provider_map: Mapping[str, str],
    ) -> tuple[set[str], dict[str, str]]:
        eligible: set[str] = set()
        changed = True
        while changed:
            changed = False
            for feature_id in sorted(candidates):
                if feature_id in eligible:
                    continue
                missing = [
                    capability.identifier
                    for capability in candidates[feature_id].requires
                    if provider_map.get(capability.identifier) not in eligible
                ]
                if not missing:
                    eligible.add(feature_id)
                    changed = True

        blocks: dict[str, str] = {}
        for feature_id in sorted(candidates):
            if feature_id in eligible:
                continue
            missing = [
                capability.identifier
                for capability in candidates[feature_id].requires
                if provider_map.get(capability.identifier) not in eligible
            ]
            blocks[feature_id] = (
                f"Missing required capabilities: {', '.join(missing)}"
                if missing
                else "Unsatisfied required dependencies"
            )
        return eligible, blocks

    def _topological_sort_required(
        self,
        eligible_set: set[str],
        candidates: Mapping[str, FeatureSpec],
        provider_map: Mapping[str, str],
    ) -> tuple[str, ...]:
        dependents: dict[str, set[str]] = {
            feature_id: set() for feature_id in eligible_set
        }
        in_degree: dict[str, int] = dict.fromkeys(eligible_set, 0)
        for consumer_id in eligible_set:
            for capability in candidates[consumer_id].requires:
                provider_id = provider_map.get(capability.identifier)
                if (
                    provider_id in eligible_set
                    and provider_id != consumer_id
                    and consumer_id not in dependents[provider_id]
                ):
                    dependents[provider_id].add(consumer_id)
                    in_degree[consumer_id] += 1

        queue = deque(
            sorted(
                feature_id
                for feature_id in eligible_set
                if in_degree[feature_id] == 0
            )
        )
        order: list[str] = []
        while queue:
            node = queue.popleft()
            order.append(node)
            for consumer_id in sorted(dependents[node]):
                in_degree[consumer_id] -= 1
                if in_degree[consumer_id] == 0:
                    queue.append(consumer_id)

        if len(order) != len(eligible_set):
            unresolved = sorted(
                feature_id for feature_id in eligible_set if in_degree[feature_id] > 0
            )
            raise DependencyCycleError(unresolved)
        return tuple(order)
