"""Approved expectancy profile contract and governance transport (FEAT-RES-14).

Implements the authoritative Research-owned approved-expectancy profile
(``TC-IMP-RES-03``/``TC-IMP-RES-04``). The profile is the governance
prerequisite that unblocks Strategy (``TC-IMP-STRAT-08``) and Risk
(``TC-IMP-RISK-07``): Strategy holds a version-exact ``profile_id``/
``exact_version`` reference and Risk consumes an exact-match eligibility
override.

Per settled decision D-1, the cross-domain contract travels as a validated
JSON-safe mapping behind ``build_approved_expectancy_profile`` /
``parse_approved_expectancy_profile``. The internal frozen dataclass stays
private; the package root exposes only standalone functions.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any, Literal, cast

from app.services.research.contracts.errors import (
    ConfigurationError,
    ValidationError,
)
from app.utils import canonical_digest, to_json_safe

type GovernanceState = Literal[
    "draft", "under_review", "approved", "suspended", "expired", "revoked"
]
type OutOfSampleStatus = Literal["in_sample", "out_of_sample", "walk_forward"]

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_NON_EMPTY = re.compile(r"\S")
# Surrogate identity uses the documented Utils ``id`` stable-id prefix so a
# profile is addressable across restarts without a filesystem path (OD-RES-01).
_PROFILE_ID = re.compile(r"id-[0-9a-f]{64}\Z")
_MAX_INSTRUMENTS = 64


def _utc(value: datetime) -> None:
    """Validate one UTC instant.

    Args:
        value: Candidate timestamp.

    Raises:
        ValidationError: If the value is not UTC-aware.
    """
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValidationError("RES_INPUT_INVALID", "EXPECTANCY_TIME_NOT_UTC")


def _require_non_empty(value: str, *, detail: str) -> None:
    """Reject empty/whitespace-only strings.

    Args:
        value: Candidate string.
        detail: Symbolic failure detail.

    Raises:
        ValidationError: If the value is empty or whitespace-only.
    """
    if not isinstance(value, str) or _NON_EMPTY.search(value) is None:
        raise ValidationError("RES_INPUT_INVALID", detail)


def _validate_profile_id(value: str) -> None:
    """Validate one surrogate profile identity.

    Args:
        value: Candidate profile identifier.

    Raises:
        ValidationError: If the identity is malformed.
    """
    if not isinstance(value, str) or _PROFILE_ID.fullmatch(value) is None:
        raise ValidationError("RES_INPUT_INVALID", "EXPECTANCY_PROFILE_ID_INVALID")


def _finite(value: float, *, detail: str, minimum: float | None = None) -> None:
    """Validate one finite bounded numeric statistic.

    Args:
        value: Candidate value.
        detail: Symbolic failure detail.
        minimum: Optional inclusive lower bound.

    Raises:
        ValidationError: If the value is non-finite or out of range.
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValidationError("RES_INPUT_INVALID", detail)
    if math.isnan(value) or math.isinf(value):
        raise ValidationError("RES_INPUT_INVALID", detail)
    if minimum is not None and value < minimum:
        raise ValidationError("RES_INPUT_INVALID", detail)


def _as_float(value: object, *, detail: str) -> float:
    """Coerce one JSON-safe value to a validated float.

    Args:
        value: Candidate JSON-safe numeric value.
        detail: Symbolic failure detail.

    Returns:
        Validated float.

    Raises:
        ValidationError: If the value is not a finite number.
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValidationError("RES_INPUT_INVALID", detail)
    result = float(value)
    if math.isnan(result) or math.isinf(result):
        raise ValidationError("RES_INPUT_INVALID", detail)
    return result


def _as_int(value: object, *, detail: str) -> int:
    """Coerce one JSON-safe value to a validated int.

    Args:
        value: Candidate JSON-safe integer value.
        detail: Symbolic failure detail.

    Returns:
        Validated int.

    Raises:
        ValidationError: If the value is not an integer.
    """
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValidationError("RES_INPUT_INVALID", detail)
    return value


def _as_str(value: object, *, detail: str) -> str:
    """Coerce one JSON-safe value to a validated non-empty string.

    Args:
        value: Candidate JSON-safe string value.
        detail: Symbolic failure detail.

    Returns:
        Validated non-empty string.

    Raises:
        ValidationError: If the value is not a non-empty string.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("RES_INPUT_INVALID", detail)
    return value


