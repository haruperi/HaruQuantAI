"""Deployment profile readiness evaluation and capability requirements."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeploymentProfile:
    """Specification of a deployment profile and its required capabilities.

    Attributes:
        name: Unique profile identifier (e.g. 'research', 'live').
        description: Human-readable description of the profile's operational role.
        required_capabilities: Frozenset of versioned capability identifiers.
        is_critical: Whether missing requirements indicate a safety hazard.
    """

    name: str
    description: str
    required_capabilities: frozenset[str]
    is_critical: bool = False


PROFILES: Mapping[str, DeploymentProfile] = {
    "research": DeploymentProfile(
        name="research",
        description="Offline research and dataset preparation",
        required_capabilities=frozenset({"data.historical-bars@1"}),
        is_critical=False,
    ),
    "backtest": DeploymentProfile(
        name="backtest",
        description="Historical strategy simulation and backtesting",
        required_capabilities=frozenset(
            {
                "data.historical-bars@1",
                "system.clock@1",
            }
        ),
        is_critical=False,
    ),
    "live": DeploymentProfile(
        name="live",
        description="Live market data streaming, risk validation, and execution",
        required_capabilities=frozenset(
            {
                "system.clock@1",
                "broker.market-data@1",
                "broker.execution@1",
                "data.realtime-ticks@1",
                "portfolio.positions@1",
                "risk.approval@1",
                "trading.execution@1",
            }
        ),
        is_critical=True,
    ),
    "offline": DeploymentProfile(
        name="offline",
        description="Zero-capability maintenance or diagnostics shell",
        required_capabilities=frozenset(),
        is_critical=False,
    ),
}

KNOWN_PROFILES: frozenset[str] = frozenset(PROFILES.keys())

PROFILE_REQUIRED_CAPABILITIES: Mapping[str, frozenset[str]] = {
    name: p.required_capabilities for name, p in PROFILES.items()
}


def check_profile_readiness(
    profile: str,
    active_capabilities: Iterable[str],
) -> tuple[bool, tuple[str, ...]]:
    """Check whether all required capabilities for a deployment profile are active.

    Args:
        profile: Target deployment profile name.
        active_capabilities: Collection of currently active capability identifiers.

    Returns:
        Tuple of (is_ready boolean, tuple of missing required capability identifiers).
    """
    profile_key = profile.strip().lower()
    prof = PROFILES.get(profile_key)
    if prof is None:
        # Fail closed on unknown/unsupported profile
        return False, (f"UNKNOWN_PROFILE:{profile}",)

    active_set = set(active_capabilities)
    missing = tuple(
        sorted(cap for cap in prof.required_capabilities if cap not in active_set)
    )
    is_ready = len(missing) == 0
    return is_ready, missing
