"""Bounded sentiment evidence output.

`SentimentEvidencePack` makes `FR-AGENTIC-030`'s separation structural: source
coverage, measured polarity, event classification, uncertainty, and unsupported
narrative are five distinct fields, so a narrative the evidence does not
support cannot be presented as a measurement.

Four of the five come from what Research projected. `unsupported_narrative` is
the only field the model fills freely, and its name says what it is — the part
of the reading the measurements do not back. Keeping it separate rather than
forbidding it is the point: an analyst that noticed something the lexicon
cannot measure should say so, in the field labelled as not evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from app.agentic.deliberation.models import reject_authorization_language
from app.composition.logging import get_logger

logger = get_logger(__name__)

_MAX_TEXT = 2_000
_MAX_SHORT_TEXT = 200
_MAX_ITEMS = 64

_MIN_STATEMENT_TEXT = 24

# Wording that would turn a measurement into a recommendation.
_DIRECTIVE_PHRASES: tuple[str, ...] = (
    "you should buy",
    "you should sell",
    "we recommend",
    "recommend buying",
    "recommend selling",
    "target price",
    "price target",
    "entry price",
    "stop loss",
)


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
    """Validate text that must report a measurement rather than direct a trade.

    Args:
        value: Candidate text.
        field: Safe field label for validation.

    Returns:
        The validated text.

    Raises:
        ValueError: If the text reads as a recommendation.
    """
    checked = reject_authorization_language(_text(value, field), field)
    lowered = checked.lower()
    for phrase in _DIRECTIVE_PHRASES:
        if phrase in lowered:
            message = (
                f"{field} must not recommend an action or name a price; "
                "sentiment research reports what was measured"
            )
            raise ValueError(message)
    return checked


def _keyed(value: Mapping[str, str], field: str) -> Mapping[str, str]:
    """Validate and freeze one bounded keyed mapping.

    Args:
        value: Candidate mapping.
        field: Safe field label for validation.

    Returns:
        Deterministically ordered read-only mapping.

    Raises:
        ValueError: If the mapping is oversized or an entry is invalid.
    """
    if len(value) > _MAX_ITEMS:
        message = f"{field} must not exceed {_MAX_ITEMS} entries"
        raise ValueError(message)
    frozen = {
        _text(key, f"{field} key", limit=_MAX_SHORT_TEXT): _text(
            item,
            f"{field} entry",
            limit=_MAX_SHORT_TEXT,
        )
        for key, item in sorted(value.items())
    }
    return MappingProxyType(frozen)


def _entries(value: tuple[str, ...], field: str) -> tuple[str, ...]:
    """Validate one bounded optional tuple.

    Args:
        value: Candidate entries.
        field: Safe field label for validation.

    Returns:
        Validated entries.

    Raises:
        ValueError: If the tuple is oversized.
    """
    if len(value) > _MAX_ITEMS:
        message = f"{field} must not exceed {_MAX_ITEMS} entries"
        raise ValueError(message)
    return tuple(_advisory(_text(item, field), field) for item in value)


class SentimentEvidencePack(BaseModel):
    """One bounded advisory reading of point-in-time text evidence.

    Attributes:
        pack_id: Stable pack identity.
        task_id: Owning task identity.
        instrument: Instrument the reading concerns.
        asset_class: Normalized asset class the applicability decision used.
        measurement_version: Deterministic version Research measured under.
        source_coverage: Receiver-reported document counts per source kind.
        polarity: Receiver-measured polarity per document reference.
        event_classification: Events the analyst identified, by reference.
        uncertainty: What the measurements could not establish.
        unsupported_narrative: Readings the measurements do not support.
        evidence_refs: Document references the reading rests on.
        excluded_refs: References excluded as suspected instruction.
        trust_evidence: Receiver-reported source trust per reference.
        manipulation_evidence: Receiver-reported manipulation signals.
        disagreement: Whether the measurements disagreed with one another.
        missing_measurements: References the lexicon could not measure.
        available_by: Instant by which every document was publicly available.
        canonical_hash: Research's digest of the evidence read.
        issued_at: Issue instant, as an ISO-8601 UTC string.
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
    asset_class: str
    measurement_version: str
    source_coverage: Mapping[str, str]
    polarity: Mapping[str, str]
    event_classification: Mapping[str, str]
    uncertainty: str
    unsupported_narrative: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    excluded_refs: tuple[str, ...]
    trust_evidence: Mapping[str, str]
    manipulation_evidence: Mapping[str, str]
    disagreement: bool
    missing_measurements: tuple[str, ...]
    available_by: str
    canonical_hash: str
    issued_at: str

    @field_validator(
        "pack_id",
        "task_id",
        "instrument",
        "asset_class",
        "measurement_version",
        "available_by",
        "canonical_hash",
        "issued_at",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required pack reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "pack reference", limit=_MAX_SHORT_TEXT)

    @field_validator(
        "source_coverage",
        "polarity",
        "event_classification",
        "trust_evidence",
        "manipulation_evidence",
    )
    @classmethod
    def _validate_mapping(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze one keyed mapping.

        Args:
            value: Candidate mapping.

        Returns:
            Frozen ordered mapping.
        """
        return _keyed(value, "sentiment field")

    @field_validator("evidence_refs")
    @classmethod
    def _validate_evidence(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the required supporting references.

        Args:
            value: Candidate references.

        Returns:
            Validated references.

        Raises:
            ValueError: If no reference supports the reading.
        """
        if not value:
            message = "a sentiment pack must rest on at least one document"
            raise ValueError(message)
        return _entries(value, "sentiment reference")

    @field_validator("excluded_refs", "missing_measurements", "unsupported_narrative")
    @classmethod
    def _validate_optional(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one bounded optional tuple.

        Args:
            value: Candidate entries.

        Returns:
            Validated entries.
        """
        return _entries(value, "sentiment entry")

    @field_validator("uncertainty")
    @classmethod
    def _validate_uncertainty(cls, value: str) -> str:
        """Validate the uncertainty statement.

        Args:
            value: Candidate statement.

        Returns:
            Validated statement.

        Raises:
            ValueError: If the statement is too short to be one.
        """
        checked = _advisory(_text(value, "uncertainty"), "uncertainty")
        if len(checked) < _MIN_STATEMENT_TEXT:
            message = (
                "state what the measurements could not establish; a pack "
                "without its uncertainty misrepresents its own basis"
            )
            raise ValueError(message)
        return checked

    @field_serializer(
        "source_coverage",
        "polarity",
        "event_classification",
        "trust_evidence",
        "manipulation_evidence",
        mode="plain",
    )
    def _serialize_mapping(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize one frozen mapping deterministically.

        Args:
            value: Frozen mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


def build_sentiment_evidence_pack(
    fields: Mapping[str, object],
) -> SentimentEvidencePack:
    """Build one bounded sentiment evidence pack.

    Args:
        fields: Complete pack fields.

    Returns:
        A validated immutable pack.
    """
    logger.debug("Building a sentiment evidence pack")
    return SentimentEvidencePack.model_validate(fields)
