"""Bounded sweep plans and robustness-focused verdicts.

`SweepPlan` makes pre-declaration structural (`FR-AGENTIC-043`): the space,
objective, trial budget, early-stop policy, search method, seed, and holdout
consumption are all required before anything runs, and the plan carries a
digest over the whole declaration so a budget raised after seeing results is a
different plan.

`TrialLedger` makes trial preservation arithmetic (`FR-AGENTIC-044`): attempted
must equal completed plus failed, and every failed trial must carry a reason.
A sweep cannot report its survivors while dropping the trials that did not
survive.

`SweepVerdict` makes robustness mandatory (`FR-AGENTIC-045`): robustness,
instability, overfit evidence, economic effect, and unresolved risk are all
required, so a verdict consisting only of the winning parameters cannot be
represented.
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

from app.utils import canonical_digest, get_logger

logger = get_logger(__name__)

_MAX_TEXT = 2_000
_MAX_SHORT_TEXT = 200
_MAX_ITEMS = 64

type HoldoutConsumption = Literal["none", "consumes"]
type SearchMethod = Literal["grid", "random", "walk_forward"]

# Receiver-owned classifications this verdict may carry verbatim. None of them
# is an approval: `ready_for_risk_review` means the deterministic Risk gate is
# the next step, not that anything was approved.
type ReceiverDecision = Literal[
    "ready_for_risk_review",
    "validation_needed",
    "research_only",
    "rejected",
    "failed",
]

# A sweep verdict is advisory evidence. Language that reads as an order, an
# approval, or a size would misrepresent it as a decision to trade.
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
                "a sweep verdict is advisory evidence only"
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
        ValueError: If the mapping is oversized or an entry is invalid.
    """
    if len(value) > _MAX_ITEMS:
        message = f"{field} must not exceed {_MAX_ITEMS} entries"
        raise ValueError(message)
    frozen = {
        _text(key, f"{field} key", limit=_MAX_SHORT_TEXT): _advisory(
            _text(item, f"{field} statement", limit=_MAX_SHORT_TEXT),
            field,
        )
        for key, item in sorted(value.items())
    }
    return MappingProxyType(frozen)


