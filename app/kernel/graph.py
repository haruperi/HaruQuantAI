"""Dependency graph construction, provider selection, and lifecycle ordering."""

from __future__ import annotations

import heapq
from collections import deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.kernel.feature import FeatureSpec


class DependencyError(RuntimeError):
    """Base exception for dependency graph errors."""


class ProviderSelectionError(DependencyError, ValueError):
    """Raised when capability provider selection is invalid."""


class AmbiguousProviderError(ProviderSelectionError):
    """Raised when multiple providers exist without an explicit selection."""


class DependencyCycleError(DependencyError):
    """Raised when required capability dependencies contain a cycle."""

    def __init__(self, cycle: Sequence[str]) -> None:
        """Initialize the error with the cyclic feature path."""
        self.cycle = tuple(cycle)
        super().__init__(
            f"Circular required dependency detected: {' -> '.join(self.cycle)}"
        )


@dataclass(frozen=True, slots=True)
class GraphResolution:
    """Resolved feature eligibility, providers, and lifecycle ordering."""

    eligible_features: tuple[str, ...]
    start_order: tuple[str, ...]
    stop_order: tuple[str, ...]
    blocked_features: dict[str, str]
    provider_map: dict[str, str]
    dependencies: dict[str, set[str]] = field(default_factory=dict)
    dependents: dict[str, set[str]] = field(default_factory=dict)
    required_dependencies: dict[str, set[str]] = field(default_factory=dict)
    required_dependents: dict[str, set[str]] = field(default_factory=dict)
    optional_dependencies: dict[str, set[str]] = field(default_factory=dict)
    optional_dependents: dict[str, set[str]] = field(default_factory=dict)

    def get_transitive_dependents(
        self,
        feature_id: str,
        *,
        required_only: bool = False,
    ) -> set[str]:
        """Return all downstream consumers of a feature."""
        edges = self.required_dependents if required_only else self.dependents
        closure: set[str] = set()
        queue = deque([feature_id])
        while queue:
            current = queue.popleft()
            for dependent in edges.get(current, set()):
                if dependent not in closure:
                    closure.add(dependent)
                    queue.append(dependent)
        return closure

    def get_transitive_dependencies(
        self,
        feature_id: str,
        *,
        required_only: bool = False,
    ) -> set[str]:
        """Return all upstream providers used by a feature."""
        edges = self.required_dependencies if required_only else self.dependencies
        closure: set[str] = set()
        queue = deque([feature_id])
        while queue:
            current = queue.popleft()
            for provider in edges.get(current, set()):
                if provider not in closure:
                    closure.add(provider)
                    queue.append(provider)
        return closure


