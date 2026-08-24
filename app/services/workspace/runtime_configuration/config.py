"""Configuration dataclass for Runtime Configuration and Admission."""

from dataclasses import dataclass, field

from app.contracts.workspace.models import StorageGuardLimits


@dataclass(frozen=True, slots=True)
class RuntimeConfigurationConfig:
    """Configuration options for Runtime Configuration and Admission.

    Attributes:
        default_guard_limits: Storage guard thresholds applied when a guard
            call does not supply explicit limits.
        port_probe_timeout_seconds: Socket timeout for the transient port
            availability probe; 1 second keeps pre-launch validation fast.
    """

    default_guard_limits: StorageGuardLimits = field(default_factory=StorageGuardLimits)
    port_probe_timeout_seconds: float = 1.0
