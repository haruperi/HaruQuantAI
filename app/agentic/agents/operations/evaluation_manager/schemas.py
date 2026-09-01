"""Evaluation plans, adversarial critiques, and acceptance verdicts.

`EvaluationPlan` makes coverage exact (`FR-AGENTIC-049`): the declared sets,
graders, and grader calibrations must be keyed by precisely the six required
kinds, so an evaluation missing its poisoning set — or carrying an uncalibrated
grader — cannot be represented at all.

`CritiqueMemo` makes adversarial coverage exact (`FR-AGENTIC-050`): all seven
challenges must be addressed, and the memo rejects approval language, so a
"critique" that merely endorses cannot be written.

`EconomicAcceptanceVerdict` makes the conclusion binding (`FR-AGENTIC-051`):
the required action is validated against the gates and the baseline margin, so
a verdict cannot say `continue` about a role that failed a safety gate or did
not beat its baseline once uncertainty and cost were paid.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from types import MappingProxyType
from typing import Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from app.agentic.agents.operations.evaluation_manager.evaluator import (
    missing_challenge_kinds,
    missing_set_kinds,
    required_action,
    survives_baseline,
    unknown_challenge_kinds,
    unknown_set_kinds,
)
from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest

logger = get_logger(__name__)

_MAX_TEXT = 2_000
_MAX_SHORT_TEXT = 200
_MAX_ITEMS = 32

# A challenge shorter than this is not a challenge. The bound is deliberately
# low: it catches "n/a" and "none", not brevity.
_MIN_CHALLENGE_TEXT = 24

type RequiredAction = Literal["continue", "disable", "retire"]
type GateOutcome = Literal["passed", "failed", "not_run"]

# An evaluation is a judgement about whether something should continue. Language
# that reads as an order, an approval, or a size would misrepresent it.
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

# Wording that turns a critique into an endorsement. A memo saying these things
# has stopped doing the job the role exists for.
_NON_ADVERSARIAL_PHRASES: tuple[str, ...] = (
    "no concerns",
    "no issues",
    "nothing to flag",
    "looks good",
    "lgtm",
    "not applicable",
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
        value: Candidate text.
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
                "an evaluation authorizes nothing"
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


def _keyed(
    value: Mapping[str, str],
    field: str,
    *,
    limit: int = _MAX_SHORT_TEXT,
) -> Mapping[str, str]:
    """Validate and freeze one bounded kind-keyed mapping.

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
        _text(key, f"{field} kind", limit=_MAX_SHORT_TEXT): _advisory(
            _text(item, f"{field} entry", limit=limit),
            field,
        )
        for key, item in sorted(value.items())
    }
    return MappingProxyType(frozen)


