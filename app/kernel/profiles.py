"""Runtime execution profile definitions and profile readiness evaluator for the microkernel.

Traces to: P4-T01, P7-T02, Gate G4, Gate G7
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from app.kernel.errors import CapabilityReasonCode, CapabilityUnavailable

if TYPE_CHECKING:
    from app.kernel.identifiers import CapabilityId
    from app.kernel.resolver import ResolutionReport


class RuntimeProfile(StrEnum):
    """Execution profiles dictating provider readiness requirements."""

    RESEARCH = "research"
    SIMULATION = "simulation"
    DEMO = "demo"
    LIVE = "live"


@dataclass(frozen=True, slots=True)
class ProfileReadiness:
    """Readiness assessment for a specific execution profile."""

    profile: RuntimeProfile
    ready: bool
    missing: tuple[CapabilityUnavailable, ...]


def evaluate_profile_readiness(
    report: ResolutionReport,
    *,
    requirements: Mapping[RuntimeProfile, tuple[CapabilityId, ...]],
) -> tuple[ProfileReadiness, ...]:
    """Evaluate readiness of each declared execution profile against resolved capabilities.

    Args:
        report: Complete resolution report.
        requirements: Map from runtime profile to required capability IDs.

    Returns:
        Tuple of ProfileReadiness assessment objects.
    """
    bound_caps = {b.capability_id for b in report.bindings}
    inactive_by_cap = {i.capability_id: i.detail for i in report.inactive}

    # Evaluate profiles in sorted enum order
    profiles_to_eval = sorted(
        set(RuntimeProfile) | set(requirements.keys()), key=lambda p: p.value
    )

    results: list[ProfileReadiness] = []
    for profile in profiles_to_eval:
        required_caps = requirements.get(profile, ())
        missing: list[CapabilityUnavailable] = []
        for cap_id in required_caps:
            if cap_id not in bound_caps:
                provider_state = "NOT_INSTALLED"
                provider_id = None
                if cap_id in inactive_by_cap:
                    detail = inactive_by_cap[cap_id]
                    provider_state = detail.provider_state or "NOT_INSTALLED"
                    provider_id = detail.provider_id

                missing.append(
                    CapabilityUnavailable(
                        code="CAPABILITY_UNAVAILABLE",
                        reason_code=CapabilityReasonCode.PROFILE_REQUIREMENT_UNSATISFIED,
                        capability=str(cap_id),
                        consumer=f"{profile}.profile",
                        provider_id=provider_id,
                        provider_state=provider_state,
                        profile=str(profile),
                        dependency_chain=(f"{profile}.profile", str(cap_id)),
                        retryable=False,
                    )
                )
        results.append(
            ProfileReadiness(
                profile=profile,
                ready=len(missing) == 0,
                missing=tuple(missing),
            )
        )
    return tuple(results)


__all__ = (
    "ProfileReadiness",
    "RuntimeProfile",
    "evaluate_profile_readiness",
)