@dataclass(frozen=True, slots=True)
class ApprovedExpectancyProfile:
    """Immutable approved expectancy profile with governance lifecycle.

    Attributes:
        contract_version: Compatibility version; always ``v1``.
        schema_id: Stable namespaced schema identity.
        profile_id: Stable surrogate governance identity (OD-RES-01).
        exact_version: Version-exact identity referenced by Strategy/Risk.
        hypothesis: Tested question or declared research objective.
        strategy_ref: Strategy identity covered by the profile.
        instruments: Exact instrument scope of the approved edge.
        regimes: Exact regime scope of the approved edge.
        sessions: Exact session scope of the approved edge.
        sample_from_utc: Inclusive start of the approved sample window.
        sample_to_utc: Inclusive end of the approved sample window.
        sample_size: Number of observations backing the statistics.
        out_of_sample_status: Declared out-of-sample evidence status.
        win_rate: Observed win probability in ``[0, 1]``.
        avg_win_r: Average winning outcome magnitude in R-multiples.
        avg_loss_r: Average losing outcome magnitude in R-multiples (non-negative).
        expected_value_r: Expected value per trade in R-multiples.
        max_drawdown_r: Observed maximum drawdown magnitude in R-multiples.
        min_reward_risk: Minimum reward/risk override carried to Risk.
        governance_state: Lifecycle state of the profile.
        approved_at_utc: Approval instant, or ``None`` before approval.
        next_review_at_utc: Scheduled next review instant, or ``None``.
        expires_at_utc: Expiry instant, or ``None`` when not expiring.
        superseded_by: Surrogate identity superseding this profile, or ``None``.
        evidence_ref: Bounded evidence reference backing the profile.
        canonical_hash: Canonical SHA-256 of the profile material.
        advisory_only: Always ``True``; Research is advisory-only.
    """

    contract_version: Literal["v1"]
    schema_id: Literal["research.approved_expectancy_profile.v1"]
    profile_id: str
    exact_version: str
    hypothesis: str
    strategy_ref: str
    instruments: tuple[str, ...]
    regimes: tuple[str, ...]
    sessions: tuple[str, ...]
    sample_from_utc: datetime
    sample_to_utc: datetime
    sample_size: int
    out_of_sample_status: OutOfSampleStatus
    win_rate: float
    avg_win_r: float
    avg_loss_r: float
    expected_value_r: float
    max_drawdown_r: float
    min_reward_risk: float
    governance_state: GovernanceState
    approved_at_utc: datetime | None
    next_review_at_utc: datetime | None
    expires_at_utc: datetime | None
    superseded_by: str | None
    evidence_ref: str
    canonical_hash: str
    advisory_only: Literal[True] = field(default=True, init=False)

    def __post_init__(self) -> None:
        """Validate profile identity, bounds, and lifecycle consistency.

        Raises:
            ValidationError: If identity, statistics, or lifecycle are invalid.
            ConfigurationError: If the canonical hash does not match material.
        """
        _validate_profile_id(self.profile_id)
        _require_non_empty(self.exact_version, detail="EXPECTANCY_VERSION_EMPTY")
        _require_non_empty(self.hypothesis, detail="EXPECTANCY_HYPOTHESIS_EMPTY")
        _require_non_empty(self.strategy_ref, detail="EXPECTANCY_STRATEGY_REF_EMPTY")
        _require_non_empty(self.evidence_ref, detail="EXPECTANCY_EVIDENCE_REF_EMPTY")
        if not self.instruments or len(self.instruments) > _MAX_INSTRUMENTS:
            raise ValidationError("RES_INPUT_INVALID", "EXPECTANCY_INSTRUMENT_SCOPE")
        if self.sample_size < 1:
            raise ValidationError("RES_INPUT_INVALID", "EXPECTANCY_SAMPLE_SIZE")
        _utc(self.sample_from_utc)
        _utc(self.sample_to_utc)
        if self.sample_from_utc > self.sample_to_utc:
            raise ValidationError("RES_INPUT_INVALID", "EXPECTANCY_SAMPLE_WINDOW")
        _validate_profile_statistics(self)
        _validate_profile_lifecycle(self)
        if (
            not isinstance(self.canonical_hash, str)
            or _SHA256.fullmatch(self.canonical_hash) is None
        ):
            raise ValidationError("RES_INPUT_INVALID", "EXPECTANCY_HASH_INVALID")
        recomputed = canonical_digest(_canonical_material(self))
        if recomputed != self.canonical_hash:
            raise ConfigurationError(
                "RES_CONFIGURATION_INVALID", "EXPECTANCY_HASH_MISMATCH"
            )


