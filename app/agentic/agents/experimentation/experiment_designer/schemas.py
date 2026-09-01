"""Immutable experiment protocols and run-bound verdicts.

`ExperimentSpec` makes protocol completeness structural (`FR-AGENTIC-040`):
inputs, ordered splits, embargo, costs, seed, baseline, metrics, stop rules,
and a falsification outcome are all required, and the split ordering is
validated rather than trusted. The spec is frozen and carries its own content
digest, so a verdict cannot be matched against a criterion rewritten after the
run.

`ExperimentVerdict` makes evidence lineage structural (`FR-AGENTIC-042`):
conclusions are keyed by the run identifier that produced them, and the
evidence class is validated against the identical key set, so a conclusion
without a run — or a run without a declared evidence class — cannot be
represented.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from itertools import pairwise
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
from app.kernel.serialization import canonical_digest

logger = get_logger(__name__)

_MAX_TEXT = 2_000
_MAX_SHORT_TEXT = 200
_MAX_ITEMS = 32

type SplitLabel = Literal["discovery", "validation", "holdout"]
type EvidenceClass = Literal["discovery", "validation", "holdout", "null_data"]

# Splits are ordered in time. The ordering is what makes an embargo meaningful,
# so it is validated rather than assumed from the mapping's insertion order.
_SPLIT_ORDER: tuple[SplitLabel, ...] = ("discovery", "validation", "holdout")

# A protocol is an object of study. Language that reads as an order, an
# approval, or a size would misrepresent it as a plan to trade.
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
    "deploy to live",
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
        value: Candidate protocol text.
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
                "an experiment protocol authorizes nothing"
            )
            raise ValueError(message)
    return value


def _statements(value: tuple[str, ...], field: str) -> tuple[str, ...]:
    """Validate a bounded ordered tuple of required statements.

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


def _keyed(value: Mapping[str, str], field: str) -> Mapping[str, str]:
    """Validate and freeze one bounded identifier-keyed mapping.

    Args:
        value: Candidate mapping.
        field: Safe field label for validation.

    Returns:
        Deterministically ordered read-only mapping.

    Raises:
        ValueError: If the mapping is empty, oversized, or invalid.
    """
    if not value:
        message = f"{field} is required"
        raise ValueError(message)
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


