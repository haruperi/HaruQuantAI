"""Deferred-integration calibration ports for the execution boundary.

Implements the consumer side of Trading Cockpit Phase 0 ``TC-IMP-OPT-02`` (fill-model
calibration) and ``TC-IMP-OPT-03`` (scenario difficulty calibration). Their
authoritative providers do not yet exist:

- ``TC-IMP-OPT-02`` is deferred to Simulator ``TC-IMP-SIM-16..20`` (fill, latency,
  slippage, queue, market-impact models).
- ``TC-IMP-OPT-03`` is deferred to Simulator ``TC-IMP-SIM-11..15`` (scenario engine).

Per the deferred-integration rule (AGENTS.md §1 and change-control rule 3) this module
declares only the narrow fields Optimization needs and a deterministic fail-closed
fallback. It never implements the provider's business logic and never returns an
inferred calibration. A missing provider yields ``NOT_CALIBRATED``, which downstream
robustness evidence treats as ``validation_needed`` rather than a plausible default.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from app.utils import get_logger

logger = get_logger(__name__)

CALIBRATION_NOT_AVAILABLE = "NOT_CALIBRATED"
CALIBRATION_AVAILABLE = "CALIBRATED"


class FillModelCalibrationPort(Protocol):
    """Narrow consumer port for Simulator-owned fill-model calibration.

    The Simulator provider (``TC-IMP-SIM-16..20``) supplies the production
    implementation. The port is declared here so Optimization can degrade safely when
    the provider is absent.
    """

    def fill_model_calibration(
        self,
        *,
        market_data_ref: str,  # noqa: ARG002
        instrument: str,  # noqa: ARG002
    ) -> Mapping[str, object]:
        """Return validated fill-model calibration evidence.

        Args:
            market_data_ref: Approved Data source reference.
            instrument: Traded instrument identifier.

        Raises:
            NotImplementedError: Protocol declarations are not executable.
        """
        logger.debug("Declaring fill-model calibration port")
        raise NotImplementedError


class ScenarioDifficultyCalibrationPort(Protocol):
    """Narrow consumer port for Simulator-owned scenario difficulty calibration.

    The Simulator provider (``TC-IMP-SIM-11..15``) supplies the production
    implementation.
    """

    def scenario_difficulty_calibration(
        self,
        *,
        market_data_ref: str,  # noqa: ARG002
        competence_target: str,  # noqa: ARG002
    ) -> Mapping[str, object]:
        """Return validated scenario-difficulty calibration evidence.

        Args:
            market_data_ref: Approved Data source reference.
            competence_target: Target competence level identifier.

        Raises:
            NotImplementedError: Protocol declarations are not executable.
        """
        logger.debug("Declaring scenario-difficulty calibration port")
        raise NotImplementedError


def resolve_fill_model_calibration(
    *,
    market_data_ref: str,
    instrument: str,
    provider: FillModelCalibrationPort | None,
) -> dict[str, object]:
    """Resolve fill-model calibration, failing closed when no provider exists.

    Args:
        market_data_ref: Approved Data source reference.
        instrument: Traded instrument identifier.
        provider: Optional injected Simulator-owned calibration provider.

    Returns:
        Calibration status mapping. When a provider is supplied and returns
        evidence, that evidence is passed through as JSON-safe mapping data. When no
        provider is supplied the result is an explicit ``NOT_CALIBRATED`` status
        with no fabricated parameters.
    """
    logger.info(
        "Resolving fill-model calibration | instrument=%s provider=%s",
        instrument,
        "present" if provider is not None else "absent",
    )
    if provider is None:
        return {
            "status": CALIBRATION_NOT_AVAILABLE,
            "reason": "fill_model_provider_absent",
            "deferred_to": "TC-IMP-SIM-16..20",
        }
    evidence = dict(
        provider.fill_model_calibration(
            market_data_ref=market_data_ref, instrument=instrument
        )
    )
    evidence.setdefault("status", CALIBRATION_AVAILABLE)
    return evidence


def resolve_scenario_difficulty_calibration(
    *,
    market_data_ref: str,
    competence_target: str,
    provider: ScenarioDifficultyCalibrationPort | None,
) -> dict[str, object]:
    """Resolve scenario-difficulty calibration, failing closed without a provider.

    Args:
        market_data_ref: Approved Data source reference.
        competence_target: Target competence level identifier.
        provider: Optional injected Simulator-owned calibration provider.

    Returns:
        Calibration status mapping. A missing provider yields an explicit
        ``NOT_CALIBRATED`` status; it never fabricates scenario parameters.
    """
    logger.info(
        "Resolving scenario-difficulty calibration | target=%s provider=%s",
        competence_target,
        "present" if provider is not None else "absent",
    )
    if provider is None:
        return {
            "status": CALIBRATION_NOT_AVAILABLE,
            "reason": "scenario_engine_absent",
            "deferred_to": "TC-IMP-SIM-11..15",
        }
    evidence = dict(
        provider.scenario_difficulty_calibration(
            market_data_ref=market_data_ref, competence_target=competence_target
        )
    )
    evidence.setdefault("status", CALIBRATION_AVAILABLE)
    return evidence


def get_calibration_contract_version() -> str:
    """Return the Optimization calibration consumer-port contract version.

    Returns:
        The canonical ``v1`` consumer-port version string.
    """
    return "v1"


__all__: tuple[str, ...] = (
    "CALIBRATION_AVAILABLE",
    "CALIBRATION_NOT_AVAILABLE",
    "FillModelCalibrationPort",
    "ScenarioDifficultyCalibrationPort",
    "get_calibration_contract_version",
    "resolve_fill_model_calibration",
    "resolve_scenario_difficulty_calibration",
)
