"""Typed output for the Simulation Interpreter.

`RunInterpretation` separates the four kinds of statement an interpretation may
contain, so a model inference can never occupy a measured-fact field.

The schema carries **no numeric field**. Every value is bounded text keyed by
the source reference it came from, so the interpreter has nowhere to put a
recomputed metric and cannot state a fact without citing it
(`FR-AGENTIC-022`, `FR-AGENTIC-023`).
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Self

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

# An interpretation is advisory evidence. Language that reads as an approval or
# a size would misrepresent it as a decision.
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
    """Reject text that would read as an approval or a position size.

    Args:
        value: Candidate advisory text.
        field: Safe field label for validation.

    Returns:
        The unchanged text.

    Raises:
        ValueError: If the text carries approval or sizing language.
    """
    lowered = value.lower()
    for phrase in _PROHIBITED_PHRASES:
        if phrase in lowered:
            message = (
                f"{field} must not carry approval or position-size language; "
                "an interpretation is advisory evidence only"
            )
            raise ValueError(message)
    return value


def _cited(value: Mapping[str, str], field: str) -> Mapping[str, str]:
    """Validate and freeze a citation-keyed statement mapping.

    The key is the exact source reference the statement came from, so a
    statement cannot exist without a citation.

    Args:
        value: Candidate mapping of source reference to statement.
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
        _text(key, f"{field} source reference", limit=_MAX_SHORT_TEXT): _advisory(
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


class RunInterpretation(BaseModel):
    """One cited interpretation of completed deterministic evidence.

    Attributes:
        interpretation_id: Stable interpretation identity.
        task_id: Owning task identity.
        evidence_ref: Reference to the interpreted artefact.
        evidence_schema_id: Namespaced schema identity of the artefact.
        evidence_contract_version: Compatibility version of the artefact.
        measured_facts: Values stated verbatim in the artefact, by source ref.
        deterministic_derivations: Relationships the artefact establishes.
        model_inferences: The interpreter's own readings, by source ref.
        recommendations: Suggested next investigations; advisory only.
        limitations: What the evidence does not cover.
        open_questions: What remains unanswered.
        uncertainty: Bounded statement of the basis and its limits.
        falsifiers: What observation would refute each material inference.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    interpretation_id: str
    task_id: str
    evidence_ref: str
    evidence_schema_id: str
    evidence_contract_version: str
    measured_facts: Mapping[str, str]
    deterministic_derivations: Mapping[str, str]
    model_inferences: Mapping[str, str]
    recommendations: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    open_questions: tuple[str, ...] = ()
    uncertainty: str
    falsifiers: tuple[str, ...] = ()

    @field_validator(
        "interpretation_id",
        "task_id",
        "evidence_ref",
        "evidence_schema_id",
        "evidence_contract_version",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded interpretation reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "interpretation reference", limit=_MAX_SHORT_TEXT)

    @field_validator(
        "measured_facts",
        "deterministic_derivations",
        "model_inferences",
    )
    @classmethod
    def _validate_cited(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze one citation-keyed statement mapping.

        Args:
            value: Candidate mapping.

        Returns:
            Frozen ordered mapping.
        """
        return _cited(value, "cited statements")

    @field_validator(
        "recommendations",
        "limitations",
        "open_questions",
        "falsifiers",
    )
    @classmethod
    def _validate_statements(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one bounded advisory statement tuple.

        Args:
            value: Candidate statements.

        Returns:
            Validated statements.
        """
        return _statements(value, "advisory statements")

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

    @model_validator(mode="after")
    def _validate_interpretation(self) -> Self:
        """Validate that the interpretation says something citable.

        Returns:
            The validated interpretation.

        Raises:
            ValueError: If it asserts an inference with no cited measured fact.
        """
        # Citing the same source in both a fact and an inference is correct and
        # expected: an interpreter reads a value, then reasons about it. What is
        # rejected is an inference standing on no cited fact at all.
        if self.model_inferences and not self.measured_facts:
            message = (
                "an inference requires at least one measured fact; an "
                "interpretation with no cited fact is speculation"
            )
            raise ValueError(message)
        return self

    @field_serializer(
        "measured_facts",
        "deterministic_derivations",
        "model_inferences",
        mode="plain",
    )
    def _serialize_mapping(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize one cited mapping deterministically.

        Args:
            value: Frozen mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


def build_run_interpretation(fields: Mapping[str, object]) -> RunInterpretation:
    """Build one cited interpretation.

    Args:
        fields: Complete interpretation fields.

    Returns:
        A validated immutable interpretation.
    """
    logger.debug("Building a run interpretation")
    return RunInterpretation.model_validate(fields)
