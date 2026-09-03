"""Persistence and storage management for Data Inspection and Retention."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.contracts.data.models import (
        DatasetManifest,
        RetentionPolicy,
        StorageArtifact,
    )


class ArtifactRetentionStore:
    """In-memory inventory and manifest persistence store."""

    def __init__(self) -> None:
        self._committed_manifests: list[DatasetManifest] = []
        self._storage_artifacts: list[StorageArtifact] = []
        self._current_policy: RetentionPolicy | None = None

    @property
    def current_policy(self) -> RetentionPolicy | None:
        """Return the active retention policy."""
        return self._current_policy

    @current_policy.setter
    def current_policy(self, policy: RetentionPolicy | None) -> None:
        """Set active retention policy."""
        self._current_policy = policy

    def register_manifest(self, manifest: DatasetManifest) -> None:
        """Register a committed dataset manifest."""
        self._committed_manifests.append(manifest)

    def register_artifact(self, artifact: StorageArtifact) -> None:
        """Register a storage artifact."""
        self._storage_artifacts.append(artifact)

    def get_manifests(self) -> list[DatasetManifest]:
        """Return all registered manifests."""
        return list(self._committed_manifests)

    def get_artifacts(self) -> list[StorageArtifact]:
        """Return all registered artifacts."""
        return list(self._storage_artifacts)

    def set_artifacts(self, artifacts: list[StorageArtifact]) -> None:
        """Replace registered artifacts."""
        self._storage_artifacts = list(artifacts)

    def clear(self) -> None:
        """Clear all registered manifests and artifacts."""
        self._committed_manifests.clear()
        self._storage_artifacts.clear()
        self._current_policy = None
