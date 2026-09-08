"""Strict empty configuration for artifact custody."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ManageArtifactsConfig:
    """Artifact custody roots are workspace-owned and not feature config."""


def from_dict(raw: dict[str, object] | None) -> ManageArtifactsConfig:
    raw = {} if raw is None else raw
    if raw:
        raise ValueError(f"unknown manage-artifacts config keys: {sorted(raw)}")
    return ManageArtifactsConfig()
