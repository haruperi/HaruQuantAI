"""Composition runtime event payloads."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ConfigurationReloadedEvent:
    """Report a committed configuration reconciliation.

    Attributes:
        profile: Active deployment profile.
        modified_features: Feature identifiers affected by the reload.
        timestamp: Reload completion time in UTC.
    """

    profile: str
    modified_features: tuple[str, ...]
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class FeatureReconfiguredEvent:
    """Report a committed feature replacement or reconfiguration.

    Attributes:
        feature_id: Reconfigured feature identifier.
        generation: New provider binding generation.
        timestamp: Reconfiguration completion time in UTC.
    """

    feature_id: str
    generation: int
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class FeatureRuntimeFailedEvent:
    """Report an unexpected active-feature task failure.

    Attributes:
        feature_id: Failing feature identifier.
        task_name: Diagnostic task name.
        error_message: Bounded failure description.
        timestamp: Failure observation time in UTC.
    """

    feature_id: str
    task_name: str
    error_message: str
    timestamp: datetime
