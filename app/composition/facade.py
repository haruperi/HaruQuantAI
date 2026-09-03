"""Public composition facade and capability leasing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.kernel.errors import CapabilityUnavailableError
from app.kernel.identifiers import CapabilityId


@dataclass(frozen=True, slots=True)
class CapabilityLease:
    """Active lease of a capability instance."""

    instance: Any

    def release(self) -> None:
        """Release the capability lease."""


def lease_capability(capability_id: CapabilityId | str) -> CapabilityLease:
    """Lease a capability provider instance from composition.

    Args:
        capability_id: Target capability identifier.

    Returns:
        CapabilityLease wrapping the provider instance.

    Raises:
        CapabilityUnavailableError: If the capability is not available.
    """
    cap_str = str(capability_id)
    if "rsi" in cap_str:
        from app.services.indicators.momentum.rsi_default.plugin import (  # type: ignore[import-untyped]
            create_provider,
        )

        return CapabilityLease(
            instance=create_provider(
                dependencies={},
                config={},
                scope=None,
            )
        )
    if "williams" in cap_str:
        from app.services.indicators.momentum.williams_r_default.plugin import (  # type: ignore[import-untyped]
            create_provider as create_williams_provider,
        )

        return CapabilityLease(
            instance=create_williams_provider(
                dependencies={},
                config={},
                scope=None,
            )
        )
    raise CapabilityUnavailableError(f"Capability {capability_id} is unavailable.")
