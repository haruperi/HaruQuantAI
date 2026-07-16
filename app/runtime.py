"""System-level runtime initialization validation."""

from typing import Final

_EXECUTION_ROUTE_BY_PROFILE: Final[dict[str, str]] = {
    "research": "none",
    "simulation": "sim",
    "paper": "paper",
    "live": "live",
}


class RuntimeConfigurationError(ValueError):
    """Report a fail-closed runtime profile and route mismatch."""

    code: Final[str] = "SYSTEM_RUNTIME_ROUTE_INCOMPATIBLE"

    def __init__(self) -> None:
        """Initialize a bounded, value-free runtime configuration error."""
        super().__init__("Runtime profile and execution route are incompatible")


def validate_runtime_configuration(
    *,
    runtime_profile: str,
    execution_route: str,
) -> None:
    """Validate the authoritative runtime profile and route pairing.

    Args:
        runtime_profile: Runtime profile selected by Utils-owned configuration.
        execution_route: Execution route selected by Trading-owned configuration.

    Raises:
        RuntimeConfigurationError: The values are unknown or are not the one
            compatible pair defined by the system configuration manifest.
    """
    expected_route = _EXECUTION_ROUTE_BY_PROFILE.get(runtime_profile)
    if expected_route is None or execution_route != expected_route:
        raise RuntimeConfigurationError
