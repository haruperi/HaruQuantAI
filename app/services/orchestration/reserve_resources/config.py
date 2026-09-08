"""Strict configuration for finite resource admission."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.contracts.orchestration.resources import ResourcePolicyRef


@dataclass(frozen=True, slots=True)
class ReserveResourcesConfig:
    """Strict configuration for resource admission feature."""

    policy: ResourcePolicyRef = field(default_factory=ResourcePolicyRef)


def from_dict(data: dict[str, Any] | None) -> ReserveResourcesConfig:
    """Parse strict feature configuration and reject unknown keys.

    Args:
        data: Raw configuration mapping or None.

    Returns:
        Validated ReserveResourcesConfig.

    Raises:
        ValueError: If unknown keys are provided.
    """
    values = dict(data or {})
    unknown = set(values) - set()
    if unknown:
        msg = f"Unknown reserve-resources configuration keys: {sorted(unknown)}"
        raise ValueError(msg)
    return ReserveResourcesConfig()
