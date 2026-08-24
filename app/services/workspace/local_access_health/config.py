"""Configuration dataclass for Local Access and Health."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LocalAccessHealthConfig:
    """Configuration options for Local Access and Health.

    Attributes:
        default_session_ttl_seconds: Lifetime of ephemeral session tokens in seconds.
        enforce_loopback: Enforce loopback source checks by default.
    """

    default_session_ttl_seconds: int = 3600
    enforce_loopback: bool = True
