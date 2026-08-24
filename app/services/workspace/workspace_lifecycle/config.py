"""Configuration dataclass for Workspace Lifecycle."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorkspaceLifecycleConfig:
    """Configuration options for Workspace Lifecycle."""

    auto_migrate: bool = True
    busy_timeout_seconds: float = 5.0
    staged_grace_period_seconds: float = 86400.0
