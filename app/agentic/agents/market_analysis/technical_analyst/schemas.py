"""Typed output for the Technical Analyst.

`TechnicalEvidencePack` makes two requirements structural rather than advisory.

`FR-AGENTIC-032`: instrument, venue, timeframe, session, observation window,
indicator versions, and data-quality evidence are **required fields**. A pack
that does not bind its reading to an exact context cannot be constructed.

`FR-AGENTIC-033`: claims, confirmations, invalidations, and leakage notes are
four mappings keyed by the same claim identifier, and validation requires the
key sets to match exactly. A claim without a confirmation, an invalidation, or
a leakage-safe evaluation note is therefore unrepresentable.

The schema carries no numeric field, so a recomputed indicator value has
nowhere to live (`FR-AGENTIC-031`).
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from app.composition.logging import get_logger

logger = get_logger(__name__)

_MAX_TEXT = 2_000
_MAX_SHORT_TEXT = 200
_MAX_ITEMS = 32

# A technical reading is advisory evidence. Language that reads as an order, an
# approval, or a size would misrepresent it as a decision.
_PROHIBITED_PHRASES: tuple[str, ...] = (
    "approved",
    "i approve",
    "authorization granted",
    "position size",
    "position_size",
    "lot size",
    "lot_size",
    "place the order",
    "execute this trade",
    "entry price",
    "stop loss at",
    "take profit at",
)

QualityStatus = Literal["passed", "warned", "failed", "calendar_unverified"]


def _text(value: str, field: str, *, limit: int = _MAX_TEXT) -> str:
    """Validate bounded non-empty trimmed text.

    Args:
        value: Candidate text.
        field: Safe field label for validation.
        limit: Maximum permitted character count.

    Returns:
        Validated text.

    Raises:
        ValueError: If the text is empty, untrimmed, or oversized.
    """
    if not value or value != value.strip():
        message = f"{field} must be non-empty trimmed text"
        raise ValueError(message)
    if len(value) > limit:
        message = f"{field} must not exceed {limit} characters"
        raise ValueError(message)
    return value


def _advisory(value: str, field: str) -> str:
    """Reject text that would read as an order, approval, or position size.

    Args:
        value: Candidate advisory text.
        field: Safe field label for validation.

    Returns:
        The unchanged text.

    Raises:
        ValueError: If the text carries execution or approval language.
    """
    lowered = value.lower()
    for phrase in _PROHIBITED_PHRASES:
        if phrase in lowered:
            message = (
                f"{field} must not carry approval, order, or position-size "
                "language; a technical reading is advisory evidence only"
            )
            raise ValueError(message)
    return value


def _utc(value: datetime, field: str) -> datetime:
    """Validate an aware UTC timestamp.

    Args:
        value: Candidate timestamp.
        field: Safe field label for validation.

    Returns:
        Validated UTC timestamp.

    Raises:
        ValueError: If the value is naive or not UTC.
    """
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        message = f"{field} must be aware UTC"
        raise ValueError(message)
    return value


def _keyed(value: Mapping[str, str], field: str) -> Mapping[str, str]:
    """Validate and freeze one bounded claim-keyed mapping.

    Args:
        value: Candidate mapping.
        field: Safe field label for validation.

    Returns:
        Deterministically ordered read-only mapping.

    Raises:
        ValueError: If the mapping is oversized or a statement is invalid.
    """
    if len(value) > _MAX_ITEMS:
        message = f"{field} must not exceed {_MAX_ITEMS} entries"
        raise ValueError(message)
    frozen = {
        _text(key, f"{field} key", limit=_MAX_SHORT_TEXT): _advisory(
            _text(item, f"{field} statement"),
            field,
        )
        for key, item in sorted(value.items())
    }
    return MappingProxyType(frozen)


class TechnicalEvidencePack(BaseModel):
    """One bound technical reading of canonical market and indicator evidence.

    Attributes:
        pack_id: Stable pack identity.
        task_id: Owning task identity.
        instrument: Canonical instrument the reading is bound to.
        venue: Venue or provider the evidence came from.
        timeframe: Canonical timeframe of the observation.
        session: Session label covering the observation window.
        observation_start: UTC start of the observation window.
        observation_end: UTC end of the observation window.
        indicator_versions: Registered indicator name to exact version used.
        data_quality_status: Quality classification of the underlying dataset.
        data_quality_ref: Reference to the quality evidence.
        market_evidence_ref: Reference to the canonical market dataset.
        claims: Structure or regime claims, by claim identifier.
        confirmations: Confirming condition per claim identifier.
        invalidations: Invalidating condition per claim identifier.
        leakage_notes: Leakage-safe evaluation note per claim identifier.
        uncertainty: Bounded statement of the basis and its limits.
        conflicts: Preserved incompatible readings.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    pack_id: str
    task_id: str
    instrument: str
    venue: str
    timeframe: str
    session: str
    observation_start: datetime
    observation_end: datetime
    indicator_versions: Mapping[str, str]
    data_quality_status: QualityStatus
    data_quality_ref: str
    market_evidence_ref: str
    claims: Mapping[str, str]
    confirmations: Mapping[str, str]
    invalidations: Mapping[str, str]
    leakage_notes: Mapping[str, str]
    uncertainty: str
    conflicts: tuple[str, ...] = ()

    @field_validator(
        "pack_id",
        "task_id",
        "instrument",
        "venue",
        "timeframe",
        "session",
        "data_quality_ref",
        "market_evidence_ref",
    )
    @classmethod
    def _validate_binding(cls, value: str) -> str:
        """Validate one required binding reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "technical binding", limit=_MAX_SHORT_TEXT)

    @field_validator("observation_start", "observation_end")
    @classmethod
    def _validate_window(cls, value: datetime) -> datetime:
        """Validate one observation-window boundary.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        return _utc(value, "observation window")

    @field_validator("indicator_versions")
    @classmethod
    def _validate_indicator_versions(
        cls,
        value: Mapping[str, str],
    ) -> Mapping[str, str]:
        """Validate and freeze the registered indicator versions.

        Args:
            value: Candidate indicator-version mapping.

        Returns:
            Frozen ordered mapping.

        Raises:
            ValueError: If no indicator version is recorded.
        """
        if not value:
            message = (
                "indicator_versions is required; a technical reading must name "
                "the exact registered indicator definitions it used"
            )
            raise ValueError(message)
        return _keyed(value, "indicator_versions")

    @field_validator("claims", "confirmations", "invalidations", "leakage_notes")
    @classmethod
    def _validate_claim_mapping(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze one claim-keyed mapping.

        Args:
            value: Candidate mapping.

        Returns:
            Frozen ordered mapping.
        """
        return _keyed(value, "claim mapping")

    @field_validator("uncertainty")
    @classmethod
    def _validate_uncertainty(cls, value: str) -> str:
        """Validate the bounded uncertainty statement.

        Args:
            value: Candidate uncertainty statement.

        Returns:
            Validated uncertainty statement.
        """
        return _advisory(_text(value, "uncertainty"), "uncertainty")

    @field_validator("conflicts")
    @classmethod
    def _validate_conflicts(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the preserved incompatible readings.

        Args:
            value: Candidate conflict statements.

        Returns:
            Validated conflict statements.

        Raises:
            ValueError: If the tuple is oversized.
        """
        if len(value) > _MAX_ITEMS:
            message = f"conflicts must not exceed {_MAX_ITEMS} entries"
            raise ValueError(message)
        return tuple(_advisory(_text(item, "conflict"), "conflict") for item in value)

    @model_validator(mode="after")
    def _validate_pack(self) -> Self:
        """Validate the window and the claim-completeness invariant.

        Returns:
            The validated pack.

        Raises:
            ValueError: If the window is inverted, or any claim lacks a
                confirmation, an invalidation, or a leakage-safe note.
        """
        if self.observation_start >= self.observation_end:
            message = "observation_start must precede observation_end"
            raise ValueError(message)
        claim_ids = set(self.claims)
        for label, mapping in (
            ("confirmations", self.confirmations),
            ("invalidations", self.invalidations),
            ("leakage_notes", self.leakage_notes),
        ):
            missing = sorted(claim_ids - set(mapping))
            if missing:
                message = (
                    f"every claim requires {label}; missing for: {', '.join(missing)}"
                )
                raise ValueError(message)
            orphaned = sorted(set(mapping) - claim_ids)
            if orphaned:
                message = (
                    f"{label} names claims that do not exist: {', '.join(orphaned)}"
                )
                raise ValueError(message)
        return self

    @field_serializer(
        "indicator_versions",
        "claims",
        "confirmations",
        "invalidations",
        "leakage_notes",
        mode="plain",
    )
    def _serialize_mapping(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize one bounded mapping deterministically.

        Args:
            value: Frozen mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


def build_technical_evidence_pack(
    fields: Mapping[str, object],
) -> TechnicalEvidencePack:
    """Build one bound technical evidence pack.

    Args:
        fields: Complete pack fields.

    Returns:
        A validated immutable technical evidence pack.
    """
    logger.debug("Building a technical evidence pack")
    return TechnicalEvidencePack.model_validate(fields)
