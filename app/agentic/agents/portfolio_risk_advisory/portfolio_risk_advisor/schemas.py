"""Non-binding allocation proposals and independent risk advisories.

`AllocationProposal` makes non-binding structural rather than adjectival
(`FR-AGENTIC-055`). Three separate facts carry it: there is no executable
quantity anywhere in the model — weights are bounded strings, and no lot size,
notional, or order field exists to be handed to an execution path even by
mistake; approval language is refused through `FEAT-AGT-07`'s
`reject_authorization_language`, so the domain keeps one definition of what
reads as an authorization; and expiry is mandatory and strict, so an
already-expired proposal cannot be constructed at all.

`RiskAdvisory` makes risk coverage exact (`FR-AGENTIC-056`): all eight risk
kinds must be assessed, validated by set equality, so an advisory that never
looked at liquidity is unrepresentable rather than merely thinner. It emits no
approval by absence — there is no verdict, no boolean, and no field a caller
could read as consent.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from types import MappingProxyType
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from app.agentic.deliberation.models import reject_authorization_language
from app.utils import canonical_digest, get_logger

logger = get_logger(__name__)

_MAX_TEXT = 2_000
_MAX_SHORT_TEXT = 200
_MAX_ITEMS = 32

# `FR-AGENTIC-056`. Every advisory assesses all eight, validated by set
# equality: an advisory that never looked at liquidity is not a weaker
# advisory but an impossible one, and a ninth kind nobody agreed to is refused
# just as firmly.
REQUIRED_RISK_KINDS: frozenset[str] = frozenset(
    {
        "barrier",
        "concentration",
        "correlation",
        "liquidity",
        "mandate",
        "model",
        "operational",
        "tail",
    },
)

# An assessment shorter than this is not an assessment. The bound is
# deliberately low: it catches "n/a" and "fine", not brevity.
_MIN_ASSESSMENT_TEXT = 24

# Wording that turns a risk critique into a blessing. A critic saying these
# things has stopped doing the job the role exists for.
_NON_CRITICAL_PHRASES: tuple[str, ...] = (
    "no concerns",
    "no issues",
    "nothing to flag",
    "looks good",
    "lgtm",
    "not applicable",
    "risk free",
    "risk-free",
)

# Vocabulary that turns advice into something executable. `FEAT-AGT-07`'s
# `reject_authorization_language` owns what reads as an *authorization*, and it
# is reused rather than restated; this list adds the level-and-price vocabulary
# specific to an advisor. Naming an entry price authorizes nothing in the
# deliberation sense, but it produces a value an execution path could consume,
# which is precisely what a non-binding proposal must not contain.
_EXECUTABLE_PHRASES: tuple[str, ...] = (
    "buy at",
    "deploy to live",
    "entry price",
    "entry_price",
    "sell at",
    "stop loss",
    "stop-loss",
    "stop_loss",
    "take profit",
    "take-profit",
    "take_profit",
    "units of",
)

# Field names that would make a proposal executable. The model has no field of
# this shape, and a test asserts none appears; the tuple states the intent so a
# later change has to argue with it.
FORBIDDEN_EXECUTABLE_FIELDS: tuple[str, ...] = (
    "approved",
    "entry_price",
    "lot_size",
    "lots",
    "notional",
    "order",
    "position_size",
    "quantity",
    "stop_loss",
    "take_profit",
    "units",
    "volume",
)


def missing_risk_kinds(assessments: Mapping[str, str]) -> tuple[str, ...]:
    """Return the required risk kinds an advisory does not assess.

    Args:
        assessments: Assessed risk kind to statement.

    Returns:
        Ordered missing risk kinds.
    """
    return tuple(sorted(REQUIRED_RISK_KINDS - set(assessments)))


def unknown_risk_kinds(assessments: Mapping[str, str]) -> tuple[str, ...]:
    """Return assessed kinds that are not required risk kinds.

    Args:
        assessments: Assessed risk kind to statement.

    Returns:
        Ordered unrecognized risk kinds.
    """
    return tuple(sorted(set(assessments) - REQUIRED_RISK_KINDS))


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


def _advisory_text(value: str, field: str) -> str:
    """Validate text that must read as advice rather than as an instruction.

    Args:
        value: Candidate text.
        field: Safe field label for validation.

    Returns:
        The validated text.

    Raises:
        ValueError: If the text carries executable level or price vocabulary.
    """
    checked = reject_authorization_language(_text(value, field), field)
    lowered = checked.lower()
    for phrase in _EXECUTABLE_PHRASES:
        if phrase in lowered:
            message = (
                f"{field} must not name an executable level or price; advice "
                "describes relative emphasis, not an order"
            )
            raise ValueError(message)
    return checked


def _entries(
    value: tuple[str, ...], field: str, *, required: bool = False
) -> tuple[
    str,
    ...,
]:
    """Validate one bounded tuple of advisory statements.

    Args:
        value: Candidate entries.
        field: Safe field label for validation.
        required: Whether the tuple must carry at least one entry.

    Returns:
        Validated entries.

    Raises:
        ValueError: If the tuple is empty when required, or oversized.
    """
    if required and not value:
        message = f"{field} is required"
        raise ValueError(message)
    if len(value) > _MAX_ITEMS:
        message = f"{field} must not exceed {_MAX_ITEMS} entries"
        raise ValueError(message)
    return tuple(_advisory_text(item, field) for item in value)


def _keyed(
    value: Mapping[str, str],
    field: str,
    *,
    limit: int = _MAX_TEXT,
) -> Mapping[str, str]:
    """Validate and freeze one bounded keyed advisory mapping.

    Args:
        value: Candidate mapping.
        field: Safe field label for validation.
        limit: Maximum permitted characters per value.

    Returns:
        Deterministically ordered read-only mapping.

    Raises:
        ValueError: If the mapping is oversized or an entry is invalid.
    """
    if len(value) > _MAX_ITEMS:
        message = f"{field} must not exceed {_MAX_ITEMS} entries"
        raise ValueError(message)
    frozen = {
        _text(key, f"{field} key", limit=_MAX_SHORT_TEXT): _advisory_text(
            _text(item, f"{field} entry", limit=limit),
            field,
        )
        for key, item in sorted(value.items())
    }
    return MappingProxyType(frozen)


class AllocationProposal(BaseModel):
    """One non-binding allocation view carrying its own expiry.

    Nothing here is executable. `relative_weights` are bounded strings keyed by
    candidate, and the model defines no quantity, price, or order field, so
    there is no value in it that an execution path could consume.

    Attributes:
        proposal_id: Stable proposal identity.
        task_id: Owning task identity.
        portfolio_id: Portfolio this proposal concerns.
        mandate_id: Risk-owned mandate the proposal was bounded by.
        mandate_version: Version of that mandate.
        asset_class: Mandate asset scope the proposal stays within.
        base_currency: Mandate base currency.
        relative_weights: Candidate identity to bounded relative emphasis.
        rationale: Why the emphasis follows from the evidence.
        constraints_respected: Mandate constraints the proposal stays within.
        evidence_refs: Receiver-returned references this proposal rests on.
        evidence_observed_at: Observation instant per evidence kind.
        limitations: What this proposal cannot establish.
        issued_at: Issue instant, as an ISO-8601 UTC string.
        expires_at: Expiry instant, as an ISO-8601 UTC string.
        proposal_hash: Derived digest over the whole proposal.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    proposal_id: str
    task_id: str
    portfolio_id: str
    mandate_id: str
    mandate_version: str
    asset_class: str
    base_currency: str
    relative_weights: Mapping[str, str]
    rationale: str
    constraints_respected: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    evidence_observed_at: Mapping[str, str]
    limitations: tuple[str, ...]
    issued_at: str
    expires_at: str
    proposal_hash: str

    @field_validator(
        "proposal_id",
        "task_id",
        "portfolio_id",
        "mandate_id",
        "mandate_version",
        "asset_class",
        "base_currency",
        "issued_at",
        "expires_at",
        "proposal_hash",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required proposal reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "proposal reference", limit=_MAX_SHORT_TEXT)

    @field_validator("relative_weights")
    @classmethod
    def _validate_weights(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate the bounded relative emphasis per candidate.

        Args:
            value: Candidate mapping.

        Returns:
            Frozen ordered mapping.

        Raises:
            ValueError: If no candidate is described.
        """
        if not value:
            message = "an allocation proposal must describe at least one candidate"
            raise ValueError(message)
        return _keyed(value, "relative weight", limit=_MAX_SHORT_TEXT)

    @field_validator("evidence_observed_at")
    @classmethod
    def _validate_observations(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate the observation instant per evidence kind.

        Args:
            value: Candidate mapping.

        Returns:
            Frozen ordered mapping.

        Raises:
            ValueError: If no observation time is recorded.
        """
        if not value:
            message = "an allocation proposal must record when its evidence was read"
            raise ValueError(message)
        return _keyed(value, "evidence observation", limit=_MAX_SHORT_TEXT)

    @field_validator("rationale")
    @classmethod
    def _validate_rationale(cls, value: str) -> str:
        """Validate the proposal rationale.

        Args:
            value: Candidate rationale.

        Returns:
            Validated rationale.
        """
        return _advisory_text(value, "proposal rationale")

    @field_validator("constraints_respected", "evidence_refs", "limitations")
    @classmethod
    def _validate_required_entries(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one required bounded proposal tuple.

        Args:
            value: Candidate entries.

        Returns:
            Validated entries.
        """
        return _entries(value, "proposal entry", required=True)

    @field_serializer("relative_weights", "evidence_observed_at", mode="plain")
    def _serialize_mapping(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize one frozen mapping deterministically.

        Args:
            value: Frozen mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)

    @model_validator(mode="after")
    def _validate_expiry(self) -> Self:
        """Validate that the proposal expires strictly after it was issued.

        Returns:
            The validated proposal.

        Raises:
            ValueError: If either instant is unreadable, or expiry does not
                strictly follow issue.
        """
        issued = _instant(self.issued_at, "issued_at")
        expires = _instant(self.expires_at, "expires_at")
        if expires <= issued:
            message = (
                "an allocation proposal must expire strictly after it was issued; "
                f"{self.expires_at} does not follow {self.issued_at}"
            )
            raise ValueError(message)
        return self

    def is_expired(self, at_time: datetime) -> bool:
        """Report whether the proposal has passed its own expiry.

        Args:
            at_time: Instant to judge the proposal at.

        Returns:
            True when the proposal is no longer current.
        """
        return at_time >= _instant(self.expires_at, "expires_at")


class RiskAdvisory(BaseModel):
    """One independent risk critique that authorizes nothing.

    There is no verdict field, no approval flag, and no severity that could be
    read as consent. What the advisory carries is what was examined and what
    remains unresolved.

    Attributes:
        advisory_id: Stable advisory identity.
        task_id: Owning task identity.
        proposal_id: Proposal this advisory critiques.
        proposal_hash: Digest of the proposal as critiqued.
        portfolio_id: Portfolio this advisory concerns.
        assessments: Bounded assessment per required risk kind.
        unresolved_risks: Risks this critique could not close.
        retained_dissent: Minority positions preserved from deliberation.
        evidence_refs: Receiver-returned references this advisory rests on.
        issued_at: Issue instant, as an ISO-8601 UTC string.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    advisory_id: str
    task_id: str
    proposal_id: str
    proposal_hash: str
    portfolio_id: str
    assessments: Mapping[str, str]
    unresolved_risks: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    issued_at: str
    retained_dissent: tuple[str, ...] = ()

    @field_validator(
        "advisory_id",
        "task_id",
        "proposal_id",
        "proposal_hash",
        "portfolio_id",
        "issued_at",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required advisory reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "advisory reference", limit=_MAX_SHORT_TEXT)

    @field_validator("assessments")
    @classmethod
    def _validate_assessments(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze the per-kind risk assessments.

        Args:
            value: Candidate mapping.

        Returns:
            Frozen ordered mapping.

        Raises:
            ValueError: If a required kind is missing, an unknown kind appears,
                or an assessment is too short or too approving to be one.
        """
        missing = missing_risk_kinds(value)
        if missing:
            message = (
                "a risk advisory must assess every required risk kind; missing: "
                f"{', '.join(missing)}"
            )
            raise ValueError(message)
        unknown = unknown_risk_kinds(value)
        if unknown:
            message = f"unrecognized risk kinds: {', '.join(unknown)}"
            raise ValueError(message)
        for kind, statement in sorted(value.items()):
            _validate_assessment_text(kind, statement)
        return _keyed(value, "risk assessment")

    @field_validator("evidence_refs")
    @classmethod
    def _validate_evidence(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the required supporting evidence references.

        Args:
            value: Candidate references.

        Returns:
            Validated references.
        """
        return _entries(value, "advisory evidence", required=True)

    @field_validator("unresolved_risks", "retained_dissent")
    @classmethod
    def _validate_optional_entries(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one bounded optional advisory tuple.

        Args:
            value: Candidate entries.

        Returns:
            Validated entries.
        """
        return _entries(value, "advisory entry")

    @field_serializer("assessments", mode="plain")
    def _serialize_assessments(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize the assessments deterministically.

        Args:
            value: Frozen mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


def _instant(value: str, field: str) -> datetime:
    """Parse one aware UTC instant from its ISO-8601 form.

    Args:
        value: Candidate instant.
        field: Safe field label for validation.

    Returns:
        The parsed aware instant.

    Raises:
        ValueError: If the instant is unreadable or carries no offset.
    """
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        message = f"{field} must be an ISO-8601 instant: {error}"
        raise ValueError(message) from error
    if parsed.tzinfo is None:
        message = f"{field} must carry a UTC offset"
        raise ValueError(message)
    return parsed


def _validate_assessment_text(kind: str, statement: str) -> None:
    """Validate that one assessment actually assesses something.

    Args:
        kind: Risk kind.
        statement: Candidate assessment statement.

    Raises:
        ValueError: If the statement is too short or merely reassures.
    """
    trimmed = statement.strip()
    if len(trimmed) < _MIN_ASSESSMENT_TEXT:
        message = (
            f"the {kind} risk assessment is too short to be an assessment; state "
            "what you examined, or record it as an unresolved risk"
        )
        raise ValueError(message)
    lowered = trimmed.lower()
    for phrase in _NON_CRITICAL_PHRASES:
        if phrase in lowered:
            message = (
                f"the {kind} risk assessment reads as reassurance; a critic that "
                "finds nothing is a critic that did not look"
            )
            raise ValueError(message)


def derive_proposal_hash(fields: Mapping[str, object]) -> str:
    """Derive the content digest of one allocation proposal.

    Args:
        fields: Proposal fields excluding the derived digest.

    Returns:
        The canonical content digest.
    """
    payload = {key: value for key, value in fields.items() if key != "proposal_hash"}
    return canonical_digest(payload)


def build_allocation_proposal(fields: Mapping[str, object]) -> AllocationProposal:
    """Build one non-binding allocation proposal.

    Args:
        fields: Complete proposal fields excluding the derived digest.

    Returns:
        A validated immutable proposal carrying its content digest.
    """
    logger.debug("Building an allocation proposal")
    return AllocationProposal.model_validate(
        {**fields, "proposal_hash": derive_proposal_hash(fields)},
    )


def build_risk_advisory(fields: Mapping[str, object]) -> RiskAdvisory:
    """Build one independent risk advisory.

    Args:
        fields: Complete advisory fields.

    Returns:
        A validated immutable advisory.
    """
    logger.debug("Building a risk advisory")
    return RiskAdvisory.model_validate(fields)
