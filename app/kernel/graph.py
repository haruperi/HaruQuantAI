"""Dependency graph construction, cycle detection, and topological ordering."""

from collections import deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.kernel.feature import FeatureSpec


class DependencyError(RuntimeError):
    """Base exception for dependency graph errors."""


class ProviderSelectionError(DependencyError, ValueError):
    """Raised when capability provider selection is invalid or fails validation."""


class AmbiguousProviderError(ProviderSelectionError):
    """Raised when multiple candidate providers exist without explicit selection."""


class DependencyCycleError(DependencyError):
    """Raised when a circular dependency is detected among required capabilities.

    Attributes:
        cycle: Sequence of feature IDs involved in the cycle.
    """

    def __init__(self, cycle: Sequence[str]) -> None:
        """Initialize cycle error.

        Args:
            cycle: Sequence of cyclic feature identifiers.
        """
        self.cycle = tuple(cycle)
        cycle_str = " -> ".join(self.cycle)
        super().__init__(f"Circular required dependency detected: {cycle_str}")


@dataclass(frozen=True, slots=True)
class GraphResolution:
    """Calculated dependency resolution and execution orders.

    Attributes:
        eligible_features: Tuple of feature IDs eligible for activation.
        start_order: Ordered tuple of feature IDs to start (dependencies first).
        stop_order: Ordered tuple of feature IDs to stop (dependents first).
        blocked_features: Mapping of feature ID to reason/missing capability.
        provider_map: Mapping of capability identifier to providing feature ID.
        dependencies: Mapping of feature ID to direct provider feature IDs.
        dependents: Mapping of feature ID to direct consumer feature IDs.
    """

    eligible_features: tuple[str, ...]
    start_order: tuple[str, ...]
    stop_order: tuple[str, ...]
    blocked_features: dict[str, str]
    provider_map: dict[str, str]
    dependencies: dict[str, set[str]] = field(default_factory=dict)
    dependents: dict[str, set[str]] = field(default_factory=dict)

    def get_transitive_dependents(self, feature_id: str) -> set[str]:
        """Calculate all transitive downstream consumers of a feature.

        Args:
            feature_id: Unique feature identifier.

        Returns:
            Set of feature IDs that transitively depend on this feature.
        """
        closure: set[str] = set()
        queue = deque([feature_id])
        while queue:
            curr = queue.popleft()
            for dep in self.dependents.get(curr, set()):
                if dep not in closure:
                    closure.add(dep)
                    queue.append(dep)
        return closure

    def get_transitive_dependencies(self, feature_id: str) -> set[str]:
        """Calculate all transitive upstream providers of a feature.

        Args:
            feature_id: Unique feature identifier.

        Returns:
            Set of feature IDs that this feature transitively depends on.
        """
        closure: set[str] = set()
        queue = deque([feature_id])
        while queue:
            curr = queue.popleft()
            for provider in self.dependencies.get(curr, set()):
                if provider not in closure:
                    closure.add(provider)
                    queue.append(provider)
        return closure


