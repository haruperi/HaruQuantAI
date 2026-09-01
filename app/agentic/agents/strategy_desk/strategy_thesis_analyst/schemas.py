"""Typed hypotheses and non-executable strategy theses.

`Hypothesis` makes falsifiability structural (`FR-AGENTIC-037`): asset scope,
horizon, mechanism, prerequisites, confounders, and a rejection criterion are
all required. A hypothesis you could not reject cannot be constructed.

`StrategyThesis` carries no code, order, price, or size field, and every text
field rejects execution language (`FR-AGENTIC-038`). It also requires the
conflicts it inherited to travel with it, so agreement alone cannot promote a
proposal (`FR-AGENTIC-039`).
"""

from __future__ import annotations

from collections.abc import Mapping
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

# A thesis is an object of study. Language that reads as an order, an approval,
# or a size would misrepresent it as a plan.
_PROHIBITED_PHRASES: tuple[str, ...] = (
    "approved",
    "i approve",
    "authorization granted",
    "position size",
    "position_size",
    "lot size",
    "lot_size",
    "order size",
    "place the order",
    "execute this trade",
    "entry price",
    "stop loss at",
    "take profit at",
    "buy at",
    "sell at",
)

# Markers that a thesis is smuggling executable content rather than describing
# intended behaviour.
_CODE_MARKERS: tuple[str, ...] = (
    "def ",
    "import ",
    "class ",
    "lambda ",
    "```",
    "return ",
)

ThesisStance = Literal["supported", "unsupported", "contested", "insufficient_evidence"]


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
    """Reject execution, approval, sizing, or code content.

    Args:
        value: Candidate advisory text.
        field: Safe field label for validation.

    Returns:
        The unchanged text.

    Raises:
        ValueError: If the text carries execution, approval, or code content.
    """
    lowered = value.lower()
    for phrase in _PROHIBITED_PHRASES:
        if phrase in lowered:
            message = (
                f"{field} must not carry approval, order, or position-size "
                "language; a thesis is an object of study, not a plan"
            )
            raise ValueError(message)
    for marker in _CODE_MARKERS:
        if marker in value:
            message = (
                f"{field} must not contain executable code; a thesis describes "
                "intended behaviour and nothing more"
            )
            raise ValueError(message)
    return value


