"""Deliberation plans, counterclaims, dissent, and immutable records.

A plan is resolved from the mandate and the versioned limits profile before
any model runs. Participants, rounds, and fan-out are deterministic caps; no
model or caller supplies them.

Consensus is not authorization. A `DeliberationRecord` records that
participants agreed, and is structurally incapable of carrying an approval or
a position size, so agreement can never be converted into a decision.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime, timedelta
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

from app.agentic.contracts.models import (
    AgentMessage,  # noqa: TC001 - runtime annotation
)
from app.utils import canonical_digest, get_logger

logger = get_logger(__name__)

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_MAX_TEXT = 2_000
_MAX_SHORT_TEXT = 200
_MAX_ITEMS = 64

# A challenge stance is assigned for one task. It is not a standing belief and
# creates no package, prompt, permission, or role.
ChallengeStance = Literal[
    "analyst",
    "proposer",
    "constructive_challenger",
    "adversarial_challenger",
    "synthesizer",
]

DeliberationTopology = Literal["independent_briefs_then_bounded_challenge"]

TerminalReason = Literal[
    "objective_complete",
    "insufficient_evidence",
    "material_unresolved_conflict",
    "max_rounds_reached",
    "deadline_exceeded",
    "budget_exhausted",
    "policy_denied",
    "no_eligible_participants",
    "operator_cancelled",
]

DissentBasis = Literal[
    "conflicting_evidence",
    "insufficient_evidence",
    "methodology",
    "scope",
    "unverifiable_claim",
]

# Language that would turn an advisory synthesis into an authorization or a
# sizing instruction. Agentic owns neither (`FR-AGENTIC-020`).
_AUTHORIZATION_PHRASES: tuple[str, ...] = (
    "approved",
    "i approve",
    "authorization granted",
    "authorised to execute",
    "authorized to execute",
    "position size",
    "position_size",
    "lot size",
    "lot_size",
    "order size",
    "order_size",
    "execute this trade",
    "place the order",
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


def reject_authorization_language(value: str, field: str) -> str:
    """Reject text that would read as an authorization or a position size.

    Args:
        value: Candidate advisory text.
        field: Safe field label for validation.

    Returns:
        The unchanged text.

    Raises:
        ValueError: If the text carries authorization or sizing language.
    """
    lowered = value.lower()
    for phrase in _AUTHORIZATION_PHRASES:
        if phrase in lowered:
            message = (
                f"{field} must not carry authorization or position-size language; "
                "consensus is not authorization"
            )
            raise ValueError(message)
    return value


class _DeliberationModel(BaseModel):
    """Private strict immutable behaviour shared by deliberation contracts."""

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )


class DeliberationPlan(_DeliberationModel):
    """The deterministic plan one bounded deliberation runs under.

    Attributes:
        plan_id: Stable plan identity.
        task_id: Owning task identity.
        objective: Bounded deliberation objective.
        topology: Discussion topology.
        participants: Ordered selected role identities.
        stances: Assigned per-task challenge stance by role.
        max_participants: Cap resolved from the limits profile.
        max_rounds: Bounded rebuttal-round cap.
        max_fan_out: Bounded parallel-branch cap.
        deadline_at: UTC deadline for the deliberation.
        budgets: Bounded budget limits by dimension.
        limits_profile_id: Versioned limits profile the caps came from.
        created_at: UTC plan creation time.
    """

    plan_id: str
    task_id: str
    objective: str
    topology: DeliberationTopology
    participants: tuple[str, ...]
    stances: Mapping[str, str]
    max_participants: int
    max_rounds: int
    max_fan_out: int
    deadline_at: datetime
    budgets: Mapping[str, Decimal]
    limits_profile_id: str
    created_at: datetime

    @field_validator("plan_id", "task_id", "limits_profile_id")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded plan reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "plan reference", limit=_MAX_SHORT_TEXT)

    @field_validator("objective")
    @classmethod
    def _validate_objective(cls, value: str) -> str:
        """Validate the bounded deliberation objective.

        Args:
            value: Candidate objective.

        Returns:
            Validated objective.
        """
        return _text(value, "objective")

    @field_validator("participants")
    @classmethod
    def _validate_participants(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the selected participants.

        Args:
            value: Candidate role identities.

        Returns:
            Validated role identities.

        Raises:
            ValueError: If the tuple is oversized or repeats a role.
        """
        if len(value) > _MAX_ITEMS:
            message = f"participants must not exceed {_MAX_ITEMS} entries"
            raise ValueError(message)
        validated = tuple(
            _text(item, "participant", limit=_MAX_SHORT_TEXT) for item in value
        )
        if len(set(validated)) != len(validated):
            message = "participants must not repeat a role"
            raise ValueError(message)
        return validated

    @field_validator("stances")
    @classmethod
    def _validate_stances(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze the assigned challenge stances.

        Args:
            value: Candidate stance mapping.

        Returns:
            Frozen ordered stance mapping.
        """
        frozen = {
            _text(key, "stance role", limit=_MAX_SHORT_TEXT): _text(
                item,
                "stance",
                limit=_MAX_SHORT_TEXT,
            )
            for key, item in sorted(value.items())
        }
        return MappingProxyType(frozen)

    @field_validator("max_participants", "max_rounds", "max_fan_out")
    @classmethod
    def _validate_cap(cls, value: int) -> int:
        """Validate one deterministic cap.

        Args:
            value: Candidate cap.

        Returns:
            Validated cap.

        Raises:
            ValueError: If the cap is not positive.
        """
        if value <= 0:
            message = "deliberation caps must be positive"
            raise ValueError(message)
        return value

    @field_validator("deadline_at", "created_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one plan timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        return _utc(value, "plan timestamp")

    @field_validator("budgets")
    @classmethod
    def _validate_budgets(cls, value: Mapping[str, Decimal]) -> Mapping[str, Decimal]:
        """Validate and freeze the declared budgets.

        Args:
            value: Candidate budget mapping.

        Returns:
            Frozen ordered budget mapping.

        Raises:
            ValueError: If a limit is non-finite or negative.
        """
        frozen: dict[str, Decimal] = {}
        for key, item in sorted(value.items()):
            if not item.is_finite() or item < 0:
                message = "budget limits must be finite and non-negative"
                raise ValueError(message)
            frozen[_text(key, "budget", limit=_MAX_SHORT_TEXT)] = item
        return MappingProxyType(frozen)

    @model_validator(mode="after")
    def _validate_plan(self) -> Self:
        """Validate that the plan respects its own caps.

        Returns:
            The validated plan.

        Raises:
            ValueError: If participants exceed the cap or a stance names a
                role that is not a participant.
        """
        if len(self.participants) > self.max_participants:
            message = (
                f"{len(self.participants)} participants exceed the cap of "
                f"{self.max_participants}"
            )
            raise ValueError(message)
        unknown = sorted(set(self.stances) - set(self.participants))
        if unknown:
            message = f"stances name non-participants: {', '.join(unknown)}"
            raise ValueError(message)
        return self

    @field_serializer("stances", mode="plain")
    def _serialize_stances(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize the stance mapping deterministically.

        Args:
            value: Frozen stance mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)

    @field_serializer("budgets", mode="plain")
    def _serialize_budgets(self, value: Mapping[str, Decimal]) -> dict[str, str]:
        """Serialize budgets without precision loss.

        Args:
            value: Frozen budget mapping.

        Returns:
            Plain ordered mapping of canonical decimal strings.
        """
        return {key: str(item) for key, item in value.items()}


class Counterclaim(_DeliberationModel):
    """One typed challenge raised against a claim during deliberation.

    Attributes:
        counterclaim_id: Stable counterclaim identity.
        task_id: Owning task identity.
        round_index: Zero-based rebuttal round.
        challenger_role_id: Registered challenging role.
        stance: Challenge stance assigned for this task.
        targets_claim_id: Claim being challenged.
        statement: Bounded challenge statement.
        evidence_refs: Supporting evidence references.
        resolved: Whether the challenge was resolved by evidence.
    """

    counterclaim_id: str
    task_id: str
    round_index: int
    challenger_role_id: str
    stance: ChallengeStance
    targets_claim_id: str
    statement: str
    evidence_refs: tuple[str, ...] = ()
    resolved: bool = False

    @field_validator(
        "counterclaim_id",
        "task_id",
        "challenger_role_id",
        "targets_claim_id",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded counterclaim reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "counterclaim reference", limit=_MAX_SHORT_TEXT)

    @field_validator("statement")
    @classmethod
    def _validate_statement(cls, value: str) -> str:
        """Validate the bounded challenge statement.

        Args:
            value: Candidate statement.

        Returns:
            Validated statement.
        """
        return reject_authorization_language(
            _text(value, "counterclaim statement"),
            "counterclaim statement",
        )

    @field_validator("round_index")
    @classmethod
    def _validate_round(cls, value: int) -> int:
        """Validate the rebuttal round index.

        Args:
            value: Candidate round index.

        Returns:
            Validated round index.

        Raises:
            ValueError: If the index is negative.
        """
        if value < 0:
            message = "round_index must be non-negative"
            raise ValueError(message)
        return value

    @field_validator("evidence_refs")
    @classmethod
    def _validate_refs(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the supporting evidence references.

        Args:
            value: Candidate references.

        Returns:
            Validated references.

        Raises:
            ValueError: If the tuple is oversized.
        """
        if len(value) > _MAX_ITEMS:
            message = f"evidence_refs must not exceed {_MAX_ITEMS} entries"
            raise ValueError(message)
        return tuple(
            _text(item, "evidence ref", limit=_MAX_SHORT_TEXT) for item in value
        )


class DissentRecord(_DeliberationModel):
    """One preserved minority position that synthesis did not resolve.

    Attributes:
        dissent_id: Stable dissent identity.
        task_id: Owning task identity.
        dissenting_role_id: Registered dissenting role.
        statement: Bounded dissent statement.
        basis: Enumerated basis for the dissent.
        targets_claim_id: Claim dissented from, when applicable.
        unresolved: Whether the dissent remains materially unresolved.
    """

    dissent_id: str
    task_id: str
    dissenting_role_id: str
    statement: str
    basis: DissentBasis
    targets_claim_id: str | None = None
    unresolved: bool = True

    @field_validator("dissent_id", "task_id", "dissenting_role_id")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded dissent reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "dissent reference", limit=_MAX_SHORT_TEXT)

    @field_validator("statement")
    @classmethod
    def _validate_statement(cls, value: str) -> str:
        """Validate the bounded dissent statement.

        Args:
            value: Candidate statement.

        Returns:
            Validated statement.
        """
        return reject_authorization_language(
            _text(value, "dissent statement"),
            "dissent statement",
        )

    @field_validator("targets_claim_id")
    @classmethod
    def _validate_target(cls, value: str | None) -> str | None:
        """Validate the optional dissent target.

        Args:
            value: Candidate claim identity.

        Returns:
            Validated claim identity, or None.
        """
        if value is None:
            return None
        return _text(value, "targets_claim_id", limit=_MAX_SHORT_TEXT)


