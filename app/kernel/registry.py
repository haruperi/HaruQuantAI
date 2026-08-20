"""Immutable inventory and index of discovered providers and capabilities.

Traces to: P4-T04, Gate G4
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from app.kernel.discovery import DiscoveredProvider
from app.kernel.errors import ResolutionError
from app.kernel.identifiers import CapabilityId, ProviderId
from app.kernel.manifests import ProviderManifest


@dataclass(frozen=True, slots=True)
class ProviderInventory:
    """Immutable catalog of providers indexed by provider ID and capability ID."""

    providers: tuple[ProviderManifest, ...]
    by_provider: Mapping[ProviderId, ProviderManifest]
    by_capability: Mapping[CapabilityId, tuple[ProviderManifest, ...]]


def build_inventory(
    discovered: tuple[DiscoveredProvider, ...],
) -> ProviderInventory:
    """Build an immutable provider inventory from discovered provider manifests.

    Args:
        discovered: Tuple of discovered providers.

    Returns:
        Immutable ProviderInventory catalog.

    Raises:
        ResolutionError: If duplicate provider IDs are present in input.
    """
    by_prov: dict[ProviderId, ProviderManifest] = {}
    by_cap_map: dict[CapabilityId, list[ProviderManifest]] = {}
    all_manifests: list[ProviderManifest] = []

    for d in discovered:
        manifest = d.manifest
        prov_id = manifest.provider_id

        if prov_id in by_prov:
            raise ResolutionError(f"duplicate provider id: {prov_id}")

        by_prov[prov_id] = manifest
        all_manifests.append(manifest)

        for provided in manifest.provides:
            by_cap_map.setdefault(provided.capability_id, []).append(manifest)

    # Sort all provider lists deterministically
    all_manifests.sort(key=lambda m: str(m.provider_id))

    frozen_by_cap: dict[CapabilityId, tuple[ProviderManifest, ...]] = {}
    for cap_id in sorted(by_cap_map.keys()):
        prov_list = by_cap_map[cap_id]
        prov_list.sort(key=lambda m: str(m.provider_id))
        frozen_by_cap[cap_id] = tuple(prov_list)

    return ProviderInventory(
        providers=tuple(all_manifests),
        by_provider=MappingProxyType(by_prov),
        by_capability=MappingProxyType(frozen_by_cap),
    )


__all__ = (
    "ProviderInventory",
    "build_inventory",
)
