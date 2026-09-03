"""Static filesystem provider manifest discovery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.composition.logging import log_debug
from app.kernel.errors import ManifestValidationError
from app.kernel.manifests import ProviderManifest, load_manifest


@dataclass(frozen=True, slots=True)
class DiscoveredProvider:
    """Represents a discovered provider manifest on the filesystem."""

    manifest_path: Path
    manifest: ProviderManifest


def discover_manifests(root: str | Path) -> tuple[DiscoveredProvider, ...]:
    """Discover all provider manifests under the specified directory root.

    Args:
        root: Root directory to search for manifest.toml files.

    Returns:
        Sorted tuple of DiscoveredProvider records.
    """
    root_resolved = Path(root).resolve()
    if not root_resolved.exists():
        return ()

    discovered: list[DiscoveredProvider] = []
    seen_ids: dict[str, Path] = {}

    for manifest_path in sorted(root_resolved.rglob("manifest.toml")):
        if "__pycache__" in manifest_path.parts:
            continue
        try:
            manifest = load_manifest(manifest_path)
        except ManifestValidationError as err:
            log_debug("Skipping invalid manifest at %s: %s", manifest_path, err)
            continue

        m_id = str(manifest.id)
        if m_id in seen_ids:
            # duplicate provider id detected
            pass
        seen_ids[m_id] = manifest_path
        discovered.append(
            DiscoveredProvider(manifest_path=manifest_path, manifest=manifest)
        )

    discovered.sort(key=lambda dp: (str(dp.manifest.id), str(dp.manifest_path)))
    return tuple(discovered)
