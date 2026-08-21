"""System lifecycle and operational event contracts."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class FeatureMountedEvent:
    """Emitted when a feature is successfully mounted and becomes active.

    Attributes:
        feature_id: Unique identifier of the mounted feature.
        domain: Business domain name.
        timestamp: Time of activation in UTC.
    """

    feature_id: str
    domain: str
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class FeatureUnmountedEvent:
    """Emitted when a feature unmounts and closes its scope.

    Attributes:
        feature_id: Unique identifier of the unmounted feature.
        timestamp: Time of deactivation in UTC.
    """

    feature_id: str
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class ProfileReadinessChangedEvent:
    """Emitted when a deployment profile's readiness status changes.

    Attributes:
        profile: Profile name (e.g. 'research', 'live').
        is_ready: Whether all mandatory profile capabilities are present.
        missing_capabilities: Tuple of missing capability identifiers.
        timestamp: Time of state change in UTC.
    """

    profile: str
    is_ready: bool
    missing_capabilities: tuple[str, ...]
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class ConfigurationReloadedEvent:
    """Emitted when application configuration is reloaded and reconciled.

    Attributes:
        profile: Active deployment profile.
        modified_features: Tuple of feature IDs affected by the reload.
        timestamp: Time of reload in UTC.
    """

    profile: str
    modified_features: tuple[str, ...]
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class FeatureReconfiguredEvent:
    """Emitted when a specific feature is reconfigured or replaced at runtime.

    Attributes:
        feature_id: Unique identifier of the reconfigured feature.
        generation: New provider binding generation.
        timestamp: Time of reconfiguration in UTC.
    """

    feature_id: str
    generation: int
    timestamp: datetime
