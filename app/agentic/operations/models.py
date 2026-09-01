"""Correlated traces, incident records, and isolated replay requests.

`AgenticTrace` makes coverage exact (`FR-AGENTIC-061`): the ten span kinds the
requirement names are validated by set equality, so a trace that silently omits
its guardrail or approval spans is unrepresentable rather than merely thinner.
Redaction is inherited, not reimplemented — spans are assembled from
`MemoryRecord`s that `FEAT-AGT-06` already redacted at write, and the trace
carries the union of their redacted paths so an operator can see that redaction
occurred.

`IncidentRecord` makes containment deterministic (`FR-AGENTIC-062`): the action
follows from the incident kind through a fixed table, not from a caller's
preference, and a record reporting containment without preserved evidence
cannot be built. Containing an incident and discarding what caused it is the
failure mode this refuses.

`ReplayRequest` makes isolation structural (`FR-AGENTIC-063`): the environment
is fixed to `sandbox` by the type, every reference is an immutable content
digest, and a replay outcome reporting any attempted side effect is rejected.
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

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest

logger = get_logger(__name__)

_MAX_TEXT = 2_000
_MAX_SHORT_TEXT = 200
_MAX_ITEMS = 64

# `FR-AGENTIC-061` names ten things that must be covered. Validation is by set
# equality: a trace missing its approval spans is not a partial trace but an
# impossible one, and a kind nobody agreed to is refused just as firmly.
REQUIRED_SPAN_KINDS: frozenset[str] = frozenset(
    {
        "agent",
        "approval",
        "cost",
        "failure",
        "guardrail",
        "handoff",
        "model",
        "state_transition",
        "tool",
        "workflow",
    },
)

# `FR-AGENTIC-062` names nine incident classes.
INCIDENT_KINDS: frozenset[str] = frozenset(
    {
        "cost",
        "data_poisoning",
        "drift",
        "injection",
        "privilege",
        "provider",
        "runaway_loop",
        "sandbox",
        "schema",
    },
)

type IncidentKind = Literal[
    "cost",
    "data_poisoning",
    "drift",
    "injection",
    "privilege",
    "provider",
    "runaway_loop",
    "sandbox",
    "schema",
]

type ContainmentAction = Literal["cancel", "quarantine", "quarantine_and_cancel"]

# What each incident kind requires. The action is a property of the kind, not a
# judgement at the call site: an injection incident contains the same way every
# time, whoever reports it and whatever they would prefer.
_CONTAINMENT: Mapping[str, str] = MappingProxyType(
    {
        # A poisoned or hijacked role must stop *and* be prevented from taking
        # the next task; cancelling the run alone leaves the role eligible.
        "data_poisoning": "quarantine_and_cancel",
        "injection": "quarantine_and_cancel",
        "privilege": "quarantine_and_cancel",
        "sandbox": "quarantine_and_cancel",
        # Drift is a property of the role rather than of one run, so the run
        # may complete while the role stops taking new work.
        "drift": "quarantine",
        # A bounded failure of one run. The role is not implicated.
        "cost": "cancel",
        "provider": "cancel",
        "runaway_loop": "cancel",
        "schema": "cancel",
    },
)

# Replay is permitted in exactly one environment. Declaring it as a literal
# rather than validating a string means a production replay is unconstructable.
type ReplayEnvironment = Literal["sandbox"]


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


def _entries(
    value: tuple[str, ...],
    field: str,
    *,
    required: bool = False,
) -> tuple[str, ...]:
    """Validate one bounded tuple of operational references.

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
    return tuple(_text(item, field, limit=_MAX_SHORT_TEXT) for item in value)


