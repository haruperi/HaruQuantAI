"""Health and readiness projections for the microkernel.

Traces to: P4-T06, Gate G4
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.kernel.profiles import ProfileReadiness, evaluate_profile_readiness

if TYPE_CHECKING:
    from app.kernel.resolver import ResolutionReport


@dataclass(frozen=True, slots=True)
class KernelHealth:
    """Readiness and health status of the provider microkernel."""

    live: bool
    ready: bool
    active_count: int
    inactive_count: int


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


__all__ = (
    "KernelHealth",
    "ProfileReadiness",
    "evaluate_kernel_health",
    "evaluate_profile_readiness",
)
