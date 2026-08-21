"""Dependency graph construction, cycle detection, and topological ordering."""

from collections import deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.kernel.feature import FeatureSpec


class DependencyError(RuntimeError):
    """Base exception for dependency graph errors."""


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
    """

    eligible_features: tuple[str, ...]
    start_order: tuple[str, ...]
    stop_order: tuple[str, ...]
    blocked_features: dict[str, str]
    provider_map: dict[str, str]


class DependencyGraph:
    """Analyzes and resolves feature capability dependencies."""

    def __init__(self, specs: Mapping[str, FeatureSpec]) -> None:
        """Initialize graph with feature specifications.

        Args:
            specs: Mapping of feature_id to FeatureSpec.
        """
        self._specs = dict(specs)

    def resolve(
        self,
        enabled_feature_ids: Iterable[str],
    ) -> GraphResolution:
        """Calculate eligible features and topological execution order.

        Args:
            enabled_feature_ids: Collection of feature IDs requested to run.

        Returns:
            GraphResolution with topological start/stop order and blocked reasons.

        Raises:
            DependencyCycleError: If an enabled required dependency cycle is found.
        """
        enabled_set = set(enabled_feature_ids)
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

        cap_to_provider = self._build_provider_map(candidates)
        eligible_set, eligibility_blocks = self._resolve_eligibility(candidates)
        blocked_features.update(eligibility_blocks)

        start_order = self._topological_sort(eligible_set, candidates, cap_to_provider)
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

    def _build_provider_map(
        self,
        candidates: Mapping[str, FeatureSpec],
    ) -> dict[str, str]:
        """Build mapping of capability identifier to primary provider.

        Args:
            candidates: Eligible candidate feature specs.

        Returns:
            Dictionary mapping capability identifier string to provider feature ID.
        """
        cap_to_provider: dict[str, str] = {}
        for f_id, spec in candidates.items():
            for cap in spec.provides:
                if cap.identifier not in cap_to_provider:
                    cap_to_provider[cap.identifier] = f_id
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
    ) -> tuple[str, ...]:
        """Perform topological sort on eligible features.

        Args:
            eligible_set: Set of eligible feature IDs.
            candidates: Candidate feature specs.
            cap_to_provider: Capability to provider mapping.

        Returns:
            Topologically ordered tuple of feature IDs (dependencies first).

        Raises:
            DependencyCycleError: If an unsatisfied required dependency cycle exists.
        """
        dependents: dict[str, set[str]] = {f_id: set() for f_id in eligible_set}
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

        return tuple(start_order)