class EvaluationPlan(BaseModel):
    """One versioned evaluation covering every required set kind.

    Attributes:
        plan_id: Stable plan identity.
        task_id: Owning task identity.
        subject_role_id: Role this evaluation measures.
        subject_role_version: Version of the role under evaluation.
        evaluation_sets: Versioned set reference per required kind.
        graders: Grader reference per required kind.
        grader_calibrations: Calibration reference per required kind.
        baseline_ref: Simpler baseline the subject is compared against.
        sample_size: Observation count backing the evaluation.
        plan_hash: Derived digest over the declared plan.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    plan_id: str
    task_id: str
    subject_role_id: str
    subject_role_version: str
    evaluation_sets: Mapping[str, str]
    graders: Mapping[str, str]
    grader_calibrations: Mapping[str, str]
    baseline_ref: str
    sample_size: str
    plan_hash: str

    @field_validator(
        "plan_id",
        "task_id",
        "subject_role_id",
        "subject_role_version",
        "baseline_ref",
        "sample_size",
        "plan_hash",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required plan reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "evaluation plan reference", limit=_MAX_SHORT_TEXT)

    @field_validator("evaluation_sets", "graders", "grader_calibrations")
    @classmethod
    def _validate_coverage(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze one kind-keyed coverage mapping.

        Args:
            value: Candidate mapping.

        Returns:
            Frozen ordered mapping.

        Raises:
            ValueError: If a required kind is missing or an unknown kind
                appears.
        """
        missing = missing_set_kinds(value)
        if missing:
            message = (
                "an evaluation must cover every required set kind; missing: "
                f"{', '.join(missing)}"
            )
            raise ValueError(message)
        unknown = unknown_set_kinds(value)
        if unknown:
            message = f"unrecognized evaluation set kinds: {', '.join(unknown)}"
            raise ValueError(message)
        return _keyed(value, "evaluation coverage")

    @field_serializer("evaluation_sets", "graders", "grader_calibrations", mode="plain")
    def _serialize_mapping(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize one coverage mapping deterministically.

        Args:
            value: Frozen mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


class BaselineComparison(BaseModel):
    """One measured comparison of a candidate against its simpler baseline.

    Attributes:
        candidate_score: Candidate's measured score.
        baseline_score: Simpler baseline's measured score.
        uncertainty_halfwidth: Half-width of the measurement interval.
        cost_delta: Extra cost the candidate incurs over the baseline.
        metric: Metric the scores are expressed in.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    candidate_score: Decimal
    baseline_score: Decimal
    uncertainty_halfwidth: Decimal
    cost_delta: Decimal
    metric: str

    @field_validator("metric")
    @classmethod
    def _validate_metric(cls, value: str) -> str:
        """Validate the metric name.

        Args:
            value: Candidate metric name.

        Returns:
            Validated metric name.
        """
        return _text(value, "comparison metric", limit=_MAX_SHORT_TEXT)

    @field_validator("uncertainty_halfwidth", "cost_delta")
    @classmethod
    def _validate_non_negative(cls, value: Decimal) -> Decimal:
        """Validate one non-negative economic quantity.

        Args:
            value: Candidate quantity.

        Returns:
            Validated quantity.

        Raises:
            ValueError: If the quantity is negative.
        """
        if value < 0:
            message = "uncertainty and cost must not be negative"
            raise ValueError(message)
        return value

    @property
    def margin(self) -> Decimal:
        """Return the raw score margin over the baseline.

        Returns:
            Candidate score minus baseline score.
        """
        return self.candidate_score - self.baseline_score

    @property
    def hurdle(self) -> Decimal:
        """Return the margin the candidate must exceed.

        Returns:
            Uncertainty half-width plus cost delta.
        """
        return self.uncertainty_halfwidth + self.cost_delta

    @property
    def survives(self) -> bool:
        """Report whether the margin clears uncertainty and cost.

        Returns:
            True when the candidate beats its baseline after everything is
            paid.
        """
        return survives_baseline(
            self.candidate_score,
            self.baseline_score,
            self.uncertainty_halfwidth,
            self.cost_delta,
        )


class CritiqueMemo(BaseModel):
    """One adversarial critique addressing every required challenge.

    Attributes:
        memo_id: Stable memo identity.
        task_id: Owning task identity.
        candidate_ref: Candidate artefact under critique.
        challenges: Substantiated challenge per required kind.
        unsubstantiated: Challenge kinds the critic could not substantiate.
        blocking_concerns: Concerns that must be resolved before promotion.
        evidence_refs: Evidence the critique rests on.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    memo_id: str
    task_id: str
    candidate_ref: str
    challenges: Mapping[str, str]
    unsubstantiated: tuple[str, ...] = ()
    blocking_concerns: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    @field_validator("memo_id", "task_id", "candidate_ref")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required memo reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "critique reference", limit=_MAX_SHORT_TEXT)

    @field_validator("challenges")
    @classmethod
    def _validate_challenges(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze the addressed challenges.

        Args:
            value: Candidate mapping.

        Returns:
            Frozen ordered mapping.

        Raises:
            ValueError: If a required challenge is missing, an unknown
                challenge appears, or a challenge is too short or
                non-adversarial to be one.
        """
        missing = missing_challenge_kinds(value)
        if missing:
            message = (
                "a critique must address every required challenge; missing: "
                f"{', '.join(missing)}"
            )
            raise ValueError(message)
        unknown = unknown_challenge_kinds(value)
        if unknown:
            message = f"unrecognized critique challenges: {', '.join(unknown)}"
            raise ValueError(message)
        for kind, statement in sorted(value.items()):
            _validate_challenge_text(kind, statement)
        return _keyed(value, "critique challenge", limit=_MAX_TEXT)

    @field_validator("unsubstantiated")
    @classmethod
    def _validate_unsubstantiated(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the declared unsubstantiated challenge kinds.

        Args:
            value: Candidate kinds.

        Returns:
            Validated kinds.

        Raises:
            ValueError: If a kind is not a required challenge kind.
        """
        unknown = unknown_challenge_kinds(dict.fromkeys(value, "declared"))
        if unknown:
            message = f"unrecognized critique challenges: {', '.join(unknown)}"
            raise ValueError(message)
        return tuple(sorted(set(value)))

    @field_validator("blocking_concerns", "evidence_refs")
    @classmethod
    def _validate_optional_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one bounded optional memo tuple.

        Args:
            value: Candidate entries.

        Returns:
            Validated entries.

        Raises:
            ValueError: If the tuple is oversized.
        """
        if len(value) > _MAX_ITEMS:
            message = f"critique tuples must not exceed {_MAX_ITEMS} entries"
            raise ValueError(message)
        return tuple(
            _advisory(_text(item, "critique entry"), "critique entry") for item in value
        )

    @field_serializer("challenges", mode="plain")
    def _serialize_challenges(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize the challenges deterministically.

        Args:
            value: Frozen mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


def _validate_challenge_text(kind: str, statement: str) -> None:
    """Validate that one challenge actually challenges something.

    Args:
        kind: Challenge kind.
        statement: Candidate challenge statement.

    Raises:
        ValueError: If the statement is too short or merely endorses.
    """
    trimmed = statement.strip()
    if len(trimmed) < _MIN_CHALLENGE_TEXT:
        message = (
            f"the {kind} challenge is too short to be a challenge; state what "
            "you looked for, or declare it unsubstantiated"
        )
        raise ValueError(message)
    lowered = trimmed.lower()
    for phrase in _NON_ADVERSARIAL_PHRASES:
        if phrase in lowered:
            message = (
                f"the {kind} challenge reads as an endorsement; a critique that "
                "finds nothing wrong is a critique that did not look"
            )
            raise ValueError(message)


class EconomicAcceptanceVerdict(BaseModel):
    """One binding decision about whether a role continues.

    Attributes:
        verdict_id: Stable verdict identity.
        task_id: Owning task identity.
        plan_id: Evaluation plan this verdict reads.
        plan_hash: Digest of the plan as declared.
        subject_role_id: Role this verdict decides.
        gate_outcomes: Outcome per safety and reliability gate.
        comparison: Measured comparison against the simpler baseline.
        required_action: What must happen to the role.
        rationale: Why the required action follows.
        uncertainty_statement: What the measurement could not establish.
        consecutive_failures: Prior consecutive failed evaluations.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    verdict_id: str
    task_id: str
    plan_id: str
    plan_hash: str
    subject_role_id: str
    gate_outcomes: Mapping[str, GateOutcome]
    comparison: BaselineComparison
    required_action: RequiredAction
    rationale: str
    uncertainty_statement: str
    consecutive_failures: int = 0

    @field_validator(
        "verdict_id",
        "task_id",
        "plan_id",
        "plan_hash",
        "subject_role_id",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required verdict reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "verdict reference", limit=_MAX_SHORT_TEXT)

    @field_validator("rationale", "uncertainty_statement")
    @classmethod
    def _validate_statement(cls, value: str) -> str:
        """Validate one required verdict statement.

        Args:
            value: Candidate statement.

        Returns:
            Validated statement.
        """
        return _advisory(_text(value, "verdict statement"), "verdict statement")

    @field_validator("gate_outcomes")
    @classmethod
    def _validate_gates(
        cls,
        value: Mapping[str, GateOutcome],
    ) -> Mapping[str, GateOutcome]:
        """Validate and freeze the recorded gate outcomes.

        Args:
            value: Candidate mapping.

        Returns:
            Frozen ordered mapping.

        Raises:
            ValueError: If no gate was recorded.
        """
        if not value:
            message = "a verdict must record the gates that were run"
            raise ValueError(message)
        frozen = {
            _text(key, "gate kind", limit=_MAX_SHORT_TEXT): item
            for key, item in sorted(value.items())
        }
        return MappingProxyType(frozen)

    @field_validator("consecutive_failures")
    @classmethod
    def _validate_failures(cls, value: int) -> int:
        """Validate the prior consecutive failure count.

        Args:
            value: Candidate count.

        Returns:
            Validated count.

        Raises:
            ValueError: If the count is negative.
        """
        if value < 0:
            message = "consecutive_failures must not be negative"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def _validate_action(self) -> Self:
        """Validate that the required action follows from the evidence.

        This is what makes the verdict binding: the action is recomputed from
        the gates and the margin, so a verdict cannot say `continue` about a
        role that failed a gate or did not beat its baseline.

        Returns:
            The validated verdict.

        Raises:
            ValueError: If the recorded action disagrees with the evidence.
        """
        failed = tuple(
            sorted(
                kind
                for kind, outcome in self.gate_outcomes.items()
                if outcome != "passed"
            ),
        )
        expected = required_action(
            failed,
            self.comparison.survives,
            self.consecutive_failures,
        )
        if self.required_action != expected:
            message = (
                f"required_action {self.required_action!r} disagrees with the "
                f"evidence, which requires {expected!r}: failed gates "
                f"{failed or ('none',)}, margin {self.comparison.margin} against "
                f"hurdle {self.comparison.hurdle}"
            )
            raise ValueError(message)
        return self

    @field_serializer("gate_outcomes", mode="plain")
    def _serialize_gates(self, value: Mapping[str, GateOutcome]) -> dict[str, str]:
        """Serialize the gate outcomes deterministically.

        Args:
            value: Frozen mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


def derive_plan_hash(fields: Mapping[str, object]) -> str:
    """Derive the declaration digest of one evaluation plan.

    Args:
        fields: Plan fields excluding the derived digest.

    Returns:
        The canonical content digest.
    """
    payload = {key: value for key, value in fields.items() if key != "plan_hash"}
    return canonical_digest(payload)


def build_evaluation_plan(fields: Mapping[str, object]) -> EvaluationPlan:
    """Build one versioned evaluation plan.

    Args:
        fields: Complete plan fields excluding the derived digest.

    Returns:
        A validated immutable plan carrying its declaration digest.
    """
    logger.debug("Building an evaluation plan")
    return EvaluationPlan.model_validate(
        {**fields, "plan_hash": derive_plan_hash(fields)},
    )


def build_baseline_comparison(fields: Mapping[str, object]) -> BaselineComparison:
    """Build one measured baseline comparison.

    Args:
        fields: Complete comparison fields.

    Returns:
        A validated immutable comparison.
    """
    return BaselineComparison.model_validate(fields)


def build_critique_memo(fields: Mapping[str, object]) -> CritiqueMemo:
    """Build one adversarial critique memo.

    Args:
        fields: Complete memo fields.

    Returns:
        A validated immutable memo.
    """
    logger.debug("Building a critique memo")
    return CritiqueMemo.model_validate(fields)


def build_economic_acceptance_verdict(
    fields: Mapping[str, object],
) -> EconomicAcceptanceVerdict:
    """Build one binding economic-acceptance verdict.

    Args:
        fields: Complete verdict fields.

    Returns:
        A validated immutable verdict.
    """
    logger.debug("Building an economic acceptance verdict")
    return EconomicAcceptanceVerdict.model_validate(fields)