class SplitWindow(BaseModel):
    """One named, closed time window of an experiment protocol.

    Attributes:
        label: Split this window belongs to.
        start: Inclusive window start.
        end: Exclusive window end.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    label: SplitLabel
    start: datetime
    end: datetime

    @model_validator(mode="after")
    def _validate_window(self) -> Self:
        """Validate that the window is ordered and timezone-aware.

        Returns:
            The validated window.

        Raises:
            ValueError: If a bound is naive or the window is not ordered.
        """
        for bound in (self.start, self.end):
            if bound.tzinfo is None:
                message = "split window bounds must be timezone-aware"
                raise ValueError(message)
        if self.start >= self.end:
            message = f"split {self.label} must start before it ends"
            raise ValueError(message)
        return self


def validate_split_windows(
    splits: tuple[SplitWindow, ...],
    embargo_seconds: int,
) -> str | None:
    """Report why a set of evaluation windows cannot form a protocol.

    This is the single source of truth for split validity. `ExperimentSpec`
    calls it so an invalid protocol is unrepresentable; the agent calls it
    first so an invalid protocol is refused before a model is paid to design
    one for it.

    Args:
        splits: Declared evaluation windows.
        embargo_seconds: Gap required between consecutive splits.

    Returns:
        The failing condition, or None when the windows form a valid protocol.
    """
    labels = tuple(window.label for window in splits)
    if sorted(labels) != sorted(_SPLIT_ORDER):
        return (
            "splits must declare exactly discovery, validation, and holdout; "
            f"got: {', '.join(sorted(labels)) or 'none'}"
        )

    ordered = sorted(splits, key=lambda window: _SPLIT_ORDER.index(window.label))
    for earlier, later in pairwise(ordered):
        gap = (later.start - earlier.end).total_seconds()
        if gap < 0:
            return (
                f"split {later.label} overlaps {earlier.label}; "
                "evaluation windows must not overlap"
            )
        if gap < embargo_seconds:
            return (
                f"split {later.label} follows {earlier.label} after {int(gap)}s, "
                f"less than the declared {embargo_seconds}s embargo"
            )
    return None


class ExperimentSpec(BaseModel):
    """One immutable, complete, pre-registered experiment protocol.

    Attributes:
        spec_id: Stable protocol identity.
        task_id: Owning task identity.
        thesis_id: Thesis this protocol is designed to refute.
        hypothesis_ids: Hypotheses under test.
        input_refs: Versioned immutable inputs the protocol reads.
        splits: Ordered non-overlapping evaluation windows.
        embargo_seconds: Gap enforced between consecutive splits.
        cost_model_ref: Registered execution-cost model applied.
        seed: Reproducibility seed for every run under this protocol.
        baseline_ref: Registered baseline every conclusion compares against.
        metrics: Catalogued metric names evaluated.
        stop_rules: Conditions that end the experiment early.
        falsification_outcome: Observable outcome that refutes the thesis.
        leakage_controls: Measures preventing information crossing splits.
        spec_hash: Derived content digest of the pre-registered protocol.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    spec_id: str
    task_id: str
    thesis_id: str
    hypothesis_ids: tuple[str, ...]
    input_refs: tuple[str, ...]
    splits: tuple[SplitWindow, ...]
    embargo_seconds: int
    cost_model_ref: str
    seed: int
    baseline_ref: str
    metrics: tuple[str, ...]
    stop_rules: tuple[str, ...]
    falsification_outcome: str
    leakage_controls: tuple[str, ...]
    spec_hash: str

    @field_validator(
        "spec_id",
        "task_id",
        "thesis_id",
        "cost_model_ref",
        "baseline_ref",
        "spec_hash",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required protocol reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "protocol reference", limit=_MAX_SHORT_TEXT)

    @field_validator("falsification_outcome")
    @classmethod
    def _validate_falsification(cls, value: str) -> str:
        """Validate the declared refuting outcome.

        Args:
            value: Candidate falsification outcome.

        Returns:
            Validated falsification outcome.
        """
        return _advisory(_text(value, "falsification outcome"), "falsification outcome")

    @field_validator(
        "hypothesis_ids",
        "input_refs",
        "metrics",
        "stop_rules",
        "leakage_controls",
    )
    @classmethod
    def _validate_required_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one required protocol tuple.

        Args:
            value: Candidate statements.

        Returns:
            Validated statements.
        """
        return _statements(value, "protocol element")

    @field_validator("embargo_seconds")
    @classmethod
    def _validate_embargo(cls, value: int) -> int:
        """Validate that an embargo was declared.

        Args:
            value: Candidate embargo in seconds.

        Returns:
            Validated embargo.

        Raises:
            ValueError: If the embargo is negative.
        """
        if value < 0:
            message = "embargo_seconds must not be negative"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def _validate_protocol(self) -> Self:
        """Validate split completeness, ordering, and embargo separation.

        Returns:
            The validated protocol.

        Raises:
            ValueError: If a split is missing or duplicated, or if the windows
                are out of order or not separated by the declared embargo.
        """
        failure = validate_split_windows(self.splits, self.embargo_seconds)
        if failure is not None:
            raise ValueError(failure)
        return self

    @field_serializer("splits", mode="plain")
    def _serialize_splits(
        self,
        value: tuple[SplitWindow, ...],
    ) -> list[dict[str, object]]:
        """Serialize the evaluation windows deterministically.

        Args:
            value: Declared windows.

        Returns:
            Plain ordered window mappings.
        """
        return [window.model_dump(mode="json") for window in value]


class ExperimentVerdict(BaseModel):
    """One run-bound reading of an executed experiment protocol.

    Attributes:
        verdict_id: Stable verdict identity.
        task_id: Owning task identity.
        spec_id: Protocol this verdict reads.
        spec_hash: Digest of the protocol as pre-registered.
        conclusions: Conclusion per originating run identifier.
        evidence_classes: Evidence class per originating run identifier.
        outcome: Whether the declared falsification outcome occurred.
        holdout_consumed: Whether this verdict spent the thesis's holdout.
        limitations: What this experiment cannot establish.
        retained_conflicts: Preserved incompatible readings.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    verdict_id: str
    task_id: str
    spec_id: str
    spec_hash: str
    conclusions: Mapping[str, str]
    evidence_classes: Mapping[str, EvidenceClass]
    outcome: Literal["refuted", "not_refuted", "inconclusive"]
    holdout_consumed: bool
    limitations: tuple[str, ...]
    retained_conflicts: tuple[str, ...] = ()

    @field_validator("verdict_id", "task_id", "spec_id", "spec_hash")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required verdict reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "verdict reference", limit=_MAX_SHORT_TEXT)

    @field_validator("conclusions")
    @classmethod
    def _validate_conclusions(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze the run-keyed conclusions.

        Args:
            value: Candidate mapping.

        Returns:
            Frozen ordered mapping.
        """
        return _keyed(value, "conclusion")

    @field_validator("evidence_classes")
    @classmethod
    def _validate_evidence_classes(
        cls,
        value: Mapping[str, EvidenceClass],
    ) -> Mapping[str, EvidenceClass]:
        """Validate and freeze the run-keyed evidence classes.

        Args:
            value: Candidate mapping.

        Returns:
            Frozen ordered mapping.

        Raises:
            ValueError: If the mapping is empty or oversized.
        """
        if not value:
            message = "evidence_classes is required"
            raise ValueError(message)
        if len(value) > _MAX_ITEMS:
            message = f"evidence_classes must not exceed {_MAX_ITEMS} entries"
            raise ValueError(message)
        frozen = {
            _text(key, "evidence class key", limit=_MAX_SHORT_TEXT): item
            for key, item in sorted(value.items())
        }
        return MappingProxyType(frozen)

    @field_validator("limitations", "retained_conflicts")
    @classmethod
    def _validate_statements(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one bounded verdict tuple.

        Args:
            value: Candidate statements.

        Returns:
            Validated statements.

        Raises:
            ValueError: If the tuple is oversized.
        """
        if len(value) > _MAX_ITEMS:
            message = f"verdict statements must not exceed {_MAX_ITEMS} entries"
            raise ValueError(message)
        return tuple(_advisory(_text(item, "verdict"), "verdict") for item in value)

    @model_validator(mode="after")
    def _validate_lineage(self) -> Self:
        """Validate that every conclusion names a classified run.

        Returns:
            The validated verdict.

        Raises:
            ValueError: If a conclusion lacks an evidence class, an evidence
                class names an unknown run, or holdout consumption disagrees
                with the evidence actually cited.
        """
        run_ids = set(self.conclusions)
        missing = sorted(run_ids - set(self.evidence_classes))
        if missing:
            message = (
                "every conclusion requires an evidence class; "
                f"missing for: {', '.join(missing)}"
            )
            raise ValueError(message)
        orphaned = sorted(set(self.evidence_classes) - run_ids)
        if orphaned:
            message = (
                "evidence_classes names runs that reached no conclusion: "
                f"{', '.join(orphaned)}"
            )
            raise ValueError(message)

        cited_holdout = "holdout" in self.evidence_classes.values()
        if cited_holdout and not self.holdout_consumed:
            message = (
                "a verdict citing holdout evidence must record holdout_consumed; "
                "looking at holdout spends it"
            )
            raise ValueError(message)
        return self

    @field_serializer("conclusions", "evidence_classes", mode="plain")
    def _serialize_mapping(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize one bounded mapping deterministically.

        Args:
            value: Frozen mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


def derive_spec_hash(fields: Mapping[str, object]) -> str:
    """Derive the pre-registration digest of one protocol.

    The digest covers the protocol as declared before any run, so a verdict can
    be checked against the criterion that was actually pre-registered.

    Args:
        fields: Protocol fields excluding the derived digest.

    Returns:
        The canonical content digest.
    """
    payload = {
        key: _json_safe(value) for key, value in fields.items() if key != "spec_hash"
    }
    return canonical_digest(payload)


def _json_safe(value: object) -> object:
    """Convert one declared protocol field to JSON-safe data.

    Split windows arrive as validated models; everything else is already
    canonical-serializable.

    Args:
        value: Declared field value.

    Returns:
        JSON-safe field data.
    """
    if isinstance(value, SplitWindow):
        return value.model_dump(mode="json")
    if isinstance(value, tuple | list):
        return [_json_safe(item) for item in value]
    return value


def build_experiment_spec(fields: Mapping[str, object]) -> ExperimentSpec:
    """Build one immutable pre-registered experiment protocol.

    Args:
        fields: Complete protocol fields excluding the derived digest.

    Returns:
        A validated immutable protocol carrying its content digest.
    """
    logger.debug("Building an experiment protocol")
    return ExperimentSpec.model_validate(
        {**fields, "spec_hash": derive_spec_hash(fields)},
    )


def build_experiment_verdict(fields: Mapping[str, object]) -> ExperimentVerdict:
    """Build one run-bound experiment verdict.

    Args:
        fields: Complete verdict fields.

    Returns:
        A validated immutable verdict.
    """
    logger.debug("Building an experiment verdict")
    return ExperimentVerdict.model_validate(fields)
