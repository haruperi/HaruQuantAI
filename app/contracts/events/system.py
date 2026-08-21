"""System lifecycle and operational event contracts."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class FeatureMountedEvent:
    """Emitted when a feature successfully becomes active."""

    feature_id: str
    domain: str
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class FeatureUnmountedEvent:
    """Emitted when a feature unmounts and closes its scope."""

    feature_id: str
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class ProfileReadinessChangedEvent:
    """Emitted when deployment-profile readiness changes."""

    profile: str
    is_ready: bool
    missing_capabilities: tuple[str, ...]
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class ConfigurationReloadedEvent:
    """Emitted after configuration reload and reconciliation."""

    profile: str
    modified_features: tuple[str, ...]
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class FeatureReconfiguredEvent:
    """Emitted after a feature replacement commits."""

    feature_id: str
    generation: int
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class FeatureRuntimeFailedEvent:
    """Emitted when a managed feature task fails unexpectedly."""

    feature_id: str
    error_type: str
    message: str
    task_name: str | None
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class ReplacementCleanupDegradedEvent:
    """Emitted when replacement committed but old-scope cleanup degraded."""

    feature_id: str
    new_generation: int | None
    cleanup_errors: tuple[str, ...]
    timestamp: datetime
