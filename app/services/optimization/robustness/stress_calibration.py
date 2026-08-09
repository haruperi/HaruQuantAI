"""Stress-profile calibration consumer port (TC-IMP-OPT-06).

Declares the narrow consumer port for calibrating shock magnitudes and dependencies
while preserving transparent assumptions. The authoritative provider does not yet
exist: Risk ``TC-IMP-RISK-12`` / Research ``TC-IMP-RES-06`` own the stress-shock
profile. Optimization supplies only the consumer port and a deterministic fail-closed
fallback (``STRESS_PROFILE_UNCALIBRATED``); it never fabricates a shock profile and
never implements the provider's business logic (change-control rule 3, deferred
integration).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from app.utils import get_logger

logger = get_logger(__name__)

STRESS_PROFILE_UNCALIBRATED = "STRESS_PROFILE_UNCALIBRATED"
STRESS_PROFILE_CALIBRATED = "STRESS_PROFILE_CALIBRATED"


class StressProfileCalibrationPort(Protocol):
    """Narrow consumer port for Risk/Research-owned stress-shock calibration.

    The provider (Risk ``TC-IMP-RISK-12`` / Research ``TC-IMP-RES-06``) supplies the
    production stress-shock profile.
    """

    def stress_profile_calibration(
        self,
        *,
        strategy_ref: str,  # noqa: ARG002
        market_data_ref: str,  # noqa: ARG002
    ) -> Mapping[str, object]:
        """Return validated stress-shock calibration evidence.

        Args:
            strategy_ref: Approved Strategy version reference.
            market_data_ref: Approved Data source reference.

        Raises:
            NotImplementedError: Protocol declarations are not executable.
        """
        logger.debug("Declaring stress-profile calibration port")
        raise NotImplementedError


def resolve_stress_profile_calibration(
    *,
    strategy_ref: str,
    market_data_ref: str,
    provider: StressProfileCalibrationPort | None,
) -> dict[str, object]:
    """Resolve stress-profile calibration, failing closed without a provider.

    Args:
        strategy_ref: Approved Strategy version reference.
        market_data_ref: Approved Data source reference.
        provider: Optional injected Risk/Research-owned calibration provider.

    Returns:
        Calibration-status mapping. A missing provider yields an explicit
        ``STRESS_PROFILE_UNCALIBRATED`` status; it never fabricates a shock profile.
    """
    logger.info(
        "Resolving stress-profile calibration | provider=%s",
        "present" if provider is not None else "absent",
    )
    if provider is None:
        return {
            "status": STRESS_PROFILE_UNCALIBRATED,
            "decision": "stress_evidence_uncalibrated",
            "reason": "stress_shock_profile_absent",
            "deferred_to": "TC-IMP-RISK-12 / TC-IMP-RES-06",
        }
    evidence = dict(
        provider.stress_profile_calibration(
            strategy_ref=strategy_ref, market_data_ref=market_data_ref
        )
    )
    evidence.setdefault("status", STRESS_PROFILE_CALIBRATED)
    evidence.setdefault("decision", "stress_evidence_calibrated")
    return evidence


def get_stress_calibration_contract_version() -> str:
    """Return the stress-profile calibration consumer-port version.

    Returns:
        The canonical ``v1`` version string.
    """
    return "v1"


__all__: tuple[str, ...] = (
    "STRESS_PROFILE_CALIBRATED",
    "STRESS_PROFILE_UNCALIBRATED",
    "StressProfileCalibrationPort",
    "get_stress_calibration_contract_version",
    "resolve_stress_profile_calibration",
)
