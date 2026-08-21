"""Deployment profile readiness evaluation."""

from collections.abc import Iterable, Mapping

PROFILE_REQUIRED_CAPABILITIES: Mapping[str, frozenset[str]] = {
    "research": frozenset({"data.historical-bars@1"}),
    "backtest": frozenset({"data.historical-bars@1", "system.clock@1"}),
    "live": frozenset(
        {
            "broker.market-data@1",
            "broker.execution@1",
            "risk.approval@1",
            "data.historical-bars@1",
            "system.clock@1",
        }
    ),
}


def check_profile_readiness(
    profile: str,
    active_capabilities: Iterable[str],
) -> tuple[bool, tuple[str, ...]]:
    """Check whether all required capabilities for a deployment profile are active.

    Args:
        profile: Target deployment profile name (e.g. 'research', 'backtest', 'live').
        active_capabilities: Collection of currently active capability identifiers.

    Returns:
        Tuple of (is_ready boolean, tuple of missing required capability identifiers).
    """
    active_set = set(active_capabilities)
    required = PROFILE_REQUIRED_CAPABILITIES.get(profile.lower(), frozenset())

    missing = tuple(sorted(cap for cap in required if cap not in active_set))
    is_ready = len(missing) == 0
    return is_ready, missing