class DependencyGraph:
    """Analyzes and resolves feature capability dependencies."""

    def __init__(
        self,
        specs: Mapping[str, FeatureSpec],
        provider_selections: Mapping[str, str] | None = None,
    ) -> None:
        """Initialize graph with feature specifications and provider selections.

        Args:
            specs: Mapping of feature_id to FeatureSpec.
            provider_selections: Optional capability-to-provider mappings.
        """
        self._specs = dict(specs)
        self._provider_selections = dict(provider_selections or {})

    def resolve(
        self,
        enabled_feature_ids: Iterable[str],
        provider_selections: Mapping[str, str] | None = None,
    ) -> GraphResolution:
        """Calculate eligible features and topological execution order.

        Args:
            enabled_feature_ids: Collection of feature IDs requested to run.
            provider_selections: Optional override provider selections.

        Returns:
            GraphResolution with topological start/stop order and blocked reasons.

        Raises:
            AmbiguousProviderError: If multiple enabled features provide a capability.
            ProviderSelectionError: If an explicit selection is invalid or incompatible.
            DependencyCycleError: If an enabled required dependency cycle is found.
        """
        enabled_set = set(enabled_feature_ids)
        effective_selections = dict(self._provider_selections)
        if provider_selections is not None:
            effective_selections.update(provider_selections)

        available_specs = {
            f_id: self._specs[f_id] for f_id in enabled_set if f_id in self._specs
        }
        blocked_features = {
            f_id: "Feature specification not found (MISSING)"
            for f_id in enabled_set
            if f_id not in self._specs
        }

        candidates, conflict_blocks = self._filter_conflicts(available_specs)
        blocked_features.update(conflict_blocks)

        cap_to_provider = self._build_provider_map(candidates, effective_selections)
        self._detect_required_cycles(candidates, cap_to_provider)

        eligible_set, eligibility_blocks = self._resolve_eligibility(candidates)
        blocked_features.update(eligibility_blocks)

        start_order, dependencies, dependents = self._topological_sort(
            eligible_set, candidates, cap_to_provider
        )
        stop_order = tuple(reversed(start_order))

        return GraphResolution(
            eligible_features=start_order,
            start_order=start_order,
            stop_order=stop_order,
            blocked_features=blocked_features,
            provider_map={
                cap: p_id
                for cap, p_id in cap_to_provider.items()
                if p_id in eligible_set
            },
            dependencies=dependencies,
            dependents=dependents,
        )

    def _filter_conflicts(
        self,
        available_specs: Mapping[str, FeatureSpec],
    ) -> tuple[dict[str, FeatureSpec], dict[str, str]]:
        """Filter out conflicting features.

        Args:
            available_specs: Available feature specs.

        Returns:
            Tuple of non-conflicting candidates map and conflict block reasons map.
        """
        conflicted: set[str] = set()
        conflict_blocks: dict[str, str] = {}

        for f_id, spec in available_specs.items():
            for conflict_id in spec.conflicts:
                if conflict_id in available_specs and conflict_id != f_id:
                    conflicted.add(f_id)
                    conflict_blocks[f_id] = (
                        f"Conflicts with active feature '{conflict_id}'"
                    )

        candidates = {
            f_id: spec
            for f_id, spec in available_specs.items()
            if f_id not in conflicted
        }
        return candidates, conflict_blocks

    def _detect_required_cycles(
        self,
        candidates: Mapping[str, FeatureSpec],
        cap_to_provider: Mapping[str, str],
    ) -> None:
        """Detect circular dependencies exclusively among required capabilities.

        Args:
            candidates: Candidate feature specs.
            cap_to_provider: Map of capability identifier to provider feature ID.

        Raises:
            DependencyCycleError: If a required dependency cycle is detected.
        """
        adj: dict[str, set[str]] = {f_id: set() for f_id in candidates}
        for f_id, spec in candidates.items():
            for cap in spec.requires:
                provider_id = cap_to_provider.get(cap.identifier)
                if provider_id and provider_id in candidates and provider_id != f_id:
                    adj[f_id].add(provider_id)

        visited: dict[str, int] = {}
        path: list[str] = []

        def dfs(node: str) -> None:
            visited[node] = 1
            path.append(node)
            for neighbor in sorted(adj.get(node, ())):
                if visited.get(neighbor) == 1:
                    cycle_start = path.index(neighbor)
                    cycle = [*path[cycle_start:], neighbor]
                    raise DependencyCycleError(cycle)
                if visited.get(neighbor, 0) == 0:
                    dfs(neighbor)
            path.pop()
            visited[node] = 2

        for node in sorted(candidates.keys()):
            if visited.get(node, 0) == 0:
                dfs(node)

    def _resolve_single_capability_provider(
        self,
        cap_id: str,
        provider_list: list[str],
        provider_selections: Mapping[str, str],
    ) -> str:
        """Resolve a single capability's provider, checking for ambiguity.

        Args:
            cap_id: Formatted capability identifier.
            provider_list: List of candidate feature IDs providing this capability.
            provider_selections: Explicit provider selections from configuration.

        Returns:
            Chosen feature ID providing the capability.

        Raises:
            AmbiguousProviderError: If multiple providers exist without selection.
            ProviderSelectionError: If the configured selection is not a candidate.
        """
        if len(provider_list) == 1:
            return provider_list[0]

        selected = provider_selections.get(cap_id)
        if selected is None:
            candidates_str = ", ".join(sorted(provider_list))
            msg = (
                f"Ambiguous capability providers for '{cap_id}': "
                f"multiple enabled candidates found [{candidates_str}]. "
                f"Explicit selection required in [providers]."
            )
            raise AmbiguousProviderError(msg)

        if selected not in provider_list:
            candidates_str = ", ".join(sorted(provider_list))
            msg = (
                f"Selected provider '{selected}' for capability '{cap_id}' "
                f"is not among enabled candidate providers [{candidates_str}]."
            )
            raise ProviderSelectionError(msg)

        return selected

    def _build_provider_map(
        self,
        candidates: Mapping[str, FeatureSpec],
        provider_selections: Mapping[str, str],
    ) -> dict[str, str]:
        """Build mapping of capability identifier to primary provider.

        Args:
            candidates: Eligible candidate feature specs.
            provider_selections: Mapping of capability to selected provider feature ID.

        Returns:
            Dictionary mapping capability identifier string to provider feature ID.

        Raises:
            AmbiguousProviderError: If multiple features provide a capability.
            ProviderSelectionError: If selected provider is invalid.
        """
        providers_by_cap: dict[str, list[str]] = {}
        for f_id, spec in candidates.items():
            for cap in spec.provides:
                providers_by_cap.setdefault(cap.identifier, []).append(f_id)

        cap_to_provider: dict[str, str] = {}
        for cap_id, provider_list in providers_by_cap.items():
            chosen = self._resolve_single_capability_provider(
                cap_id, provider_list, provider_selections
            )
            cap_to_provider[cap_id] = chosen

        # Validate explicit selections for candidate features
        for cap_id, selected_id in provider_selections.items():
            if selected_id in candidates:
                spec = candidates[selected_id]
                if not any(c.identifier == cap_id for c in spec.provides):
                    msg = (
                        f"Selected provider '{selected_id}' does not provide "
                        f"capability '{cap_id}'"
                    )
                    raise ProviderSelectionError(msg)

        return cap_to_provider

    def _resolve_eligibility(
        self,
        candidates: Mapping[str, FeatureSpec],
    ) -> tuple[set[str], dict[str, str]]:
        """Determine eligible features through iterative fixed-point resolution.

        Args:
            candidates: Candidate feature specs.

        Returns:
            Tuple of eligible feature ID set and blocked features reason map.
        """
        eligible_set: set[str] = set()
        available_caps: set[str] = set()
        changed = True

        while changed:
            changed = False
            for f_id, spec in candidates.items():
                if f_id in eligible_set:
                    continue
                missing_reqs = [
                    cap.identifier
                    for cap in spec.requires
                    if cap.identifier not in available_caps
                ]
                if not missing_reqs:
                    eligible_set.add(f_id)
                    for cap in spec.provides:
                        available_caps.add(cap.identifier)
                    changed = True

        blocks: dict[str, str] = {}
        for f_id, spec in candidates.items():
            if f_id not in eligible_set:
                missing_reqs = [
                    cap.identifier
                    for cap in spec.requires
                    if cap.identifier not in available_caps
                ]
                if missing_reqs:
                    blocks[f_id] = (
                        f"Missing required capabilities: {', '.join(missing_reqs)}"
                    )
                else:
                    blocks[f_id] = "Unsatisfied dependencies or dependency cycle"

        return eligible_set, blocks

    def _topological_sort(
        self,
        eligible_set: set[str],
        candidates: Mapping[str, FeatureSpec],
        cap_to_provider: Mapping[str, str],
    ) -> tuple[tuple[str, ...], dict[str, set[str]], dict[str, set[str]]]:
        """Perform topological sort on eligible features.

        Args:
            eligible_set: Set of eligible feature IDs.
            candidates: Candidate feature specs.
            cap_to_provider: Capability to provider mapping.

        Returns:
            Tuple of (start_order tuple, dependencies map, dependents map).

        Raises:
            DependencyCycleError: If an unsatisfied required dependency cycle exists.
        """
        dependents: dict[str, set[str]] = {f_id: set() for f_id in eligible_set}
        dependencies: dict[str, set[str]] = {f_id: set() for f_id in eligible_set}
        in_degree: dict[str, int] = dict.fromkeys(eligible_set, 0)

        for f_id in eligible_set:
            spec = candidates[f_id]
            all_deps = tuple(spec.requires) + tuple(spec.optional)
            for cap in all_deps:
                provider_id = cap_to_provider.get(cap.identifier)
                if (
                    provider_id
                    and provider_id in eligible_set
                    and provider_id != f_id
                    and f_id not in dependents[provider_id]
                ):
                    dependents[provider_id].add(f_id)
                    dependencies[f_id].add(provider_id)
                    in_degree[f_id] += 1

        queue = deque([f_id for f_id in eligible_set if in_degree[f_id] == 0])
        start_order: list[str] = []

        while queue:
            node = queue.popleft()
            start_order.append(node)
            for dep in dependents[node]:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

        if len(start_order) != len(eligible_set):
            unresolved = [f_id for f_id in eligible_set if in_degree[f_id] > 0]
            raise DependencyCycleError(unresolved)

        return tuple(start_order), dependencies, dependents