def _validate_profile_statistics(profile: ApprovedExpectancyProfile) -> None:
    """Validate the bounded numeric statistics of one profile.

    Args:
        profile: Profile under construction.

    Raises:
        ValidationError: If any statistic is non-finite or out of range.
    """
    _finite(profile.win_rate, detail="EXPECTANCY_WIN_RATE", minimum=0.0)
    if profile.win_rate > 1.0:
        raise ValidationError("RES_INPUT_INVALID", "EXPECTANCY_WIN_RATE")
    _finite(profile.avg_win_r, detail="EXPECTANCY_AVG_WIN", minimum=0.0)
    _finite(profile.avg_loss_r, detail="EXPECTANCY_AVG_LOSS", minimum=0.0)
    _finite(profile.expected_value_r, detail="EXPECTANCY_EXPECTED_VALUE")
    _finite(profile.max_drawdown_r, detail="EXPECTANCY_DRAWDOWN")
    _finite(
        profile.min_reward_risk,
        detail="EXPECTANCY_MIN_REWARD_RISK",
        minimum=0.0,
    )


def _validate_profile_lifecycle(profile: ApprovedExpectancyProfile) -> None:
    """Validate optional timestamps and governance-lifecycle consistency.

    An approved profile must record an approval instant; non-approved states
    must not carry one. A superseded profile must be revoked. These rules keep
    the lifecycle consistent with no silent defaults.

    Args:
        profile: Profile under construction.

    Raises:
        ValidationError: If timestamps or lifecycle state conflict.
    """
    for timestamp in (
        profile.approved_at_utc,
        profile.next_review_at_utc,
        profile.expires_at_utc,
    ):
        if timestamp is not None:
            _utc(timestamp)
    if profile.governance_state == "approved":
        if profile.approved_at_utc is None:
            raise ValidationError(
                "RES_GOVERNANCE_TRANSITION_INVALID", "APPROVED_WITHOUT_TIMESTAMP"
            )
    elif profile.approved_at_utc is not None:
        raise ValidationError(
            "RES_GOVERNANCE_TRANSITION_INVALID", "TIMESTAMP_WITHOUT_APPROVAL"
        )
    if profile.superseded_by is not None:
        _validate_profile_id(profile.superseded_by)
        if profile.governance_state != "revoked":
            raise ValidationError(
                "RES_GOVERNANCE_TRANSITION_INVALID", "SUPERSEDED_NOT_REVOKED"
            )


def _canonical_material(profile: ApprovedExpectancyProfile) -> Mapping[str, object]:
    """Return the canonical hash material for one profile.

    Args:
        profile: Validated profile.

    Returns:
        Deterministic JSON-safe mapping fed to ``canonical_digest``.
    """
    return {
        "contract_version": profile.contract_version,
        "schema_id": profile.schema_id,
        "profile_id": profile.profile_id,
        "exact_version": profile.exact_version,
        "hypothesis": profile.hypothesis,
        "strategy_ref": profile.strategy_ref,
        "instruments": profile.instruments,
        "regimes": profile.regimes,
        "sessions": profile.sessions,
        "sample_from_utc": profile.sample_from_utc.isoformat(),
        "sample_to_utc": profile.sample_to_utc.isoformat(),
        "sample_size": profile.sample_size,
        "out_of_sample_status": profile.out_of_sample_status,
        "win_rate": profile.win_rate,
        "avg_win_r": profile.avg_win_r,
        "avg_loss_r": profile.avg_loss_r,
        "expected_value_r": profile.expected_value_r,
        "max_drawdown_r": profile.max_drawdown_r,
        "min_reward_risk": profile.min_reward_risk,
        "evidence_ref": profile.evidence_ref,
    }


