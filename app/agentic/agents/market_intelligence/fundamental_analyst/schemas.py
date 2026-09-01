"""Bounded fundamental evidence output.

`FundamentalEvidencePack` makes `FR-AGENTIC-027` structural: claims,
assumptions, horizons, and falsifiers are validated as **parallel key sets**,
so a claim without a stated falsifier is unrepresentable rather than merely
discouraged. A fundamental view that cannot be shown wrong is not a view.

The pack carries no computed number. Coverage, document references, source
kinds, and the canonical hash are copied from what Research projected, so the
model describes evidence rather than producing it, and `advisory_only` is
carried verbatim from the projection rather than asserted here.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from app.agentic.deliberation.models import reject_authorization_language
from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest

logger = get_logger(__name__)

_MAX_TEXT = 2_000
_MAX_SHORT_TEXT = 200
_MAX_ITEMS = 32

# A claim, assumption, horizon, or falsifier shorter than this is not one. The
# bound catches "n/a" and "unknown", not brevity.
_MIN_STATEMENT_TEXT = 24

# Wording that would turn evidence into a recommendation. Fundamental research
# describes what the filings say; it does not tell anyone what to do.
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
    """Validate text that must describe evidence rather than direct a trade.

    `FEAT-AGT-07` owns what reads as an authorization and is reused rather than
    restated; this adds only the recommendation vocabulary a research role must
    not emit.

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
                "fundamental research describes evidence"
            )
            raise ValueError(message)
    return checked


def _statements(value: Mapping[str, str], field: str) -> Mapping[str, str]:
    """Validate and freeze one bounded keyed statement mapping.

    Args:
        value: Candidate mapping.
        field: Safe field label for validation.

    Returns:
        Deterministically ordered read-only mapping.

    Raises:
        ValueError: If the mapping is empty, oversized, or an entry is too
            short to be a statement.
    """
    if not value:
        message = f"{field} is required"
        raise ValueError(message)
    if len(value) > _MAX_ITEMS:
        message = f"{field} must not exceed {_MAX_ITEMS} entries"
        raise ValueError(message)
    frozen: dict[str, str] = {}
    for key, item in sorted(value.items()):
        checked = _advisory(_text(item, field), field)
        if len(checked) < _MIN_STATEMENT_TEXT:
            message = (
                f"the {key!r} {field} is too short to be one; state what the "
                "evidence shows, or omit the claim"
            )
            raise ValueError(message)
        frozen[_text(key, f"{field} key", limit=_MAX_SHORT_TEXT)] = checked
    return MappingProxyType(frozen)


def _refs(value: tuple[str, ...], field: str) -> tuple[str, ...]:
    """Validate one required bounded reference tuple.

    Args:
        value: Candidate references.
        field: Safe field label for validation.

    Returns:
        Validated references.

    Raises:
        ValueError: If the tuple is empty or oversized.
    """
    if not value:
        message = f"{field} is required"
        raise ValueError(message)
    if len(value) > _MAX_ITEMS:
        message = f"{field} must not exceed {_MAX_ITEMS} entries"
        raise ValueError(message)
    return tuple(_text(item, field, limit=_MAX_SHORT_TEXT) for item in value)


