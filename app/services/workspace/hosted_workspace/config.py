"""Configuration settings for Hosted Workspace Boundary."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HostedWorkspaceConfig:
    """Configuration model for hosted workspace isolation and authorization.

    Attributes:
        default_decision_ttl_seconds: Default validity TTL in seconds for decisions.
        enforce_scope_isolation: Whether to strictly enforce scope uniqueness.
    """

    default_decision_ttl_seconds: int = 3600
    enforce_scope_isolation: bool = True