def _parse_datetime(value: object) -> datetime | None:
    """Parse one optional UTC datetime from a JSON-safe mapping.

    Args:
        value: Candidate ISO-8601 string or ``None``.

    Returns:
        Parsed timezone-aware datetime, or ``None``.

    Raises:
        ValidationError: If the value is present but malformed.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        _utc(value)
        return value
    if not isinstance(value, str):
        raise ValidationError("RES_INPUT_INVALID", "EXPECTANCY_TIME_INVALID")
    parsed = datetime.fromisoformat(value)
    _utc(parsed)
    return parsed


def _parse_required_datetime(value: object, *, detail: str) -> datetime:
    """Parse one required UTC datetime from a JSON-safe mapping.

    Args:
        value: Candidate ISO-8601 string.
        detail: Symbolic failure detail.

    Returns:
        Parsed timezone-aware datetime.

    Raises:
        ValidationError: If the value is missing or malformed.
    """
    if value is None:
        raise ValidationError("RES_INPUT_INVALID", detail)
    if isinstance(value, datetime):
        _utc(value)
        return value
    if not isinstance(value, str):
        raise ValidationError("RES_INPUT_INVALID", detail)
    parsed = datetime.fromisoformat(value)
    _utc(parsed)
    return parsed


def build_approved_expectancy_profile(
    *,
    profile_id: str,
    exact_version: str,
    hypothesis: str,
    strategy_ref: str,
    instruments: tuple[str, ...],
    regimes: tuple[str, ...],
    sessions: tuple[str, ...],
    sample_from_utc: datetime,
    sample_to_utc: datetime,
    sample_size: int,
    out_of_sample_status: OutOfSampleStatus,
    win_rate: float,
    avg_win_r: float,
    avg_loss_r: float,
    expected_value_r: float,
    max_drawdown_r: float,
    min_reward_risk: float,
    governance_state: GovernanceState,
    approved_at_utc: datetime | None = None,
    next_review_at_utc: datetime | None = None,
    expires_at_utc: datetime | None = None,
    superseded_by: str | None = None,
    evidence_ref: str,
) -> dict[str, Any]:
    """Build a validated JSON-safe approved expectancy profile v1 mapping.

    Args:
        profile_id: Stable surrogate governance identity (``exp-`` prefixed).
        exact_version: Version-exact identity referenced by Strategy/Risk.
        hypothesis: Tested question or declared research objective.
        strategy_ref: Strategy identity covered by the profile.
        instruments: Exact instrument scope of the approved edge.
        regimes: Exact regime scope of the approved edge.
        sessions: Exact session scope of the approved edge.
        sample_from_utc: Inclusive start of the approved sample window.
        sample_to_utc: Inclusive end of the approved sample window.
        sample_size: Number of observations backing the statistics.
        out_of_sample_status: Declared out-of-sample evidence status.
        win_rate: Observed win probability in ``[0, 1]``.
        avg_win_r: Average winning outcome magnitude in R-multiples.
        avg_loss_r: Average losing outcome magnitude in R-multiples (non-negative).
        expected_value_r: Expected value per trade in R-multiples.
        max_drawdown_r: Observed maximum drawdown magnitude in R-multiples.
        min_reward_risk: Minimum reward/risk override carried to Risk.
        governance_state: Lifecycle state of the profile.
        approved_at_utc: Approval instant, or ``None`` before approval.
        next_review_at_utc: Scheduled next review instant, or ``None``.
        expires_at_utc: Expiry instant, or ``None`` when not expiring.
        superseded_by: Surrogate identity superseding this profile, or ``None``.
        evidence_ref: Bounded evidence reference backing the profile.

    Returns:
        JSON-safe profile mapping with ``canonical_hash``.

    Raises:
        ValidationError: If identity, statistics, or lifecycle are invalid.
        ConfigurationError: If canonical hashing fails.
    """
    material = {
        "contract_version": "v1",
        "schema_id": "research.approved_expectancy_profile.v1",
        "profile_id": profile_id,
        "exact_version": exact_version,
        "hypothesis": hypothesis,
        "strategy_ref": strategy_ref,
        "instruments": tuple(instruments),
        "regimes": tuple(regimes),
        "sessions": tuple(sessions),
        "sample_from_utc": sample_from_utc.isoformat(),
        "sample_to_utc": sample_to_utc.isoformat(),
        "sample_size": sample_size,
        "out_of_sample_status": out_of_sample_status,
        "win_rate": win_rate,
        "avg_win_r": avg_win_r,
        "avg_loss_r": avg_loss_r,
        "expected_value_r": expected_value_r,
        "max_drawdown_r": max_drawdown_r,
        "min_reward_risk": min_reward_risk,
        "evidence_ref": evidence_ref,
    }
    canonical_hash = canonical_digest(material)
    profile = ApprovedExpectancyProfile(
        contract_version="v1",
        schema_id="research.approved_expectancy_profile.v1",
        profile_id=profile_id,
        exact_version=exact_version,
        hypothesis=hypothesis,
        strategy_ref=strategy_ref,
        instruments=tuple(instruments),
        regimes=tuple(regimes),
        sessions=tuple(sessions),
        sample_from_utc=sample_from_utc,
        sample_to_utc=sample_to_utc,
        sample_size=sample_size,
        out_of_sample_status=out_of_sample_status,
        win_rate=win_rate,
        avg_win_r=avg_win_r,
        avg_loss_r=avg_loss_r,
        expected_value_r=expected_value_r,
        max_drawdown_r=max_drawdown_r,
        min_reward_risk=min_reward_risk,
        governance_state=governance_state,
        approved_at_utc=approved_at_utc,
        next_review_at_utc=next_review_at_utc,
        expires_at_utc=expires_at_utc,
        superseded_by=superseded_by,
        evidence_ref=evidence_ref,
        canonical_hash=canonical_hash,
    )
    return dict(to_json_safe(_profile_mapping(profile)))  # type: ignore[arg-type]


def _profile_mapping(profile: ApprovedExpectancyProfile) -> Mapping[str, object]:
    """Return the full transport mapping for one validated profile."""
    return {
        "contract_version": profile.contract_version,
        "schema_id": profile.schema_id,
        "profile_id": profile.profile_id,
        "exact_version": profile.exact_version,
        "hypothesis": profile.hypothesis,
        "strategy_ref": profile.strategy_ref,
        "instruments": profile.instruments,
        "regimes": profile.regimes,
        "sessions": profile.sessions,
        "sample_from_utc": profile.sample_from_utc.isoformat(),
        "sample_to_utc": profile.sample_to_utc.isoformat(),
        "sample_size": profile.sample_size,
        "out_of_sample_status": profile.out_of_sample_status,
        "win_rate": profile.win_rate,
        "avg_win_r": profile.avg_win_r,
        "avg_loss_r": profile.avg_loss_r,
        "expected_value_r": profile.expected_value_r,
        "max_drawdown_r": profile.max_drawdown_r,
        "min_reward_risk": profile.min_reward_risk,
        "governance_state": profile.governance_state,
        "approved_at_utc": (
            None
            if profile.approved_at_utc is None
            else profile.approved_at_utc.isoformat()
        ),
        "next_review_at_utc": (
            None
            if profile.next_review_at_utc is None
            else profile.next_review_at_utc.isoformat()
        ),
        "expires_at_utc": (
            None
            if profile.expires_at_utc is None
            else profile.expires_at_utc.isoformat()
        ),
        "superseded_by": profile.superseded_by,
        "evidence_ref": profile.evidence_ref,
        "canonical_hash": profile.canonical_hash,
        "advisory_only": True,
    }


def parse_approved_expectancy_profile(
    value: Mapping[str, object],
) -> dict[str, Any]:
    """Parse and fully validate an approved expectancy profile v1 mapping.

    Args:
        value: Candidate JSON-safe profile mapping.

    Returns:
        Re-validated JSON-safe profile mapping.

    Raises:
        ConfigurationError: If the supplied canonical hash does not match.
        ValidationError: If the mapping is structurally or semantically invalid.
    """
    if not isinstance(value, Mapping):
        raise ValidationError("RES_INPUT_INVALID", "EXPECTANCY_PROFILE_NOT_MAPPING")
    if value.get("contract_version") != "v1":
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "EXPECTANCY_VERSION")
    if value.get("schema_id") != "research.approved_expectancy_profile.v1":
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "EXPECTANCY_SCHEMA")
    if value.get("advisory_only") is not True:
        raise ValidationError("RES_INPUT_INVALID", "EXPECTANCY_NOT_ADVISORY")
    instruments = value.get("instruments")
    regimes = value.get("regimes")
    sessions = value.get("sessions")
    # JSON-safe transport represents tuples as lists; accept both forms.
    if not isinstance(instruments, (tuple, list)) or not isinstance(
        regimes, (tuple, list)
    ):
        raise ValidationError("RES_INPUT_INVALID", "EXPECTANCY_SCOPE_INVALID")
    if not isinstance(sessions, (tuple, list)):
        raise ValidationError("RES_INPUT_INVALID", "EXPECTANCY_SCOPE_INVALID")
    parsed = build_approved_expectancy_profile(
        profile_id=_as_str(value["profile_id"], detail="EXPECTANCY_PROFILE_ID_INVALID"),
        exact_version=_as_str(
            value["exact_version"], detail="EXPECTANCY_VERSION_EMPTY"
        ),
        hypothesis=_as_str(value["hypothesis"], detail="EXPECTANCY_HYPOTHESIS_EMPTY"),
        strategy_ref=_as_str(
            value["strategy_ref"], detail="EXPECTANCY_STRATEGY_REF_EMPTY"
        ),
        instruments=tuple(str(item) for item in instruments),
        regimes=tuple(str(item) for item in regimes),
        sessions=tuple(str(item) for item in sessions),
        sample_from_utc=_parse_required_datetime(
            value["sample_from_utc"], detail="EXPECTANCY_SAMPLE_FROM_INVALID"
        ),
        sample_to_utc=_parse_required_datetime(
            value["sample_to_utc"], detail="EXPECTANCY_SAMPLE_TO_INVALID"
        ),
        sample_size=_as_int(value["sample_size"], detail="EXPECTANCY_SAMPLE_SIZE"),
        out_of_sample_status=cast(
            "OutOfSampleStatus", str(value["out_of_sample_status"])
        ),
        win_rate=_as_float(value["win_rate"], detail="EXPECTANCY_WIN_RATE"),
        avg_win_r=_as_float(value["avg_win_r"], detail="EXPECTANCY_AVG_WIN"),
        avg_loss_r=_as_float(value["avg_loss_r"], detail="EXPECTANCY_AVG_LOSS"),
        expected_value_r=_as_float(
            value["expected_value_r"], detail="EXPECTANCY_EXPECTED_VALUE"
        ),
        max_drawdown_r=_as_float(value["max_drawdown_r"], detail="EXPECTANCY_DRAWDOWN"),
        min_reward_risk=_as_float(
            value["min_reward_risk"], detail="EXPECTANCY_MIN_REWARD_RISK"
        ),
        governance_state=cast("GovernanceState", str(value["governance_state"])),
        approved_at_utc=_parse_datetime(value.get("approved_at_utc")),
        next_review_at_utc=_parse_datetime(value.get("next_review_at_utc")),
        expires_at_utc=_parse_datetime(value.get("expires_at_utc")),
        superseded_by=(
            None if value.get("superseded_by") is None else str(value["superseded_by"])
        ),
        evidence_ref=str(value["evidence_ref"]),
    )
    if parsed["canonical_hash"] != value.get("canonical_hash"):
        raise ConfigurationError(
            "RES_CONFIGURATION_INVALID", "EXPECTANCY_HASH_MISMATCH"
        )
    return parsed


def expect_profile_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    """Return a frozen read-only view of one validated profile mapping.

    Args:
        value: JSON-safe profile mapping.

    Returns:
        Frozen mapping view.

    Raises:
        ValidationError: If the mapping fails validation.
    """
    return MappingProxyType(dict(parse_approved_expectancy_profile(value)))


__all__ = (
    "ApprovedExpectancyProfile",
    "build_approved_expectancy_profile",
    "expect_profile_mapping",
    "parse_approved_expectancy_profile",
)
