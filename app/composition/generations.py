"""Immutable provider generation, capability lease, and pinned graph records.

Traces to: P6-T01, Gate G6
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from types import MappingProxyType
from uuid import UUID

from app.kernel.identifiers import CapabilityId, ProviderId, SemanticVersion


def configuration_digest(config: Mapping[str, object]) -> str:
    """Compute a deterministic SHA-256 hex digest of canonical JSON configuration.

    Args:
        config: Mapping of configuration key/values.

    Returns:
        64-character SHA-256 hexadecimal digest string.
    """
    canonical_json = json.dumps(
        config,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ProviderGeneration:
    """Immutable record of an activated provider instance generation."""

    provider_id: ProviderId
    generation_id: UUID
    version: SemanticVersion
    config_digest: str
    dependency_generation_ids: tuple[UUID, ...]
    activated_at: datetime

    def __post_init__(self) -> None:
        """Validate activated_at timezone and normalize dependency_generation_ids."""
        if self.activated_at.tzinfo != UTC:
            raise ValueError("activated_at must be timezone-aware UTC")
        # Ensure dependencies are sorted deterministically by hex
        sorted_deps = tuple(sorted(self.dependency_generation_ids, key=lambda u: u.hex))
        if self.dependency_generation_ids != sorted_deps:
            object.__setattr__(self, "dependency_generation_ids", sorted_deps)


@dataclass(frozen=True, slots=True)
class CapabilityLease[T]:
    """Typed lease granting direct access to an active capability instance."""

    capability_id: CapabilityId
    generation_id: UUID
    instance: T


@dataclass(frozen=True, slots=True)
class PinnedCapabilityGraph:
    """Immutable snapshot of generation records and capability leases."""

    generations: Mapping[ProviderId, ProviderGeneration]
    leases: Mapping[CapabilityId, CapabilityLease[object]]

    def __init__(
        self,
        generations: Mapping[ProviderId, ProviderGeneration],
        leases: Mapping[CapabilityId, CapabilityLease[object]],
    ) -> None:
        """Initialize PinnedCapabilityGraph with immutable mapping proxies.

        Args:
            generations: Mapping of ProviderId to ProviderGeneration.
            leases: Mapping of CapabilityId to CapabilityLease.

        Raises:
            ValueError: If duplicate provider IDs or inconsistent maps are detected.
        """
        seen_pids: set[ProviderId] = set()
        for pid in generations:
            if pid in seen_pids:
                raise ValueError(f"duplicate pinned provider: {pid}")
            seen_pids.add(pid)

        object.__setattr__(self, "generations", MappingProxyType(dict(generations)))
        object.__setattr__(self, "leases", MappingProxyType(dict(leases)))


__all__ = (
    "CapabilityLease",
    "PinnedCapabilityGraph",
    "ProviderGeneration",
    "configuration_digest",
)