class DeliberationRecord(_DeliberationModel):
    """The immutable record of one bounded deliberation.

    Attributes:
        record_id: Stable record identity.
        task_id: Owning task identity.
        plan: Deterministic plan the deliberation ran under.
        messages: Ordered typed messages, briefs first.
        counterclaims: Ordered typed challenges raised.
        dissent: Ordered preserved minority positions.
        synthesis: Bounded advisory synthesis, absent when refused.
        consensus_reached: Whether participants agreed; never an authorization.
        rounds_used: Rebuttal rounds actually consumed.
        participants_used: Participants that actually produced a brief.
        refusals: Ordered role identities that refused.
        terminal_reason: Enumerated stop reason.
        persisted: Whether the record reached a governed audit store.
        created_at: UTC completion time.
        content_hash: Canonical digest of the record material.
    """

    record_id: str
    task_id: str
    plan: DeliberationPlan
    messages: tuple[AgentMessage, ...]
    counterclaims: tuple[Counterclaim, ...]
    dissent: tuple[DissentRecord, ...]
    synthesis: str | None
    consensus_reached: bool
    rounds_used: int
    participants_used: int
    refusals: tuple[str, ...]
    terminal_reason: TerminalReason
    persisted: bool
    created_at: datetime
    content_hash: str

    @field_validator("record_id", "task_id")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded record reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "record reference", limit=_MAX_SHORT_TEXT)

    @field_validator("synthesis")
    @classmethod
    def _validate_synthesis(cls, value: str | None) -> str | None:
        """Validate the bounded advisory synthesis.

        Args:
            value: Candidate synthesis.

        Returns:
            Validated synthesis, or None.
        """
        if value is None:
            return None
        return reject_authorization_language(_text(value, "synthesis"), "synthesis")

    @field_validator("rounds_used", "participants_used")
    @classmethod
    def _validate_counter(cls, value: int) -> int:
        """Validate one non-negative record counter.

        Args:
            value: Candidate counter.

        Returns:
            Validated counter.

        Raises:
            ValueError: If the counter is negative.
        """
        if value < 0:
            message = "record counters must be non-negative"
            raise ValueError(message)
        return value

    @field_validator("refusals")
    @classmethod
    def _validate_refusals(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the recorded refusals.

        Args:
            value: Candidate role identities.

        Returns:
            Validated role identities.
        """
        return tuple(_text(item, "refusal", limit=_MAX_SHORT_TEXT) for item in value)

    @field_validator("created_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate the completion timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        return _utc(value, "created_at")

    @field_validator("content_hash")
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        """Validate the record content digest.

        Args:
            value: Candidate digest.

        Returns:
            Validated digest.

        Raises:
            ValueError: If the digest shape is invalid.
        """
        if _SHA256.fullmatch(value) is None:
            message = "content_hash must be lowercase SHA-256 hexadecimal"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def _validate_record(self) -> Self:
        """Validate caps, dissent preservation, and terminal agreement.

        Returns:
            The validated record.

        Raises:
            ValueError: If the record exceeds a declared cap, claims a
                synthesis while refusing, or claims consensus while material
                dissent remains unresolved.
        """
        if self.rounds_used > self.plan.max_rounds:
            message = (
                f"{self.rounds_used} rounds exceed the plan cap of "
                f"{self.plan.max_rounds}"
            )
            raise ValueError(message)
        if self.participants_used > self.plan.max_participants:
            message = "participants used exceed the plan cap"
            raise ValueError(message)
        if (
            self.terminal_reason == "insufficient_evidence"
            and self.synthesis is not None
        ):
            message = "an insufficient_evidence outcome must carry no synthesis"
            raise ValueError(message)
        # Consensus is a description of agreement, never an authorization, and
        # it cannot be claimed while a material dissent stands unresolved.
        if self.consensus_reached and any(item.unresolved for item in self.dissent):
            message = "consensus cannot be claimed while dissent remains unresolved"
            raise ValueError(message)
        return self


def derive_record_hash(value: object) -> str:
    """Derive the canonical digest of deliberation record material.

    Args:
        value: JSON-safe record material.

    Returns:
        The canonical record digest.
    """
    return canonical_digest(value)
