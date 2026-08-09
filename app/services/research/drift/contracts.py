"""Performance drift evidence contract (FEAT-RES-15).

Monitors live-simulation/paper outcomes against an approved expectancy
envelope and proposes suspension when drift thresholds are reached. Drift
evidence is advisory: it never mutates governance state directly. A missing
approved envelope fails closed to ``INSUFFICIENT_EVIDENCE`` rather than an
inferred "no drift" verdict.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal, cast

from app.services.research.contracts.errors import ConfigurationError, ValidationError
from app.utils import canonical_digest, to_json_safe

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
# Drift thresholds are bounded fractions; a 100% relative drop is the sane
# ceiling for advisory suspension proposals.
_MAX_RELATIVE_DRIFT = 1.0


def _utc(value: datetime) -> None:
    """Validate one UTC instant.

    Raises:
        ValidationError: If the value is not UTC-aware.
    """
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValidationError("RES_INPUT_INVALID", "DRIFT_TIME_NOT_UTC")


def _finite_fraction(value: float, *, detail: str) -> None:
    """Validate one finite fraction in ``[0, 1]``.

    Raises:
        ValidationError: If the value is non-finite or out of range.
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValidationError("RES_INPUT_INVALID", detail)
    if math.isnan(value) or value < 0.0 or value > 1.0:
        raise ValidationError("RES_INPUT_INVALID", detail)


