"""Configuration dataclass for Broker Provider Gateway."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProviderGatewayConfig:
    """Configuration options for Broker Provider Gateway."""
