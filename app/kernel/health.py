"""Health and readiness projections for the microkernel.

Traces to: P4-T06, Gate G4
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from app.kernel.errors import CapabilityUnavailable
from app.kernel.identifiers import CapabilityId
from app.kernel.profiles import RuntimeProfile
from app.kernel.resolver import ResolutionReport


@dataclass(frozen=True, slots=True)
class KernelHealth:
    """Readiness and health status of the provider microkernel."""

    live: bool
    ready: bool
    active_count: int
    inactive_count: int


@dataclass(frozen=True, slots=True)
class ProfileReadiness:
    """Readiness assessment for a specific execution profile."""

    profile: RuntimeProfile
    ready: bool
    missing: tuple[CapabilityUnavailable, ...]


def evaluate_kernel_health(report: ResolutionReport) -> KernelHealth:
    """Evaluate bounded health of the provider microkernel from a resolution report.

    Args:
        report: The resolution report.

    Returns:
        KernelHealth model with active/inactive counts.
    """
    return KernelHealth(
        live=True,
        ready=True,
        active_count=len(report.bindings),
        inactive_count=len(report.inactive),
    )


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

    results: list[ProfileReadiness] = []
    for profile in sorted(requirements.keys(), key=str):
        required_caps = requirements[profile]
        missing: list[CapabilityUnavailable] = []
        for cap_id in required_caps:
            if cap_id not in bound_caps:
                if cap_id in inactive_by_cap:
                    missing.append(inactive_by_cap[cap_id])
                else:
                    missing.append(
                        CapabilityUnavailable(
                            code="CAPABILITY_UNAVAILABLE",
                            reason_code="NOT_INSTALLED",  # type: ignore[arg-type]
                            capability=str(cap_id),
                            consumer=None,
                            provider_id=None,
                            provider_state="NOT_INSTALLED",
                            profile=str(profile),
                            dependency_chain=(str(cap_id),),
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
    "KernelHealth",
    "ProfileReadiness",
    "evaluate_kernel_health",
    "evaluate_profile_readiness",
)