def _finite_non_negative(value: float, *, detail: str) -> None:
    """Validate one finite non-negative numeric value.

    Raises:
        ValidationError: If the value is non-finite or negative.
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValidationError("RES_INPUT_INVALID", detail)
    if math.isnan(value) or value < 0.0:
        raise ValidationError("RES_INPUT_INVALID", detail)


@dataclass(frozen=True, slots=True)
class PerformanceDriftEvidence:
    """Immutable advisory performance drift evidence.

    Attributes:
        contract_version: Compatibility version; always ``v1``.
        schema_id: Stable namespaced schema identity.
        profile_id: Approved expectancy profile under review.
        observed_from_utc: Inclusive start of the observation window.
        observed_to_utc: Inclusive end of the observation window.
        observed_win_rate: Observed live-sim/paper win rate.
        observed_expected_value_r: Observed live-sim/paper EV in R.
        observed_max_drawdown_r: Observed live-sim/paper drawdown magnitude.
        envelope_win_rate: Approved envelope win rate.
        envelope_expected_value_r: Approved envelope EV in R.
        envelope_max_drawdown_r: Approved envelope drawdown magnitude.
        win_rate_drift: Relative win-rate drop vs envelope (non-negative).
        expected_value_drift: Relative EV drop vs envelope (non-negative).
        drawdown_exceeded: Whether observed drawdown breached the envelope.
        thresholds: Drift thresholds applied (win_rate, expected_value, drawdown).
        breach: Which threshold(s) breached
            (``win_rate``/``expected_value``/``drawdown``).
        suspension_proposed: Whether suspension is proposed.
        generated_at_utc: Evidence generation instant.
        canonical_hash: Canonical SHA-256 of the evidence material.
        advisory_only: Always ``True``; Research is advisory-only.
    """

    contract_version: Literal["v1"]
    schema_id: Literal["research.performance_drift.v1"]
    profile_id: str
    observed_from_utc: datetime
    observed_to_utc: datetime
    observed_win_rate: float
    observed_expected_value_r: float
    observed_max_drawdown_r: float
    envelope_win_rate: float
    envelope_expected_value_r: float
    envelope_max_drawdown_r: float
    win_rate_drift: float
    expected_value_drift: float
    drawdown_exceeded: bool
    thresholds: Mapping[str, float]
    breach: tuple[str, ...]
    suspension_proposed: bool
    generated_at_utc: datetime
    canonical_hash: str
    advisory_only: Literal[True] = field(default=True, init=False)

    def __post_init__(self) -> None:
        """Validate drift evidence identity, bounds, and breach consistency.

        Raises:
            ValidationError: If statistics, thresholds, or breaches are invalid.
        """
        if not isinstance(self.profile_id, str) or not self.profile_id.strip():
            raise ValidationError("RES_INPUT_INVALID", "DRIFT_PROFILE_ID_EMPTY")
        _utc(self.observed_from_utc)
        _utc(self.observed_to_utc)
        _utc(self.generated_at_utc)
        if self.observed_from_utc > self.observed_to_utc:
            raise ValidationError("RES_INPUT_INVALID", "DRIFT_WINDOW")
        _finite_fraction(self.observed_win_rate, detail="DRIFT_OBSERVED_WIN_RATE")
        _finite_fraction(self.envelope_win_rate, detail="DRIFT_ENVELOPE_WIN_RATE")
        for detail, value in (
            ("DRIFT_OBSERVED_EV", self.observed_expected_value_r),
            ("DRIFT_ENVELOPE_EV", self.envelope_expected_value_r),
            ("DRIFT_WIN_RATE_DRIFT", self.win_rate_drift),
            ("DRIFT_EV_DRIFT", self.expected_value_drift),
        ):
            _finite_non_negative(value, detail=detail)
        if not isinstance(self.observed_max_drawdown_r, (int, float)):
            raise ValidationError("RES_INPUT_INVALID", "DRIFT_OBSERVED_DRAWDOWN")
        _finite_non_negative(
            self.envelope_max_drawdown_r, detail="DRIFT_ENVELOPE_DRAWDOWN"
        )
        self._validate_thresholds_and_breaches()
        if (
            not isinstance(self.canonical_hash, str)
            or _SHA256.fullmatch(self.canonical_hash) is None
        ):
            raise ValidationError("RES_INPUT_INVALID", "DRIFT_HASH_INVALID")

    def _validate_thresholds_and_breaches(self) -> None:
        """Validate threshold bounds, breach labels, and proposal consistency.

        Raises:
            ValidationError: If thresholds, breach labels, or proposal conflict.
        """
        if not self.thresholds or not all(
            0.0 <= float(v) <= _MAX_RELATIVE_DRIFT for v in self.thresholds.values()
        ):
            raise ValidationError("RES_INPUT_INVALID", "DRIFT_THRESHOLDS")
        # Breach labels must come from the known threshold keys.
        allowed = set(self.thresholds)
        if any(item not in allowed for item in self.breach):
            raise ValidationError("RES_INPUT_INVALID", "DRIFT_BREACH_LABEL")
        if (self.suspension_proposed and not self.breach) or (
            self.breach and not self.suspension_proposed
        ):
            raise ValidationError("RES_INPUT_INVALID", "DRIFT_BREACH_CONSISTENCY")


def _drift_material(evidence: PerformanceDriftEvidence) -> Mapping[str, object]:
    """Return the canonical hash material for drift evidence."""
    return {
        "contract_version": evidence.contract_version,
        "schema_id": evidence.schema_id,
        "profile_id": evidence.profile_id,
        "observed_from_utc": evidence.observed_from_utc.isoformat(),
        "observed_to_utc": evidence.observed_to_utc.isoformat(),
        "observed_win_rate": evidence.observed_win_rate,
        "observed_expected_value_r": evidence.observed_expected_value_r,
        "observed_max_drawdown_r": evidence.observed_max_drawdown_r,
        "envelope_win_rate": evidence.envelope_win_rate,
        "envelope_expected_value_r": evidence.envelope_expected_value_r,
        "envelope_max_drawdown_r": evidence.envelope_max_drawdown_r,
        "thresholds": dict(evidence.thresholds),
        "generated_at_utc": evidence.generated_at_utc.isoformat(),
    }


def _relative_drop(approved: float, observed: float) -> float:
    """Return the non-negative relative drop of an observed vs approved metric.

    A relative drop is ``(approved - observed) / approved`` when approved is
    positive and the observed is below approved; otherwise ``0.0``. Negative
    drops (observed better than approved) are clamped to zero — drift evidence
    measures degradation only.

    Args:
        approved: Approved envelope metric value.
        observed: Observed live-sim/paper metric value.

    Returns:
        Non-negative relative drop fraction.
    """
    if approved <= 0.0:
        return 0.0
    drop = (approved - observed) / approved
    return max(0.0, drop)


def build_performance_drift_evidence(
    *,
    profile_id: str,
    observed_from_utc: datetime,
    observed_to_utc: datetime,
    observed_win_rate: float,
    observed_expected_value_r: float,
    observed_max_drawdown_r: float,
    envelope_win_rate: float,
    envelope_expected_value_r: float,
    envelope_max_drawdown_r: float,
    thresholds: Mapping[str, float],
    generated_at_utc: datetime,
) -> dict[str, Any]:
    """Build validated JSON-safe performance drift evidence v1.

    Args:
        profile_id: Approved expectancy profile under review.
        observed_from_utc: Inclusive start of the observation window.
        observed_to_utc: Inclusive end of the observation window.
        observed_win_rate: Observed live-sim/paper win rate.
        observed_expected_value_r: Observed live-sim/paper EV in R.
        observed_max_drawdown_r: Observed drawdown magnitude in R.
        envelope_win_rate: Approved envelope win rate.
        envelope_expected_value_r: Approved envelope EV in R.
        envelope_max_drawdown_r: Approved envelope drawdown magnitude in R.
        thresholds: Drift thresholds keyed by
            ``win_rate``/``expected_value``/``drawdown``.
        generated_at_utc: Evidence generation instant.

    Returns:
        JSON-safe drift evidence mapping.

    Raises:
        ValidationError: If statistics, thresholds, or breaches are invalid.
    """
    win_rate_drift = _relative_drop(envelope_win_rate, observed_win_rate)
    expected_value_drift = _relative_drop(
        envelope_expected_value_r, observed_expected_value_r
    )
    drawdown_exceeded = observed_max_drawdown_r > envelope_max_drawdown_r
    breach: list[str] = []
    if win_rate_drift >= float(thresholds.get("win_rate", _MAX_RELATIVE_DRIFT)):
        breach.append("win_rate")
    if expected_value_drift >= float(
        thresholds.get("expected_value", _MAX_RELATIVE_DRIFT)
    ):
        breach.append("expected_value")
    if drawdown_exceeded and float(thresholds.get("drawdown", 0.0)) > 0.0:
        breach.append("drawdown")
    material = {
        "contract_version": "v1",
        "schema_id": "research.performance_drift.v1",
        "profile_id": profile_id,
        "observed_from_utc": observed_from_utc.isoformat(),
        "observed_to_utc": observed_to_utc.isoformat(),
        "observed_win_rate": observed_win_rate,
        "observed_expected_value_r": observed_expected_value_r,
        "observed_max_drawdown_r": observed_max_drawdown_r,
        "envelope_win_rate": envelope_win_rate,
        "envelope_expected_value_r": envelope_expected_value_r,
        "envelope_max_drawdown_r": envelope_max_drawdown_r,
        "thresholds": dict(thresholds),
        "generated_at_utc": generated_at_utc.isoformat(),
    }
    canonical_hash = canonical_digest(material)
    evidence = PerformanceDriftEvidence(
        contract_version="v1",
        schema_id="research.performance_drift.v1",
        profile_id=profile_id,
        observed_from_utc=observed_from_utc,
        observed_to_utc=observed_to_utc,
        observed_win_rate=observed_win_rate,
        observed_expected_value_r=observed_expected_value_r,
        observed_max_drawdown_r=observed_max_drawdown_r,
        envelope_win_rate=envelope_win_rate,
        envelope_expected_value_r=envelope_expected_value_r,
        envelope_max_drawdown_r=envelope_max_drawdown_r,
        win_rate_drift=win_rate_drift,
        expected_value_drift=expected_value_drift,
        drawdown_exceeded=drawdown_exceeded,
        thresholds=dict(thresholds),
        breach=tuple(breach),
        suspension_proposed=bool(breach),
        generated_at_utc=generated_at_utc,
        canonical_hash=canonical_hash,
    )
    return dict(to_json_safe(_drift_mapping(evidence)))  # type: ignore[arg-type]


def _drift_mapping(evidence: PerformanceDriftEvidence) -> Mapping[str, object]:
    """Return the full transport mapping for drift evidence."""
    return {
        "contract_version": evidence.contract_version,
        "schema_id": evidence.schema_id,
        "profile_id": evidence.profile_id,
        "observed_from_utc": evidence.observed_from_utc.isoformat(),
        "observed_to_utc": evidence.observed_to_utc.isoformat(),
        "observed_win_rate": evidence.observed_win_rate,
        "observed_expected_value_r": evidence.observed_expected_value_r,
        "observed_max_drawdown_r": evidence.observed_max_drawdown_r,
        "envelope_win_rate": evidence.envelope_win_rate,
        "envelope_expected_value_r": evidence.envelope_expected_value_r,
        "envelope_max_drawdown_r": evidence.envelope_max_drawdown_r,
        "win_rate_drift": evidence.win_rate_drift,
        "expected_value_drift": evidence.expected_value_drift,
        "drawdown_exceeded": evidence.drawdown_exceeded,
        "thresholds": dict(evidence.thresholds),
        "breach": evidence.breach,
        "suspension_proposed": evidence.suspension_proposed,
        "generated_at_utc": evidence.generated_at_utc.isoformat(),
        "canonical_hash": evidence.canonical_hash,
        "advisory_only": True,
    }


def parse_performance_drift_evidence(
    value: Mapping[str, object],
) -> dict[str, Any]:
    """Parse and fully validate a performance drift evidence v1 mapping.

    Args:
        value: Candidate JSON-safe drift evidence mapping.

    Returns:
        Re-validated JSON-safe drift evidence mapping.

    Raises:
        ConfigurationError: If the supplied canonical hash does not match.
        ValidationError: If the mapping is structurally or semantically invalid.
    """
    if not isinstance(value, Mapping):
        raise ValidationError("RES_INPUT_INVALID", "DRIFT_NOT_MAPPING")
    if value.get("contract_version") != "v1":
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "DRIFT_VERSION")
    if value.get("schema_id") != "research.performance_drift.v1":
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "DRIFT_SCHEMA")
    if value.get("advisory_only") is not True:
        raise ValidationError("RES_INPUT_INVALID", "DRIFT_NOT_ADVISORY")
    parsed = build_performance_drift_evidence(
        profile_id=str(value["profile_id"]),
        observed_from_utc=datetime.fromisoformat(str(value["observed_from_utc"])),
        observed_to_utc=datetime.fromisoformat(str(value["observed_to_utc"])),
        observed_win_rate=float(cast("Any", value["observed_win_rate"])),
        observed_expected_value_r=float(
            cast("Any", value["observed_expected_value_r"])
        ),
        observed_max_drawdown_r=float(cast("Any", value["observed_max_drawdown_r"])),
        envelope_win_rate=float(cast("Any", value["envelope_win_rate"])),
        envelope_expected_value_r=float(
            cast("Any", value["envelope_expected_value_r"])
        ),
        envelope_max_drawdown_r=float(cast("Any", value["envelope_max_drawdown_r"])),
        thresholds=cast("Mapping[str, float]", value["thresholds"]),
        generated_at_utc=datetime.fromisoformat(str(value["generated_at_utc"])),
    )
    if parsed["canonical_hash"] != value.get("canonical_hash"):
        raise ConfigurationError("RES_CONFIGURATION_INVALID", "DRIFT_HASH_MISMATCH")
    return parsed


__all__ = (
    "PerformanceDriftEvidence",
    "build_performance_drift_evidence",
    "parse_performance_drift_evidence",
)
