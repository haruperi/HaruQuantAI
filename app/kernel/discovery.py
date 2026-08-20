"""Static filesystem discovery of provider manifests.

Traces to: P4-T03, Gate G4
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.kernel.errors import ManifestValidationError
from app.kernel.identifiers import ProviderId
from app.kernel.manifests import ProviderManifest, load_manifest


@dataclass(frozen=True, slots=True)
class DiscoveredProvider:
    """Discovered manifest on disk and its parsed model."""

    manifest_path: Path
    manifest: ProviderManifest


def discover_manifests(root: Path) -> tuple[DiscoveredProvider, ...]:
    """Discover and parse first-party provider manifests under an explicit root directory.

    Args:
        root: Root directory to search for manifest.toml files.

    Returns:
        Sorted tuple of DiscoveredProvider instances.

    Raises:
        ManifestValidationError: If symlink escapes root or duplicate provider IDs exist.
    """
    if not root.exists() or not root.is_dir():
        return ()

    resolved_root = root.resolve()
    discovered_list: list[DiscoveredProvider] = []
    seen_provider_ids: dict[ProviderId, Path] = {}

    candidates = sorted(root.rglob("manifest.toml"))
    for candidate in candidates:
        rel = candidate.relative_to(root)
        if any(part.startswith(".") or part == "__pycache__" for part in rel.parts):
            continue

        resolved_candidate = candidate.resolve()
        try:
            resolved_candidate.relative_to(resolved_root)
        except ValueError:
            raise ManifestValidationError(
                f"invalid provider manifest {candidate}: manifest escapes discovery root"
            ) from None

        manifest = load_manifest(candidate)
        prov_id = manifest.provider_id

        if prov_id in seen_provider_ids:
            first_path = seen_provider_ids[prov_id]
            raise ManifestValidationError(
                f"invalid provider manifest {candidate}: duplicate provider id {prov_id} (first seen at {first_path})"
            )
        seen_provider_ids[prov_id] = candidate

        discovered_list.append(
            DiscoveredProvider(
                manifest_path=candidate,
                manifest=manifest,
            )
        )

    discovered_list.sort(
        key=lambda d: (str(d.manifest.provider_id), str(d.manifest_path))
    )
    return tuple(discovered_list)


__all__ = (
    "DiscoveredProvider",
    "discover_manifests",
)