class FundamentalEvidencePack(BaseModel):
    """One bounded advisory reading of point-in-time fundamental evidence.

    Attributes:
        pack_id: Stable pack identity.
        task_id: Owning task identity.
        instrument: Instrument the reading concerns.
        asset_class: Normalized asset class the applicability decision used.
        model: Fundamental model Research applied.
        claims: What the evidence supports, by claim identifier.
        assumptions: What each claim assumes, by the same identifiers.
        horizons: Over what period each claim is asserted to hold.
        falsifiers: What would show each claim to be wrong.
        evidence_refs: Document references the reading rests on.
        source_kinds: Source kinds Research found eligible.
        coverage: Receiver-reported coverage counts per kind.
        observed_from: Earliest observation instant in the evidence.
        available_by: Instant by which every document was publicly available.
        uncertainty: What the evidence cannot establish.
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
    model: str
    claims: Mapping[str, str]
    assumptions: Mapping[str, str]
    horizons: Mapping[str, str]
    falsifiers: Mapping[str, str]
    evidence_refs: tuple[str, ...]
    source_kinds: tuple[str, ...]
    coverage: Mapping[str, str]
    observed_from: str
    available_by: str
    uncertainty: str
    canonical_hash: str
    issued_at: str

    @field_validator(
        "pack_id",
        "task_id",
        "instrument",
        "asset_class",
        "model",
        "observed_from",
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

    @field_validator("claims", "assumptions", "horizons", "falsifiers")
    @classmethod
    def _validate_statements(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze one keyed statement mapping.

        Args:
            value: Candidate mapping.

        Returns:
            Frozen ordered mapping.
        """
        return _statements(value, "fundamental statement")

    @field_validator("coverage")
    @classmethod
    def _validate_coverage(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze the receiver-reported coverage.

        Args:
            value: Candidate mapping.

        Returns:
            Frozen ordered mapping.

        Raises:
            ValueError: If no coverage is reported.
        """
        if not value:
            message = "a fundamental pack must carry the coverage Research reported"
            raise ValueError(message)
        if len(value) > _MAX_ITEMS:
            message = f"coverage must not exceed {_MAX_ITEMS} entries"
            raise ValueError(message)
        frozen = {
            _text(key, "coverage kind", limit=_MAX_SHORT_TEXT): _text(
                item,
                "coverage count",
                limit=_MAX_SHORT_TEXT,
            )
            for key, item in sorted(value.items())
        }
        return MappingProxyType(frozen)

    @field_validator("evidence_refs", "source_kinds")
    @classmethod
    def _validate_refs(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one required reference tuple.

        Args:
            value: Candidate references.

        Returns:
            Validated references.
        """
        return _refs(value, "fundamental reference")

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
                "state what the evidence could not establish; a pack without "
                "its uncertainty misrepresents its own basis"
            )
            raise ValueError(message)
        return checked

    @field_serializer(
        "claims",
        "assumptions",
        "horizons",
        "falsifiers",
        "coverage",
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


def missing_parallel_keys(pack_fields: Mapping[str, object]) -> tuple[str, ...]:
    """Return the statement fields whose key sets do not match the claims.

    Args:
        pack_fields: Candidate pack fields.

    Returns:
        Ordered field names whose keys diverge from the claim keys.
    """
    claims = pack_fields.get("claims")
    if not isinstance(claims, Mapping):
        return ("claims",)
    expected = set(claims)
    diverged: list[str] = []
    for field in ("assumptions", "horizons", "falsifiers"):
        value = pack_fields.get(field)
        if not isinstance(value, Mapping) or set(value) != expected:
            diverged.append(field)
    return tuple(diverged)


def build_fundamental_evidence_pack(
    fields: Mapping[str, object],
) -> FundamentalEvidencePack:
    """Build one bounded fundamental evidence pack.

    Claims, assumptions, horizons, and falsifiers must share an identical key
    set. A claim the analyst cannot say how to falsify is not admissible, and
    the parallel key sets make that a construction error rather than a review
    finding.

    Args:
        fields: Complete pack fields.

    Returns:
        A validated immutable pack.

    Raises:
        ValueError: If the statement key sets diverge.
    """
    diverged = missing_parallel_keys(fields)
    if diverged:
        message = (
            "every claim needs its own assumption, horizon, and falsifier; "
            f"these do not match the claim keys: {', '.join(diverged)}"
        )
        raise ValueError(message)
    logger.debug("Building a fundamental evidence pack")
    return FundamentalEvidencePack.model_validate(fields)


def derive_pack_hash(fields: Mapping[str, object]) -> str:
    """Derive the content digest of one fundamental pack.

    Args:
        fields: Pack fields.

    Returns:
        The canonical content digest.
    """
    return canonical_digest(dict(sorted(fields.items())))