class SweepPlan(BaseModel):
    """One bounded search declared in full before anything runs.

    Attributes:
        plan_id: Stable plan identity.
        task_id: Owning task identity.
        spec_hash: Pre-registered experiment protocol this sweep serves.
        parameter_space: Bounded candidate values per parameter name.
        objective: Objective the search optimises.
        method: Search method the receiver will use.
        trial_budget: Maximum trials this plan authorises.
        early_stop_policy: Condition that ends the search early.
        seed: Reproducibility seed for the search.
        holdout_consumption: Whether this sweep spends the thesis's holdout.
        prior_trials_consumed: Trials already spent on this thesis.
        justification: Why this budget and this space are appropriate.
        plan_hash: Derived digest over the pre-declared plan.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    plan_id: str
    task_id: str
    spec_hash: str
    parameter_space: Mapping[str, str]
    objective: str
    method: SearchMethod
    trial_budget: int
    early_stop_policy: str
    seed: int
    holdout_consumption: HoldoutConsumption
    prior_trials_consumed: int
    justification: str
    plan_hash: str

    @field_validator("plan_id", "task_id", "spec_hash", "objective", "plan_hash")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required plan reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "sweep plan reference", limit=_MAX_SHORT_TEXT)

    @field_validator("early_stop_policy", "justification")
    @classmethod
    def _validate_statement(cls, value: str) -> str:
        """Validate one required plan statement.

        Args:
            value: Candidate statement.

        Returns:
            Validated statement.
        """
        return _advisory(_text(value, "sweep plan statement"), "sweep plan statement")

    @field_validator("parameter_space")
    @classmethod
    def _validate_space(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze the bounded parameter space.

        Args:
            value: Candidate space.

        Returns:
            Frozen ordered space.

        Raises:
            ValueError: If the space is empty.
        """
        if not value:
            message = "a sweep plan must declare a bounded parameter space"
            raise ValueError(message)
        return _keyed(value, "parameter space")

    @field_validator("trial_budget")
    @classmethod
    def _validate_budget(cls, value: int) -> int:
        """Validate that the trial budget is a positive bound.

        Args:
            value: Candidate budget.

        Returns:
            Validated budget.

        Raises:
            ValueError: If the budget is not positive.
        """
        if value <= 0:
            message = "trial_budget must be positive; unbounded is not a budget"
            raise ValueError(message)
        return value

    @field_validator("prior_trials_consumed")
    @classmethod
    def _validate_prior(cls, value: int) -> int:
        """Validate the cumulative prior trial count.

        Args:
            value: Candidate prior count.

        Returns:
            Validated prior count.

        Raises:
            ValueError: If the count is negative.
        """
        if value < 0:
            message = "prior_trials_consumed must not be negative"
            raise ValueError(message)
        return value

    @property
    def lifetime_trials(self) -> int:
        """Return the cumulative trial count this plan would reach.

        Returns:
            Prior trials plus this plan's budget.
        """
        return self.prior_trials_consumed + self.trial_budget

    @field_serializer("parameter_space", mode="plain")
    def _serialize_space(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize the parameter space deterministically.

        Args:
            value: Frozen space.

        Returns:
            Plain ordered space.
        """
        return dict(value)


class TrialLedger(BaseModel):
    """Complete accounting of one search's attempted trials.

    The arithmetic is the point: a sweep that reports only its survivors is
    describing a different experiment from the one that ran, so attempted must
    equal completed plus failed and every failure must carry a reason.

    Attributes:
        attempted: Trials the search started.
        completed: Trials that produced a candidate.
        failed: Trials that errored, timed out, or produced nothing.
        failure_reasons: Reason per failed trial identifier.
        budget: Trial budget the plan authorised.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    attempted: int
    completed: int
    failed: int
    failure_reasons: Mapping[str, str]
    budget: int

    @field_validator("attempted", "completed", "failed", "budget")
    @classmethod
    def _validate_count(cls, value: int) -> int:
        """Validate one non-negative trial count.

        Args:
            value: Candidate count.

        Returns:
            Validated count.

        Raises:
            ValueError: If the count is negative.
        """
        if value < 0:
            message = "a trial count must not be negative"
            raise ValueError(message)
        return value

    @field_validator("failure_reasons")
    @classmethod
    def _validate_reasons(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze the per-trial failure reasons.

        Args:
            value: Candidate mapping.

        Returns:
            Frozen ordered mapping.
        """
        return _keyed(value, "failure reason")

    @model_validator(mode="after")
    def _validate_ledger(self) -> Self:
        """Validate that the trial accounting reconciles.

        Returns:
            The validated ledger.

        Raises:
            ValueError: If attempted does not equal completed plus failed, if
                the failure reasons do not cover the failed trials, or if the
                search exceeded the budget it was granted.
        """
        if self.attempted != self.completed + self.failed:
            message = (
                f"trial accounting does not reconcile: {self.attempted} attempted "
                f"but {self.completed} completed plus {self.failed} failed"
            )
            raise ValueError(message)
        if len(self.failure_reasons) != self.failed:
            message = (
                f"every failed trial requires a reason: {self.failed} failed but "
                f"{len(self.failure_reasons)} reasons were recorded"
            )
            raise ValueError(message)
        if self.attempted > self.budget:
            message = (
                f"the search attempted {self.attempted} trials against a budget of "
                f"{self.budget}"
            )
            raise ValueError(message)
        return self

    @field_serializer("failure_reasons", mode="plain")
    def _serialize_reasons(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize the failure reasons deterministically.

        Args:
            value: Frozen mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


class SweepVerdict(BaseModel):
    """One robustness-focused reading of a completed bounded search.

    Attributes:
        verdict_id: Stable verdict identity.
        task_id: Owning task identity.
        plan_id: Plan this verdict reads.
        plan_hash: Digest of the plan as pre-declared.
        search_id: Receiver-returned search identity.
        reproducibility_hash: Receiver-returned evidence identity.
        receiver_decision: The receiver's own classification, carried verbatim.
        trials: Complete trial accounting.
        selected_parameters: Best-ranked parameter set, reported last.
        robustness_evidence: What the deterministic robustness score returned.
        instability_evidence: What the deterministic stability check returned.
        overfit_evidence: What the deterministic overfit check returned.
        economic_effect: Whether the difference survives costs.
        unresolved_risk: What this sweep could not establish.
        holdout_consumed: Whether this sweep spent the thesis's holdout.
        lifetime_trials: Cumulative trials spent on this thesis.
        warnings: Receiver-returned warnings, preserved.
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
    search_id: str
    reproducibility_hash: str
    receiver_decision: ReceiverDecision
    trials: TrialLedger
    selected_parameters: Mapping[str, str]
    robustness_evidence: str
    instability_evidence: str
    overfit_evidence: str
    economic_effect: str
    unresolved_risk: tuple[str, ...]
    holdout_consumed: bool
    lifetime_trials: int
    warnings: tuple[str, ...] = ()

    @field_validator(
        "verdict_id",
        "task_id",
        "plan_id",
        "plan_hash",
        "search_id",
        "reproducibility_hash",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required verdict reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "sweep verdict reference", limit=_MAX_SHORT_TEXT)

    @field_validator(
        "robustness_evidence",
        "instability_evidence",
        "overfit_evidence",
        "economic_effect",
    )
    @classmethod
    def _validate_disclosure(cls, value: str) -> str:
        """Validate one required robustness disclosure.

        Args:
            value: Candidate disclosure.

        Returns:
            Validated disclosure.
        """
        return _advisory(_text(value, "sweep disclosure"), "sweep disclosure")

    @field_validator("unresolved_risk")
    @classmethod
    def _validate_unresolved(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the required unresolved-risk statements.

        Args:
            value: Candidate statements.

        Returns:
            Validated statements.
        """
        return _statements(value, "unresolved risk")

    @field_validator("warnings")
    @classmethod
    def _validate_warnings(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the preserved receiver warnings.

        Args:
            value: Candidate warnings.

        Returns:
            Validated warnings.

        Raises:
            ValueError: If the tuple is oversized.
        """
        if len(value) > _MAX_ITEMS:
            message = f"warnings must not exceed {_MAX_ITEMS} entries"
            raise ValueError(message)
        return tuple(_text(item, "warning") for item in value)

    @field_validator("selected_parameters")
    @classmethod
    def _validate_selected(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze the selected parameter set.

        Args:
            value: Candidate parameters.

        Returns:
            Frozen ordered parameters.
        """
        return _keyed(value, "selected parameter")

    @field_validator("lifetime_trials")
    @classmethod
    def _validate_lifetime(cls, value: int) -> int:
        """Validate the cumulative trial count.

        Args:
            value: Candidate count.

        Returns:
            Validated count.

        Raises:
            ValueError: If the count is negative.
        """
        if value < 0:
            message = "lifetime_trials must not be negative"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def _validate_verdict(self) -> Self:
        """Validate that the verdict accounts for the whole search.

        Returns:
            The validated verdict.

        Raises:
            ValueError: If parameters are selected from a search that completed
                no trial, or if the cumulative count is smaller than this
                search alone.
        """
        if self.selected_parameters and self.trials.completed == 0:
            message = (
                "parameters cannot be selected from a search in which no trial "
                "completed"
            )
            raise ValueError(message)
        if self.lifetime_trials < self.trials.attempted:
            message = (
                "lifetime_trials cannot be smaller than the trials this search "
                "attempted"
            )
            raise ValueError(message)
        return self

    @field_serializer("selected_parameters", mode="plain")
    def _serialize_selected(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize the selected parameters deterministically.

        Args:
            value: Frozen mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


def derive_plan_hash(fields: Mapping[str, object]) -> str:
    """Derive the pre-declaration digest of one sweep plan.

    The digest covers the plan as declared before any trial runs, so a budget,
    space, or stop rule rewritten afterwards yields a different plan.

    Args:
        fields: Plan fields excluding the derived digest.

    Returns:
        The canonical content digest.
    """
    payload = {key: value for key, value in fields.items() if key != "plan_hash"}
    return canonical_digest(payload)


def build_sweep_plan(fields: Mapping[str, object]) -> SweepPlan:
    """Build one pre-declared bounded sweep plan.

    Args:
        fields: Complete plan fields excluding the derived digest.

    Returns:
        A validated immutable plan carrying its declaration digest.
    """
    logger.debug("Building a bounded sweep plan")
    return SweepPlan.model_validate(
        {**fields, "plan_hash": derive_plan_hash(fields)},
    )


def build_trial_ledger(fields: Mapping[str, object]) -> TrialLedger:
    """Build one reconciled trial ledger.

    Args:
        fields: Complete ledger fields.

    Returns:
        A validated immutable ledger.
    """
    return TrialLedger.model_validate(fields)


def build_sweep_verdict(fields: Mapping[str, object]) -> SweepVerdict:
    """Build one robustness-focused sweep verdict.

    Args:
        fields: Complete verdict fields.

    Returns:
        A validated immutable verdict.
    """
    logger.debug("Building a sweep verdict")
    return SweepVerdict.model_validate(fields)
