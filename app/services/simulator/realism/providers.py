"""Simulator-owned fill-model calibration provider."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType

from app.services.simulator.calibration import (
    dump_calibration_artifact,
    get_calibration_applicability,
    load_calibration_artifact,
)
from app.services.simulator.realism.contracts import _CalibratedRealism
from app.services.simulator.realism.random_streams import sample


class _FillModelProvider:
    """Private provider satisfying Optimization's calibration port."""

    def __init__(self, profiles: Mapping[str, Mapping[str, object]]) -> None:
        self._profiles = {key: dict(value) for key, value in profiles.items()}

    def fill_model_calibration(
        self, *, market_data_ref: str, instrument: str
    ) -> Mapping[str, object]:
        """Return explicit calibration evidence without inferred defaults."""
        profile = self._profiles.get(instrument)
        if profile is None or profile.get("market_data_ref") != market_data_ref:
            return {
                "status": "NOT_CALIBRATED",
                "reason": "matching_profile_absent",
                "instrument": instrument,
            }
        return {"status": "CALIBRATED", "instrument": instrument, **profile}


def build_fill_model_provider(
    profiles: Mapping[str, Mapping[str, object]],
) -> object:
    """Build an opaque fill-model provider from explicit profile evidence.

    Args:
        profiles: Instrument-keyed validated calibration mappings.

    Returns:
        Opaque provider satisfying Optimization's consumer protocol.

    Raises:
        ValueError: If no profiles are supplied.
    """
    if not profiles:
        raise ValueError("fill-model provider requires explicit profiles")
    return _FillModelProvider(profiles)


def admit_calibrated_realism(
    artifact_value: Mapping[str, object],
    *,
    component: str,
    environment: str,
    symbol: str,
    as_of: datetime,
    canonical: bool,
) -> object:
    """Admit one applicable, valid, calibrated realism component.

    Args:
        artifact_value: Checksummed Phase-19 artifact mapping.
        component: Requested spread or execution component.
        environment: Exact target evidence scope.
        symbol: Exact canonical symbol.
        as_of: Evaluation instant.
        canonical: Whether the consumer requests canonical eligibility.

    Returns:
        Opaque admitted realism projection.

    Raises:
        TypeError: If artifact applicability or parameters are malformed.
        ValueError: If calibration, applicability, validity, or mode is ineligible.
    """
    artifact = load_calibration_artifact(artifact_value)
    dumped = dump_calibration_artifact(artifact)
    applicability = get_calibration_applicability(artifact)
    exact = applicability["applicability"]
    if not isinstance(exact, Mapping):
        raise TypeError("calibration applicability is invalid")
    if exact.get("environment") != environment or exact.get("symbol") != symbol:
        raise ValueError("calibration applicability does not match the run")
    if as_of > applicability["valid_until"]:  # type: ignore[operator]
        raise ValueError("calibration artifact is expired")
    raw_exclusions = applicability["exclusions"]
    if not isinstance(raw_exclusions, (tuple, list)):
        raise TypeError("calibration exclusions are invalid")
    exclusions = tuple(str(value) for value in raw_exclusions)
    if canonical and exact.get("canonical_eligible") != "true":
        raise ValueError("exploratory calibration cannot enter a canonical run")
    artifact_component = str(dumped["component"])
    parameters = dumped["parameters"]
    if not isinstance(parameters, Mapping):
        raise TypeError("calibration parameters are invalid")
    if component == "queue_position_pathwise":
        raise ValueError("pathwise queue requires unresolved Level-2 evidence")
    if component == "spread":
        admitted = artifact_component == "spread"
    else:
        admitted = (
            artifact_component == "execution_components"
            and f"{component}.mean" in parameters
            and not any(value.startswith(f"{component}:") for value in exclusions)
        )
    if not admitted:
        raise ValueError("requested realism component is not calibrated")
    return _CalibratedRealism(
        artifact_checksum=str(dumped["checksum"]),
        component=component,
        environment=environment,
        symbol=symbol,
        parameters=MappingProxyType(
            {str(key): str(value) for key, value in parameters.items()}
        ),
        exclusions=exclusions,
        canonical=canonical,
    )


def sample_calibrated_realism(
    admission: object, stream: object
) -> Mapping[str, object]:
    """Sample one bounded calibrated value with complete journal evidence.

    Args:
        admission: Opaque value returned by ``admit_calibrated_realism``.
        stream: Opaque concern-specific deterministic stream.

    Returns:
        Immutable sampled value and causal calibration/stream evidence.

    Raises:
        TypeError: If admission has the wrong private type.
    """
    if not isinstance(admission, _CalibratedRealism):
        raise TypeError("invalid calibrated realism admission")
    draw = sample(stream)
    key = "mean" if admission.component == "spread" else f"{admission.component}.mean"
    center = Decimal(admission.parameters[key])
    upper_key = (
        "ordinary.p95"
        if admission.component == "spread"
        else f"{admission.component}.p95"
    )
    upper = Decimal(admission.parameters.get(upper_key, str(center)))
    value = center + draw * (upper - center)
    return MappingProxyType(
        {
            "component": admission.component,
            "value": value,
            "artifact_checksum": admission.artifact_checksum,
            "stream_draw": draw,
            "canonical": admission.canonical,
            "journal_event_type": "calibrated_realism_sample",
        }
    )


__all__ = [
    "admit_calibrated_realism",
    "build_fill_model_provider",
    "sample_calibrated_realism",
]