def _keyed(value: Mapping[str, str], field: str) -> Mapping[str, str]:
    """Validate and freeze one bounded keyed operational mapping.

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
        )
        for key, item in sorted(value.items())
    }
    return MappingProxyType(frozen)


def missing_span_kinds(spans: Mapping[str, str]) -> tuple[str, ...]:
    """Return the required span kinds a trace does not cover.

    Args:
        spans: Covered span kind to bounded summary.

    Returns:
        Ordered missing span kinds.
    """
    return tuple(sorted(REQUIRED_SPAN_KINDS - set(spans)))


def unknown_span_kinds(spans: Mapping[str, str]) -> tuple[str, ...]:
    """Return covered span kinds that are not required kinds.

    Args:
        spans: Covered span kind to bounded summary.

    Returns:
        Ordered unrecognized span kinds.
    """
    return tuple(sorted(set(spans) - REQUIRED_SPAN_KINDS))


def required_containment(kind: str) -> str:
    """Return the containment one incident kind requires.

    Args:
        kind: Enumerated incident kind.

    Returns:
        The enumerated containment action.

    Raises:
        ValueError: If the kind is not a recognized incident.
    """
    action = _CONTAINMENT.get(kind)
    if action is None:
        message = f"{kind!r} is not a recognized incident kind"
        raise ValueError(message)
    return action


class AgenticTrace(BaseModel):
    """One correlated redacted view of everything a run did.

    Attributes:
        trace_id: Stable trace identity.
        correlation_id: Identifier every span shares.
        task_id: Owning task identity.
        run_id: Run this trace describes.
        spans: Bounded summary per required span kind.
        record_count: Audit records the trace was assembled from.
        redacted_paths: Union of paths redacted before persistence.
        observed_cost: Cost the run consumed, as reported.
        assembled_at: Assembly time, as an ISO-8601 UTC string.
        trace_hash: Derived digest over the whole trace.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    trace_id: str
    correlation_id: str
    task_id: str
    run_id: str
    spans: Mapping[str, str]
    record_count: int
    redacted_paths: tuple[str, ...]
    observed_cost: Decimal
    assembled_at: str
    trace_hash: str

    @field_validator(
        "trace_id",
        "correlation_id",
        "task_id",
        "run_id",
        "assembled_at",
        "trace_hash",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required trace reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "trace reference", limit=_MAX_SHORT_TEXT)

    @field_validator("spans")
    @classmethod
    def _validate_spans(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze the covered spans.

        Args:
            value: Candidate mapping.

        Returns:
            Frozen ordered mapping.

        Raises:
            ValueError: If a required span kind is missing or unknown.
        """
        missing = missing_span_kinds(value)
        if missing:
            message = (
                "a trace must cover every required span kind; missing: "
                f"{', '.join(missing)}"
            )
            raise ValueError(message)
        unknown = unknown_span_kinds(value)
        if unknown:
            message = f"unrecognized span kinds: {', '.join(unknown)}"
            raise ValueError(message)
        return _keyed(value, "trace span")

    @field_validator("redacted_paths")
    @classmethod
    def _validate_paths(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the union of redacted paths.

        Args:
            value: Candidate paths.

        Returns:
            Validated paths.
        """
        return _entries(value, "redacted path")

    @field_validator("record_count")
    @classmethod
    def _validate_count(cls, value: int) -> int:
        """Validate the assembled record count.

        Args:
            value: Candidate count.

        Returns:
            Validated count.

        Raises:
            ValueError: If the count is negative.
        """
        if value < 0:
            message = "a trace cannot be assembled from a negative record count"
            raise ValueError(message)
        return value

    @field_validator("observed_cost")
    @classmethod
    def _validate_cost(cls, value: Decimal) -> Decimal:
        """Validate the reported cost.

        Args:
            value: Candidate cost.

        Returns:
            Validated cost.

        Raises:
            ValueError: If the cost is negative.
        """
        if value < 0:
            message = "a trace cannot report a negative cost"
            raise ValueError(message)
        return value

    @field_serializer("spans", mode="plain")
    def _serialize_spans(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize the spans deterministically.

        Args:
            value: Frozen mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)

    @field_serializer("observed_cost", mode="plain")
    def _serialize_cost(self, value: Decimal) -> str:
        """Serialize the cost deterministically.

        Args:
            value: Reported cost.

        Returns:
            The canonical decimal string.
        """
        return str(value)


class IncidentRecord(BaseModel):
    """One classified incident, its containment, and the evidence it kept.

    Attributes:
        incident_id: Stable incident identity.
        task_id: Owning task identity.
        run_id: Run the incident occurred in.
        correlation_id: Identifier linking the incident to its trace.
        kind: Enumerated incident classification.
        trigger: Bounded description of what was observed.
        containment_action: What the kind required.
        contained_state: Durable run state after containment.
        quarantined_role_id: Role prevented from taking new work, when one was.
        preserved_evidence_refs: Evidence references kept, never discarded.
        checkpoint_ref: Checkpoint preserved rather than dropped.
        detected_at: Detection time, as an ISO-8601 UTC string.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    incident_id: str
    task_id: str
    run_id: str
    correlation_id: str
    kind: IncidentKind
    trigger: str
    containment_action: ContainmentAction
    contained_state: str
    preserved_evidence_refs: tuple[str, ...]
    checkpoint_ref: str
    detected_at: str
    quarantined_role_id: str | None = None

    @field_validator(
        "incident_id",
        "task_id",
        "run_id",
        "correlation_id",
        "contained_state",
        "checkpoint_ref",
        "detected_at",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required incident reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "incident reference", limit=_MAX_SHORT_TEXT)

    @field_validator("quarantined_role_id")
    @classmethod
    def _validate_role(cls, value: str | None) -> str | None:
        """Validate the optional quarantined role identity.

        Args:
            value: Candidate role identity.

        Returns:
            Validated identity, or None.
        """
        if value is None:
            return None
        return _text(value, "quarantined role", limit=_MAX_SHORT_TEXT)

    @field_validator("trigger")
    @classmethod
    def _validate_trigger(cls, value: str) -> str:
        """Validate the incident trigger description.

        Args:
            value: Candidate description.

        Returns:
            Validated description.
        """
        return _text(value, "incident trigger")

    @field_validator("preserved_evidence_refs")
    @classmethod
    def _validate_evidence(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the preserved evidence references.

        Containment without preservation is the failure mode this refuses: an
        incident that discards what caused it cannot be investigated.

        Args:
            value: Candidate references.

        Returns:
            Validated references.
        """
        return _entries(value, "preserved evidence", required=True)

    @model_validator(mode="after")
    def _validate_containment(self) -> Self:
        """Validate that containment matches what the incident kind requires.

        Returns:
            The validated record.

        Raises:
            ValueError: If the action disagrees with the kind, or a quarantine
                is claimed without or against a role.
        """
        expected = required_containment(self.kind)
        if self.containment_action != expected:
            message = (
                f"a {self.kind!r} incident requires {expected!r} containment, "
                f"not {self.containment_action!r}"
            )
            raise ValueError(message)
        quarantines = self.containment_action in {"quarantine", "quarantine_and_cancel"}
        if quarantines and self.quarantined_role_id is None:
            message = (
                f"{self.containment_action!r} containment must name the role it "
                "quarantined"
            )
            raise ValueError(message)
        if not quarantines and self.quarantined_role_id is not None:
            message = (
                f"{self.containment_action!r} containment quarantines no role; "
                "naming one misreports what happened"
            )
            raise ValueError(message)
        return self


class ReplayRequest(BaseModel):
    """One request to replay a run against immutable references only.

    Attributes:
        replay_id: Stable replay identity.
        run_id: Run to replay.
        task_id: Owning task identity of the original run.
        environment: Environment the replay targets; always `sandbox`.
        reference_hashes: Content digest per referenced evidence record.
        requested_by: Principal requesting the replay.
        requested_at: Request time, as an ISO-8601 UTC string.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    replay_id: str
    run_id: str
    task_id: str
    environment: ReplayEnvironment
    reference_hashes: Mapping[str, str]
    requested_by: str
    requested_at: str

    @field_validator(
        "replay_id",
        "run_id",
        "task_id",
        "requested_by",
        "requested_at",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required replay reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "replay reference", limit=_MAX_SHORT_TEXT)

    @field_validator("reference_hashes")
    @classmethod
    def _validate_hashes(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze the immutable references.

        Args:
            value: Candidate mapping.

        Returns:
            Frozen ordered mapping.

        Raises:
            ValueError: If no reference is declared.
        """
        if not value:
            message = "a replay must name the immutable references it reads"
            raise ValueError(message)
        return _keyed(value, "replay reference")

    @field_serializer("reference_hashes", mode="plain")
    def _serialize_hashes(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize the references deterministically.

        Args:
            value: Frozen mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


class ReplayOutcome(BaseModel):
    """What one validated replay is permitted to do, and what it did.

    Attributes:
        replay_id: Replay this outcome answers.
        run_id: Run that was replayed.
        environment: Environment the replay ran in.
        verified_references: References whose digests still matched.
        side_effects_attempted: External side effects attempted; always zero.
        executed: Whether an isolated executor actually ran the replay.
        completed_at: Outcome time, as an ISO-8601 UTC string.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    replay_id: str
    run_id: str
    environment: ReplayEnvironment
    verified_references: tuple[str, ...]
    side_effects_attempted: int
    executed: bool
    completed_at: str

    @field_validator("replay_id", "run_id", "completed_at")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required outcome reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "replay reference", limit=_MAX_SHORT_TEXT)

    @field_validator("verified_references")
    @classmethod
    def _validate_verified(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the verified reference identities.

        Args:
            value: Candidate references.

        Returns:
            Validated references.
        """
        return _entries(value, "verified reference", required=True)

    @field_validator("side_effects_attempted")
    @classmethod
    def _validate_side_effects(cls, value: int) -> int:
        """Validate that the replay attempted no external side effect.

        Args:
            value: Candidate count.

        Returns:
            Validated count.

        Raises:
            ValueError: If any side effect was attempted.
        """
        if value != 0:
            message = (
                "a replay that attempted an external side effect is not a "
                f"replay; {value} attempted"
            )
            raise ValueError(message)
        return value


def derive_trace_hash(fields: Mapping[str, object]) -> str:
    """Derive the content digest of one assembled trace.

    Args:
        fields: Trace fields excluding the derived digest.

    Returns:
        The canonical content digest.
    """
    payload = {
        key: str(value) if isinstance(value, Decimal) else value
        for key, value in sorted(fields.items())
        if key != "trace_hash"
    }
    return canonical_digest(payload)


def build_agentic_trace(fields: Mapping[str, object]) -> AgenticTrace:
    """Build one correlated redacted trace.

    Args:
        fields: Complete trace fields excluding the derived digest.

    Returns:
        A validated immutable trace carrying its content digest.
    """
    logger.debug("Building an Agentic trace")
    return AgenticTrace.model_validate(
        {**fields, "trace_hash": derive_trace_hash(fields)},
    )


def build_incident_record(fields: Mapping[str, object]) -> IncidentRecord:
    """Build one classified incident record.

    Args:
        fields: Complete record fields.

    Returns:
        A validated immutable incident record.
    """
    logger.debug("Building an incident record")
    return IncidentRecord.model_validate(fields)


def build_replay_request(fields: Mapping[str, object]) -> ReplayRequest:
    """Build one isolated replay request.

    Args:
        fields: Complete request fields.

    Returns:
        A validated immutable replay request.
    """
    logger.debug("Building a replay request")
    return ReplayRequest.model_validate(fields)


def build_replay_outcome(fields: Mapping[str, object]) -> ReplayOutcome:
    """Build one replay outcome.

    Args:
        fields: Complete outcome fields.

    Returns:
        A validated immutable replay outcome.
    """
    return ReplayOutcome.model_validate(fields)
