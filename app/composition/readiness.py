"""Deployment profile readiness evaluation."""

from collections.abc import Iterable, Mapping

PROFILE_REQUIRED_CAPABILITIES: Mapping[str, frozenset[str]] = {
    "research": frozenset({"data.historical-bars@1"}),
    "backtest": frozenset({"data.historical-bars@1", "system.clock@1"}),
    "live": frozenset(
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
}


def check_profile_readiness(
    profile: str,
    active_capabilities: Iterable[str],
) -> tuple[bool, tuple[str, ...]]:
    """Check whether all required capabilities for a deployment profile are active.

    Raises:
        ValueError: If profile is unknown. Readiness must fail closed rather than
            silently treating an unknown deployment profile as ready.
    """
    normalized = profile.strip().lower()
    if normalized not in PROFILE_REQUIRED_CAPABILITIES:
        allowed = ", ".join(sorted(PROFILE_REQUIRED_CAPABILITIES))
        msg = f"Unknown readiness profile '{profile}'. Allowed: {allowed}"
        raise ValueError(msg)

    active_set = set(active_capabilities)
    required = PROFILE_REQUIRED_CAPABILITIES[normalized]
    missing = tuple(sorted(cap for cap in required if cap not in active_set))
    return len(missing) == 0, missing
