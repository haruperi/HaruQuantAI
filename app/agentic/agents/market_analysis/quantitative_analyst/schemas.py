"""Typed output for the Quantitative Analyst.

`QuantitativeEvidencePack` makes statistical disclosure structural
(`FR-AGENTIC-035`): sample, estimator, uncertainty, multiple-testing exposure,
assumptions, and limitations are all required, and findings are keyed alike
with their uncertainty and assumptions so a bare point estimate is
unrepresentable.

The schema carries no numeric field. Every value is bounded text, so the model
has nowhere to impute a statistic it was not given (`FR-AGENTIC-036`), and the
estimator names are copied from the deterministic catalog rather than authored
(`FR-AGENTIC-034`).
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

from app.utils import get_logger

logger = get_logger(__name__)

_MAX_TEXT = 2_000
_MAX_SHORT_TEXT = 200
_MAX_ITEMS = 32

# A quantitative reading is advisory evidence. Language that reads as an order,
# an approval, or a size would misrepresent it as a decision.
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
                "a quantitative reading is advisory evidence only"
            )
            raise ValueError(message)
    return value


def _keyed(value: Mapping[str, str], field: str) -> Mapping[str, str]:
    """Validate and freeze one bounded finding-keyed mapping.

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
        ValueError: If the tuple is empty or oversized.
    """
    if not value:
        message = f"{field} is required"
        raise ValueError(message)
    if len(value) > _MAX_ITEMS:
        message = f"{field} must not exceed {_MAX_ITEMS} entries"
        raise ValueError(message)
    return tuple(_advisory(_text(item, field), field) for item in value)


class QuantitativeEvidencePack(BaseModel):
    """One disclosed statistical reading of versioned deterministic evidence.

    Attributes:
        pack_id: Stable pack identity.
        task_id: Owning task identity.
        dataset_hash: Dataset the evidence was computed from.
        configuration_hash: Configuration the evidence was computed under.
        split_label: Split the evidence covers.
        sample_size: Observation count, recorded as text to stay non-numeric.
        multiple_testing_exposure: Hypotheses tested to reach this reading.
        estimators: Catalogued estimator name per finding identifier.
        findings: Statistical findings, by finding identifier.
        uncertainty: Interval or dispersion evidence per finding identifier.
        assumptions: Estimator assumptions most at risk here.
        limitations: What this evidence cannot establish.
        leakage_status: Leakage classification of the underlying data.
        validation_status: Whether a null or random-label control was run.
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
    dataset_hash: str
    configuration_hash: str
    split_label: str
    sample_size: str
    multiple_testing_exposure: str
    estimators: Mapping[str, str]
    findings: Mapping[str, str]
    uncertainty: Mapping[str, str]
    assumptions: tuple[str, ...]
    limitations: tuple[str, ...]
    leakage_status: str
    validation_status: str
    conflicts: tuple[str, ...] = ()

    @field_validator(
        "pack_id",
        "task_id",
        "dataset_hash",
        "configuration_hash",
        "split_label",
        "sample_size",
        "multiple_testing_exposure",
        "leakage_status",
        "validation_status",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required disclosure field.

        Args:
            value: Candidate value.

        Returns:
            Validated value.
        """
        return _text(value, "quantitative disclosure", limit=_MAX_SHORT_TEXT)

    @field_validator("estimators", "findings", "uncertainty")
    @classmethod
    def _validate_keyed(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze one finding-keyed mapping.

        Args:
            value: Candidate mapping.

        Returns:
            Frozen ordered mapping.
        """
        return _keyed(value, "finding mapping")

    @field_validator("assumptions", "limitations")
    @classmethod
    def _validate_required_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one required disclosure tuple.

        Args:
            value: Candidate statements.

        Returns:
            Validated statements.
        """
        return _statements(value, "quantitative disclosure")

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
        """Validate that every finding is fully disclosed.

        Returns:
            The validated pack.

        Raises:
            ValueError: If a finding lacks an estimator or uncertainty, or an
                estimator or uncertainty names a finding that does not exist.
        """
        finding_ids = set(self.findings)
        for label, mapping in (
            ("estimators", self.estimators),
            ("uncertainty", self.uncertainty),
        ):
            missing = sorted(finding_ids - set(mapping))
            if missing:
                message = (
                    f"every finding requires {label}; missing for: {', '.join(missing)}"
                )
                raise ValueError(message)
            orphaned = sorted(set(mapping) - finding_ids)
            if orphaned:
                message = (
                    f"{label} names findings that do not exist: {', '.join(orphaned)}"
                )
                raise ValueError(message)
        return self

    @field_serializer("estimators", "findings", "uncertainty", mode="plain")
    def _serialize_mapping(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize one bounded mapping deterministically.

        Args:
            value: Frozen mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


def build_quantitative_evidence_pack(
    fields: Mapping[str, object],
) -> QuantitativeEvidencePack:
    """Build one disclosed quantitative evidence pack.

    Args:
        fields: Complete pack fields.

    Returns:
        A validated immutable quantitative evidence pack.
    """
    logger.debug("Building a quantitative evidence pack")
    return QuantitativeEvidencePack.model_validate(fields)