def _keyed(value: Mapping[str, str], field: str) -> Mapping[str, str]:
    """Validate and freeze one bounded hypothesis-keyed mapping.

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


def _statements(value: tuple[str, ...], field: str) -> tuple[str, ...]:
    """Validate a bounded ordered tuple of advisory statements.

    Args:
        value: Candidate statements.
        field: Safe field label for validation.

    Returns:
        Validated statements.

    Raises:
        ValueError: If the tuple is oversized.
    """
    if len(value) > _MAX_ITEMS:
        message = f"{field} must not exceed {_MAX_ITEMS} entries"
        raise ValueError(message)
    return tuple(_advisory(_text(item, field), field) for item in value)


class _ThesisModel(BaseModel):
    """Private strict immutable behaviour shared by thesis contracts."""

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )


class Hypothesis(_ThesisModel):
    """One falsifiable claim about market behaviour.

    Attributes:
        hypothesis_id: Stable hypothesis identity.
        task_id: Owning task identity.
        statement: The claim itself.
        asset_scope: Instruments, venues, and conditions it applies to.
        horizon: Timescale over which it should hold.
        mechanism: Proposed cause; why it would be true.
        prerequisites: What must hold for the claim to be testable.
        confounders: Plausible alternative explanations.
        rejection_criterion: The measurable outcome that would abandon it.
        evidence_refs: Evidence packs supporting the claim.
        leakage_constraints: Constraints for leakage-safe evaluation.
    """

    hypothesis_id: str
    task_id: str
    statement: str
    asset_scope: tuple[str, ...]
    horizon: str
    mechanism: str
    prerequisites: tuple[str, ...]
    confounders: tuple[str, ...]
    rejection_criterion: str
    evidence_refs: tuple[str, ...]
    leakage_constraints: tuple[str, ...] = ()

    @field_validator("hypothesis_id", "task_id", "horizon")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded hypothesis reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "hypothesis reference", limit=_MAX_SHORT_TEXT)

    @field_validator("statement", "mechanism", "rejection_criterion")
    @classmethod
    def _validate_prose(cls, value: str) -> str:
        """Validate one required hypothesis prose field.

        Args:
            value: Candidate text.

        Returns:
            Validated text.
        """
        return _advisory(_text(value, "hypothesis text"), "hypothesis text")

    @field_validator(
        "asset_scope",
        "prerequisites",
        "confounders",
        "evidence_refs",
    )
    @classmethod
    def _validate_required_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one required hypothesis declaration.

        A hypothesis with no asset scope, no prerequisite, no confounder, or no
        supporting evidence is not falsifiable in practice.

        Args:
            value: Candidate entries.

        Returns:
            Validated entries.

        Raises:
            ValueError: If the declaration is empty.
        """
        if not value:
            message = (
                "asset scope, prerequisites, confounders, and evidence are all "
                "required; a hypothesis missing any of them is not falsifiable"
            )
            raise ValueError(message)
        return _statements(value, "hypothesis declaration")

    @field_validator("leakage_constraints")
    @classmethod
    def _validate_leakage(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the optional leakage constraints.

        Args:
            value: Candidate constraints.

        Returns:
            Validated constraints.
        """
        return _statements(value, "leakage constraints")


class StrategyThesis(_ThesisModel):
    """One non-executable synthesis of hypotheses into intended behaviour.

    Attributes:
        thesis_id: Stable thesis identity.
        task_id: Owning task identity.
        title: Bounded thesis title.
        summary: Bounded description of the idea.
        stance: Evidential standing of the thesis.
        hypothesis_ids: Hypotheses this thesis rests on.
        signals: Described signals, by signal identifier.
        intended_behaviour: Described behaviour, by signal identifier.
        supporting_evidence: Evidence pack references.
        retained_conflicts: Unresolved conflicts carried forward.
        assumptions: Stated assumptions not backed by evidence.
        uncertainty: Bounded statement of the basis and its limits.
        next_test: The cheapest experiment that could falsify the thesis.
    """

    thesis_id: str
    task_id: str
    title: str
    summary: str
    stance: ThesisStance
    hypothesis_ids: tuple[str, ...]
    signals: Mapping[str, str]
    intended_behaviour: Mapping[str, str]
    supporting_evidence: tuple[str, ...]
    retained_conflicts: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    uncertainty: str
    next_test: str

    @field_validator("thesis_id", "task_id", "title")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded thesis reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "thesis reference", limit=_MAX_SHORT_TEXT)

    @field_validator("summary", "uncertainty", "next_test")
    @classmethod
    def _validate_prose(cls, value: str) -> str:
        """Validate one required thesis prose field.

        Args:
            value: Candidate text.

        Returns:
            Validated text.
        """
        return _advisory(_text(value, "thesis text"), "thesis text")

    @field_validator("signals", "intended_behaviour")
    @classmethod
    def _validate_keyed(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze one signal-keyed mapping.

        Args:
            value: Candidate mapping.

        Returns:
            Frozen ordered mapping.
        """
        return _keyed(value, "thesis mapping")

    @field_validator("hypothesis_ids", "supporting_evidence")
    @classmethod
    def _validate_required_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one required thesis declaration.

        Args:
            value: Candidate entries.

        Returns:
            Validated entries.

        Raises:
            ValueError: If the declaration is empty.
        """
        if not value:
            message = "a thesis requires supporting hypotheses and evidence"
            raise ValueError(message)
        return _statements(value, "thesis declaration")

    @field_validator("retained_conflicts", "assumptions")
    @classmethod
    def _validate_optional_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one optional thesis declaration.

        Args:
            value: Candidate entries.

        Returns:
            Validated entries.
        """
        return _statements(value, "thesis declaration")

    @model_validator(mode="after")
    def _validate_thesis(self) -> Self:
        """Validate signal coverage and conflict retention.

        Returns:
            The validated thesis.

        Raises:
            ValueError: If a described signal has no intended behaviour, or a
                contested thesis retains no conflict.
        """
        missing = sorted(set(self.signals) - set(self.intended_behaviour))
        if missing:
            message = (
                "every described signal requires an intended behaviour; "
                f"missing for: {', '.join(missing)}"
            )
            raise ValueError(message)
        orphaned = sorted(set(self.intended_behaviour) - set(self.signals))
        if orphaned:
            message = (
                "intended behaviour names signals that were never described: "
                f"{', '.join(orphaned)}"
            )
            raise ValueError(message)
        # A contested standing exists precisely to carry disagreement forward;
        # claiming it while retaining no conflict would erase the dissent.
        if self.stance == "contested" and not self.retained_conflicts:
            message = "a contested thesis must retain the conflicts that contest it"
            raise ValueError(message)
        return self

    @field_serializer("signals", "intended_behaviour", mode="plain")
    def _serialize_mapping(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize one bounded mapping deterministically.

        Args:
            value: Frozen mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


def build_hypothesis(fields: Mapping[str, object]) -> Hypothesis:
    """Build one falsifiable hypothesis.

    Args:
        fields: Complete hypothesis fields.

    Returns:
        A validated immutable hypothesis.
    """
    logger.debug("Building a hypothesis")
    return Hypothesis.model_validate(fields)


def build_strategy_thesis(fields: Mapping[str, object]) -> StrategyThesis:
    """Build one non-executable strategy thesis.

    Args:
        fields: Complete thesis fields.

    Returns:
        A validated immutable strategy thesis.
    """
    logger.debug("Building a strategy thesis")
    return StrategyThesis.model_validate(fields)
