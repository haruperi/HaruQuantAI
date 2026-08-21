"""Deployment profile readiness evaluation."""

from collections.abc import Iterable

from app.composition.config import ConfigurationError, DEPLOYMENT_PROFILES


def check_profile_readiness(
    profile: str,
    active_capabilities: Iterable[str],
) -> tuple[bool, tuple[str, ...]]:
    """Check whether all required capabilities for a deployment profile are active."""
    normalized = profile.strip().lower()
    deployment_profile = DEPLOYMENT_PROFILES.get(normalized)
    if deployment_profile is None:
        allowed = ", ".join(sorted(DEPLOYMENT_PROFILES))
        raise ConfigurationError(
            f"Unknown readiness profile '{profile}'. Allowed: {allowed}"
        )

    active_set = set(active_capabilities)
    missing = tuple(
        sorted(
            capability
            for capability in deployment_profile.required_capabilities
            if capability not in active_set
        )
    )
    return not missing, missing