class DependencyGraph:
    """Resolve composable features using deterministic capability providers."""

    def __init__(
        self,
        specs: Mapping[str, FeatureSpec],
        provider_selections: Mapping[str, str] | None = None,
    ) -> None:
        """Initialize the graph from feature specifications."""
        self._specs = dict(specs)
        self._provider_selections = dict(provider_selections or {})

    def resolve(
        self,
        enabled_feature_ids: Iterable[str],
        provider_selections: Mapping[str, str] | None = None,
    ) -> GraphResolution:
        """Resolve providers, eligibility, and deterministic lifecycle order."""
        enabled_set = set(enabled_feature_ids)
        selections = dict(self._provider_selections)
        if provider_selections is not None:
            selections.update(provider_selections)

        available_specs = {
            feature_id: self._specs[feature_id]
            for feature_id in enabled_set
            if feature_id in self._specs
        }
        blocked = {
            feature_id: "Feature specification not found (MISSING)"
            for feature_id in enabled_set
            if feature_id not in self._specs
        }

        candidates, conflict_blocks = self._filter_conflicts(available_specs)
        blocked.update(conflict_blocks)

        providers_by_capability = self._collect_providers(candidates)
        self._validate_provider_selections(
            candidates,
            providers_by_capability,
            selections,
        )
        provider_map = self._select_providers(providers_by_capability, selections)
        candidates, unselected_blocks = self._suppress_unselected_providers(
            candidates,
            provider_map,
        )
        blocked.update(unselected_blocks)
        provider_map = {
            capability: provider
            for capability, provider in provider_map.items()
            if provider in candidates
        }

        self._detect_required_cycles(candidates, provider_map)
        eligible, eligibility_blocks = self._resolve_eligibility(
            candidates,
            provider_map,
        )
        blocked.update(eligibility_blocks)

        required_dependencies = self._build_dependencies(
            eligible,
            candidates,
            provider_map,
            optional=False,
        )
        optional_dependencies = self._build_dependencies(
            eligible,
            candidates,
            provider_map,
            optional=True,
        )
        required_dependents = self._reverse_edges(eligible, required_dependencies)
        optional_dependents = self._reverse_edges(eligible, optional_dependencies)

        required_order = self._topological_sort(eligible, required_dependencies)
        combined_dependencies = {
            feature_id: required_dependencies[feature_id]
            | optional_dependencies[feature_id]
            for feature_id in eligible
        }
        try:
            start_order = self._topological_sort(eligible, combined_dependencies)
        except DependencyCycleError:
            start_order = required_order

        combined_dependents = self._reverse_edges(eligible, combined_dependencies)
        active_provider_map = {
            capability: provider
            for capability, provider in provider_map.items()
            if provider in eligible
        }
        return GraphResolution(
            eligible_features=start_order,
            start_order=start_order,
            stop_order=tuple(reversed(start_order)),
            blocked_features=blocked,
            provider_map=active_provider_map,
            dependencies=combined_dependencies,
            dependents=combined_dependents,
            required_dependencies=required_dependencies,
            required_dependents=required_dependents,
            optional_dependencies=optional_dependencies,
            optional_dependents=optional_dependents,
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
                        f"Conflicts with enabled feature '{conflict_id}'"
                    )
        return (
            {
                feature_id: spec
                for feature_id, spec in available_specs.items()
                if feature_id not in conflicted
            },
            blocks,
        )

    def _collect_providers(
        self,
        candidates: Mapping[str, FeatureSpec],
    ) -> dict[str, tuple[str, ...]]:
        providers: dict[str, list[str]] = {}
        for feature_id in sorted(candidates):
            for capability in candidates[feature_id].provides:
                providers.setdefault(capability.identifier, []).append(feature_id)
        return {
            capability: tuple(sorted(feature_ids))
            for capability, feature_ids in providers.items()
        }

    def _validate_provider_selections(
        self,
        candidates: Mapping[str, FeatureSpec],
        providers_by_capability: Mapping[str, tuple[str, ...]],
        selections: Mapping[str, str],
    ) -> None:
        for capability, selected_feature in selections.items():
            if selected_feature not in candidates:
                raise ProviderSelectionError(
                    f"Selected provider '{selected_feature}' for capability "
                    f"'{capability}' is not among enabled candidate features "
                    "(it is disabled or was not discovered)"
                )
            selected_spec = candidates[selected_feature]
            if not any(
                provided.identifier == capability
                for provided in selected_spec.provides
            ):
                raise ProviderSelectionError(
                    f"Selected provider '{selected_feature}' does not provide "
                    f"capability '{capability}'"
                )
            if capability not in providers_by_capability:
                raise ProviderSelectionError(
                    f"No enabled feature provides selected capability '{capability}'"
                )

    def _select_providers(
        self,
        providers_by_capability: Mapping[str, tuple[str, ...]],
        selections: Mapping[str, str],
    ) -> dict[str, str]:
        provider_map: dict[str, str] = {}
        for capability, provider_ids in sorted(providers_by_capability.items()):
            selected = selections.get(capability)
            if selected is not None:
                if selected not in provider_ids:
                    raise ProviderSelectionError(
                        f"Selected provider '{selected}' for capability '{capability}' "
                        f"is not among enabled candidates {list(provider_ids)}"
                    )
                provider_map[capability] = selected
            elif len(provider_ids) == 1:
                provider_map[capability] = provider_ids[0]
            else:
                raise AmbiguousProviderError(
                    f"Ambiguous capability providers for '{capability}': "
                    f"{list(provider_ids)}. Configure an explicit selection in "
                    "[providers]."
                )
        return provider_map

    def _suppress_unselected_providers(
        self,
        candidates: Mapping[str, FeatureSpec],
        provider_map: Mapping[str, str],
    ) -> tuple[dict[str, FeatureSpec], dict[str, str]]:
        suppressed: set[str] = set()
        blocks: dict[str, str] = {}
        for feature_id, spec in candidates.items():
            provided = {capability.identifier for capability in spec.provides}
            selected = {
                capability
                for capability in provided
                if provider_map.get(capability) == feature_id
            }
            unselected = {
                capability
                for capability in provided
                if provider_map.get(capability) not in {None, feature_id}
            }
            if not unselected:
                continue
            if selected:
                raise ProviderSelectionError(
                    f"Feature '{feature_id}' is selected for {sorted(selected)} but "
                    f"unselected for {sorted(unselected)}. Capability bundles are "
                    "atomic; select one feature consistently for every overlapping "
                    "capability."
                )
            suppressed.add(feature_id)
            blocks[feature_id] = (
                "Provider feature not selected for: "
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

    def _required_adjacency(
        self,
        candidates: Mapping[str, FeatureSpec],
        provider_map: Mapping[str, str],
    ) -> dict[str, set[str]]:
        adjacency: dict[str, set[str]] = {
            feature_id: set() for feature_id in candidates
        }
        for consumer_id, spec in candidates.items():
            for capability in spec.requires:
                provider_id = provider_map.get(capability.identifier)
                if provider_id is not None and provider_id != consumer_id:
                    adjacency[consumer_id].add(provider_id)
        return adjacency

    def _detect_required_cycles(
        self,
        candidates: Mapping[str, FeatureSpec],
        provider_map: Mapping[str, str],
    ) -> None:
        adjacency = self._required_adjacency(candidates, provider_map)
        visiting: set[str] = set()
        visited: set[str] = set()
        path: list[str] = []

        def visit(node: str) -> None:
            if node in visited:
                return
            if node in visiting:
                cycle_start = path.index(node)
                raise DependencyCycleError((*path[cycle_start:], node))
            visiting.add(node)
            path.append(node)
            for provider in sorted(adjacency[node]):
                visit(provider)
            path.pop()
            visiting.remove(node)
            visited.add(node)

        for feature_id in sorted(adjacency):
            visit(feature_id)

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

    def _build_dependencies(
        self,
        eligible: set[str],
        candidates: Mapping[str, FeatureSpec],
        provider_map: Mapping[str, str],
        *,
        optional: bool,
    ) -> dict[str, set[str]]:
        dependencies: dict[str, set[str]] = {
            feature_id: set() for feature_id in eligible
        }
        for consumer_id in eligible:
            capabilities = (
                candidates[consumer_id].optional
                if optional
                else candidates[consumer_id].requires
            )
            for capability in capabilities:
                provider_id = provider_map.get(capability.identifier)
                if (
                    provider_id is not None
                    and provider_id in eligible
                    and provider_id != consumer_id
                ):
                    dependencies[consumer_id].add(provider_id)
        return dependencies

    def _reverse_edges(
        self,
        nodes: set[str],
        dependencies: Mapping[str, set[str]],
    ) -> dict[str, set[str]]:
        dependents: dict[str, set[str]] = {feature_id: set() for feature_id in nodes}
        for consumer_id, provider_ids in dependencies.items():
            for provider_id in provider_ids:
                dependents[provider_id].add(consumer_id)
        return dependents

    def _topological_sort(
        self,
        nodes: set[str],
        dependencies: Mapping[str, set[str]],
    ) -> tuple[str, ...]:
        in_degree = {
            feature_id: len(dependencies.get(feature_id, set()))
            for feature_id in nodes
        }
        dependents = self._reverse_edges(nodes, dependencies)
        queue = [
            feature_id
            for feature_id in nodes
            if in_degree[feature_id] == 0
        ]
        heapq.heapify(queue)
        order: list[str] = []
        while queue:
            feature_id = heapq.heappop(queue)
            order.append(feature_id)
            for dependent in sorted(dependents[feature_id]):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    heapq.heappush(queue, dependent)

        if len(order) != len(nodes):
            unresolved = sorted(
                feature_id
                for feature_id in nodes
                if in_degree[feature_id] > 0
            )
            raise DependencyCycleError(unresolved)
        return tuple(order)
