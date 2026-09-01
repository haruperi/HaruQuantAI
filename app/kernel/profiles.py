"""Runtime profiles and readiness evaluation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from app.kernel.identifiers import CapabilityId

if TYPE_CHECKING:
    from app.kernel.resolver import ResolutionReport


class RuntimeProfile(StrEnum):
    """Authoritative runtime profiles."""

    OFFLINE = "offline"
    RESEARCH = "research"
    SIMULATION = "simulation"
    BACKTEST = "backtest"
    DEMO = "demo"
    LIVE = "live"


@dataclass(frozen=True, slots=True)
class CapabilityUnavailable:
    """Missing or unavailable capability description."""

    capability: str
    code: str = "CAPABILITY_UNAVAILABLE"
    reason_code: str = "NOT_INSTALLED"
    consumer: str | None = None
    provider_id: str | None = None
    provider_state: str = "absent"
    profile: str | None = None
    dependency_chain: tuple[str, ...] = ()
    retryable: bool = False


@dataclass(frozen=True, slots=True)
class ProfileReadiness:
    """Readiness status for a specific runtime profile."""

    profile: RuntimeProfile
    ready: bool
    missing: tuple[CapabilityUnavailable, ...] = ()


def evaluate_profile_readiness(
    report: ResolutionReport,
    *,
    requirements: Mapping[RuntimeProfile, tuple[CapabilityId, ...]],
) -> tuple[ProfileReadiness, ...]:
    """Evaluate profile readiness given a resolution report and profile requirements."""
    active_caps = {b.capability_id for b in report.bindings}
    results: list[ProfileReadiness] = []

    for profile, required_caps in requirements.items():
        missing_list: list[CapabilityUnavailable] = []
        for req_cap in required_caps:
            if req_cap not in active_caps:
                missing_list.append(
                    CapabilityUnavailable(
                        capability=str(req_cap),
                        code="CAPABILITY_UNAVAILABLE",
                        reason_code="CAPABILITY_UNAVAILABLE",
                        profile=str(profile),
                    )
                )
        results.append(
            ProfileReadiness(
                profile=profile,
                ready=len(missing_list) == 0,
                missing=tuple(missing_list),
            )
        )

    return tuple(results)
