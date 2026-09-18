"""Explicit feature registry and profile mappings.

This module serves as the application's declarative feature factory registry.
Adding or removing a domain feature from the runtime is accomplished by adding
or removing its factory callable in `FEATURES`.

Key Design Principles:
- Pure Declarations: Importing this module executes no business logic, opens no
  database connections, and performs no I/O.
- Deterministic Composition: All feature factories are explicitly enumerated in
  `FEATURES`. The runtime performs topological dependency sorting over this
  collection to determine valid startup order.
- Role Profiles: The `PROFILES` mapping enables named deployment roles (e.g.,
  'api', 'worker', 'all') that activate predefined subsets of features.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from app.kernel.bootstrapper import FeatureFactory
from app.services.gateway.api_server import feature as gateway_api_server

# Enumerate all domain feature factory callables here.
# Features will be topologically sorted by Runtime before startup.
FEATURES: tuple[FeatureFactory, ...] = (gateway_api_server,)

# Named deployment profiles mapping a profile name to its active feature set.
PROFILES: Mapping[str, frozenset[str]] = {
    "all": frozenset({"gateway.api_server"}),
    "api": frozenset({"gateway.api_server"}),
    "default": frozenset(),
}


def available_profiles() -> tuple[str, ...]:
    """Return an alphabetically sorted tuple of all configured profile names.

    Returns:
        Sorted tuple of profile name strings.
    """
    return tuple(sorted(PROFILES.keys()))


def get_features(
    profile: str | None = None,
    enabled: Sequence[str] | None = None,
) -> tuple[tuple[FeatureFactory, ...], frozenset[str] | None]:
    """Resolve active feature factories and optional enabled name filter.

    Args:
        profile: Named role profile mapping to a predefined set of feature names.
        enabled: Explicit feature names to activate.

    Returns:
        A tuple of (factories, enabled_names_or_none).

    Raises:
        ValueError: If both profile and enabled are specified simultaneously,
            or if the requested profile name is not found in `PROFILES`.

    Example:
        >>> factories, enabled = get_features(profile="default")
        >>> factories, enabled = get_features(enabled=["auth", "database"])
    """
    if profile is not None and enabled is not None:
        raise ValueError("Cannot specify both profile and explicit enabled names")
    if profile is not None:
        if profile not in PROFILES:
            valid = ", ".join(available_profiles())
            raise ValueError(f"Unknown profile {profile!r}; valid profiles: {valid}")
        return FEATURES, PROFILES[profile]
    if enabled is not None:
        return FEATURES, frozenset(enabled)
    return FEATURES, None


__all__ = ("FEATURES", "PROFILES", "available_profiles", "get_features")
