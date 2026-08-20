"""Transactional configuration reconciliation for installed providers.

Traces to: P6-T03, Phase 6, Phase 17, Gate G6
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING
from uuid import UUID

from app.composition.generations import configuration_digest
from app.kernel.errors import ManifestValidationError
from app.kernel.identifiers import CapabilityId, ProviderId
from app.kernel.resolver import resolve_providers
from app.utils.logging import get_logger

if TYPE_CHECKING:
    from app.composition.runtime import CompositionRuntime
    from app.kernel.lifecycle import ProviderFactory
    from app.kernel.registry import ProviderInventory

_logger = get_logger("app.composition.reconciliation")


@dataclass(frozen=True, slots=True)
class ProviderConfiguration:
    """Declared runtime configuration for enabled providers, selections, and parameters."""

    enabled_provider_ids: frozenset[ProviderId]
    selected_provider_ids: Mapping[CapabilityId, ProviderId]
    provider_configs: Mapping[ProviderId, Mapping[str, object]]

    def __init__(
        self,
        *,
        enabled_provider_ids: frozenset[ProviderId] = frozenset(),
        selected_provider_ids: Mapping[CapabilityId, ProviderId] | None = None,
        provider_configs: Mapping[ProviderId, Mapping[str, object]] | None = None,
    ) -> None:
        """Initialize immutable ProviderConfiguration."""
        object.__setattr__(
            self, "enabled_provider_ids", frozenset(enabled_provider_ids)
        )
        object.__setattr__(
            self,
            "selected_provider_ids",
            MappingProxyType(dict(selected_provider_ids or {})),
        )
        frozen_configs = {
            pid: MappingProxyType(dict(cfg))
            for pid, cfg in (provider_configs or {}).items()
        }
        object.__setattr__(self, "provider_configs", MappingProxyType(frozen_configs))


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    """Outcome of a provider configuration reconciliation execution."""

    changed_provider_ids: tuple[ProviderId, ...]
    activated_generation_ids: tuple[UUID, ...]
    rolled_back: bool


def reconcile_configuration(
    runtime: CompositionRuntime,
    inventory: ProviderInventory,
    current: ProviderConfiguration,
    candidate: ProviderConfiguration,
    *,
    factories: Mapping[ProviderId, ProviderFactory],
) -> ReconciliationResult:
    """Compute and apply configuration reconciliation among installed providers only.

    Args:
        runtime: Active CompositionRuntime instance.
        inventory: Discovered and registered ProviderInventory.
        current: Active/incumbent ProviderConfiguration.
        candidate: Proposed candidate ProviderConfiguration.
        factories: Mapping of ProviderId to ProviderFactory callable.

    Returns:
        ReconciliationResult detailing changed IDs, activated generations, and rollback status.

    Raises:
        ManifestValidationError: If any candidate provider is not in inventory.
        LifecycleError: If candidate fails and incumbent cannot be restored.
    """
    # 1. Enforce candidate only references installed providers
    installed_pids = set(inventory.by_provider.keys())
    for pid in candidate.enabled_provider_ids:
        if pid not in installed_pids:
            msg = f"provider is not installed: {pid}"
            raise ManifestValidationError(msg)

    for pid in candidate.selected_provider_ids.values():
        if pid not in installed_pids:
            msg = f"provider is not installed: {pid}"
            raise ManifestValidationError(msg)

    for pid in candidate.provider_configs:
        if pid not in installed_pids:
            msg = f"provider is not installed: {pid}"
            raise ManifestValidationError(msg)

    # 2. Compute changed providers
    changed: set[ProviderId] = set()

    # Enabled set differences
    changed.update(
        current.enabled_provider_ids.symmetric_difference(
            candidate.enabled_provider_ids
        )
    )

    # Selection differences
    all_selected_caps = set(current.selected_provider_ids.keys()) | set(
        candidate.selected_provider_ids.keys()
    )
    for cap_id in all_selected_caps:
        cur_sel = current.selected_provider_ids.get(cap_id)
        cand_sel = candidate.selected_provider_ids.get(cap_id)
        if cur_sel != cand_sel:
            if cur_sel is not None:
                changed.add(cur_sel)
            if cand_sel is not None:
                changed.add(cand_sel)

    # Configuration differences (via digest)
    all_config_pids = set(current.provider_configs.keys()) | set(
        candidate.provider_configs.keys()
    )
    for pid in all_config_pids:
        cur_cfg = current.provider_configs.get(pid, {})
        cand_cfg = candidate.provider_configs.get(pid, {})
        if configuration_digest(cur_cfg) != configuration_digest(cand_cfg):
            changed.add(pid)

    if not changed and current.enabled_provider_ids == candidate.enabled_provider_ids:
        return ReconciliationResult(
            changed_provider_ids=(),
            activated_generation_ids=(),
            rolled_back=False,
        )

    _logger.info("Reconciling %d affected provider(s)", len(changed))

    # 3. Resolve candidate
    candidate_report = resolve_providers(
        inventory.providers,
        enabled_provider_ids=candidate.enabled_provider_ids,
        selected_provider_ids=candidate.selected_provider_ids,
    )

    # 4. Activate candidate with automatic fallback on failure
    try:
        gens = runtime.activate(
            candidate_report,
            factories=factories,
            configs=candidate.provider_configs,
        )
        return ReconciliationResult(
            changed_provider_ids=tuple(sorted(changed, key=str)),
            activated_generation_ids=tuple(g.generation_id for g in gens),
            rolled_back=False,
        )
    except Exception:
        _logger.error("Provider reconciliation failed; restoring incumbent graph")
        # Reactivate incumbent
        incumbent_report = resolve_providers(
            inventory.providers,
            enabled_provider_ids=current.enabled_provider_ids,
            selected_provider_ids=current.selected_provider_ids,
        )
        runtime.activate(
            incumbent_report,
            factories=factories,
            configs=current.provider_configs,
        )
        return ReconciliationResult(
            changed_provider_ids=(),
            activated_generation_ids=(),
            rolled_back=True,
        )


__all__ = (
    "ProviderConfiguration",
    "ReconciliationResult",
    "reconcile_configuration",
)
