"""Canonical immutable Agentic boundary contracts and provenance.

This module owns `FEAT-AGT-01` and implements `FR-AGENTIC-001` through
`FR-AGENTIC-003`. Every contract is provider-neutral: no Google ADK object,
provider SDK object, broker field, or deterministic-domain implementation type
may appear here.

Module flow: untrusted typed data -> strict validation and canonical hashing ->
immutable contract.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from types import MappingProxyType
from typing import Literal, Self, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from app.utils import canonical_digest, get_logger, validate_id

logger = get_logger(__name__)

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_REASON_CODE = re.compile(r"[A-Z][A-Z0-9_]{2,63}\Z")

# Bounded sizes keep every contract finite and JSON-safe (FR-AGENTIC-001).
_MAX_TEXT = 2_000
_MAX_SHORT_TEXT = 200
_MAX_SEQUENCE_ITEMS = 64
_MAX_MAPPING_KEYS = 32

# Budget dimensions an `AgentTask` may bound. `BudgetUsage` reports consumption
# against exactly these dimensions, so limits and usage stay comparable.
_BUDGET_DIMENSIONS = frozenset(
    {
        "compute_seconds",
        "cost",
        "model_calls",
        "search_trials",
        "storage_bytes",
        "tokens",
        "tool_calls",
    },
)

# Substrings that would turn advisory Agentic output into an execution
# instruction. Agentic owns no order, credential, approval, sizing, or
# kill-switch authority, so these may never reach a contract field
# (`FR-AGENTIC-002`; constitution articles 6 and 7).
_PROHIBITED_EXECUTION_TOKENS = frozenset(
    {
        "api_key",
        "approval_token",
        "broker",
        "credential",
        "kill_switch",
        "lot_size",
        "order_ticket",
        "password",
        "position_size",
        "secret",
    },
)

# Model identifiers must pin one exact evaluated model. Floating aliases would
# allow a silent provider substitution in a governed workflow (`FR-AGENTIC-008`).
_FLOATING_MODEL_ALIASES = frozenset({"current", "latest", "newest", "stable"})

MessageType = Literal[
    "brief",
    "claim",
    "counterclaim",
    "dissent",
    "evidence_request",
    "rebuttal",
    "refusal",
    "synthesis",
    "tool_evidence",
]

WorkflowState = Literal[
    "cancelled",
    "expired",
    "failed",
    "refused",
    "running",
    "submitted",
    "succeeded",
    "waiting_human",
]

ResultStatus = Literal["failed", "ok", "refused"]


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
    logger.debug("Validating Agentic text field %s", field)
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
    logger.debug("Validating Agentic UTC field %s", field)
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        message = f"{field} must be aware UTC"
        raise ValueError(message)
    return value


def _hash(value: str, field: str) -> str:
    """Validate lowercase SHA-256 hexadecimal.

    Args:
        value: Candidate digest.
        field: Safe field label for validation.

    Returns:
        Validated digest.

    Raises:
        ValueError: If the digest shape is invalid.
    """
    logger.debug("Validating Agentic digest field %s", field)
    if _SHA256.fullmatch(value) is None:
        message = f"{field} must be lowercase SHA-256 hexadecimal"
        raise ValueError(message)
    return value


def _identity(value: str, field: str) -> str:
    """Validate one canonical Agentic stable identifier.

    Agentic entity identities use the Utils stable ``id`` prefix so that every
    contract identity is reproducible from canonical material.

    Args:
        value: Candidate identifier.
        field: Safe field label for validation.

    Returns:
        Validated identifier.

    Raises:
        ValueError: If the identifier is not a canonical stable identifier.
    """
    logger.debug("Validating Agentic identity field %s", field)
    try:
        return validate_id(value, expected_prefix="id")
    except Exception as error:
        message = f"{field} must be a canonical stable identifier"
        raise ValueError(message) from error


def _trace(value: str, field: str, prefix: str) -> str:
    """Validate one canonical prefixed UUID4 trace identifier.

    Args:
        value: Candidate trace identifier.
        field: Safe field label for validation.
        prefix: Required Utils trace prefix.

    Returns:
        Validated trace identifier.

    Raises:
        ValueError: If the identifier or prefix is invalid.
    """
    logger.debug("Validating Agentic trace field %s", field)
    try:
        return validate_id(value, expected_prefix=prefix)
    except Exception as error:
        message = f"{field} must be a canonical {prefix} trace identifier"
        raise ValueError(message) from error


def _count(value: int, field: str) -> int:
    """Validate a non-negative bounded counter.

    Args:
        value: Candidate counter.
        field: Safe field label for validation.

    Returns:
        Validated counter.

    Raises:
        ValueError: If the counter is negative.
    """
    logger.debug("Validating Agentic counter field %s", field)
    if value < 0:
        message = f"{field} must be non-negative"
        raise ValueError(message)
    return value


def _amount(value: Decimal, field: str) -> Decimal:
    """Validate a finite non-negative exact amount.

    Args:
        value: Candidate exact amount.
        field: Safe field label for validation.

    Returns:
        Validated amount.

    Raises:
        ValueError: If the amount is non-finite or negative.
    """
    logger.debug("Validating Agentic amount field %s", field)
    if not value.is_finite():
        message = f"{field} must be finite"
        raise ValueError(message)
    if value < 0:
        message = f"{field} must be non-negative"
        raise ValueError(message)
    return value


def _reference_tuple(value: tuple[str, ...], field: str) -> tuple[str, ...]:
    """Validate a bounded ordered tuple of references.

    Args:
        value: Candidate ordered references.
        field: Safe field label for validation.

    Returns:
        Validated references.

    Raises:
        ValueError: If the tuple is oversized or holds invalid text.
    """
    logger.debug("Validating Agentic reference tuple %s", field)
    if len(value) > _MAX_SEQUENCE_ITEMS:
        message = f"{field} must not exceed {_MAX_SEQUENCE_ITEMS} entries"
        raise ValueError(message)
    return tuple(_text(item, field, limit=_MAX_SHORT_TEXT) for item in value)


def _reject_execution_keys(value: Mapping[str, object], field: str) -> None:
    """Reject any key that would carry deterministic execution authority.

    Args:
        value: Candidate mapping.
        field: Safe field label for validation.

    Raises:
        ValueError: If a prohibited execution key is present.
    """
    logger.debug("Screening Agentic mapping %s for execution keys", field)
    for key in value:
        lowered = key.lower()
        if any(token in lowered for token in _PROHIBITED_EXECUTION_TOKENS):
            message = f"{field} must not carry a deterministic execution field"
            raise ValueError(message)


def _freeze_mapping(
    value: Mapping[str, str],
    field: str,
) -> Mapping[str, str]:
    """Validate and freeze a bounded string mapping.

    Args:
        value: Candidate mapping.
        field: Safe field label for validation.

    Returns:
        Deterministically ordered read-only mapping.

    Raises:
        ValueError: If the mapping is empty or oversized.
    """
    logger.debug("Freezing Agentic mapping %s", field)
    if not value:
        message = f"{field} is required"
        raise ValueError(message)
    if len(value) > _MAX_MAPPING_KEYS:
        message = f"{field} must not exceed {_MAX_MAPPING_KEYS} keys"
        raise ValueError(message)
    _reject_execution_keys(value, field)
    frozen = {
        _text(key, field, limit=_MAX_SHORT_TEXT): _text(
            item,
            field,
            limit=_MAX_SHORT_TEXT,
        )
        for key, item in sorted(value.items())
    }
    return MappingProxyType(frozen)


class _AgenticContractModel(BaseModel):
    """Private strict immutable behaviour shared by every Agentic contract."""

    model_config = ConfigDict(
        allow_inf_nan=False,
        arbitrary_types_allowed=True,
        extra="forbid",
        frozen=True,
        strict=True,
    )


class _IdentifiedContract(_AgenticContractModel):
    """Private identity, time, lineage, and integrity envelope.

    Every public Agentic contract inherits this envelope so that
    `FR-AGENTIC-003` holds for each instance.

    Attributes:
        contract_version: Compatibility version.
        created_at: UTC creation time.
        request_id: Request trace identity.
        workflow_id: Workflow trace identity.
        correlation_id: Correlation trace identity.
        causation_id: Optional causing-event trace identity.
        canonical_hash: Canonical content digest of the contract material.
    """

    contract_version: Literal["v1"] = "v1"
    created_at: datetime
    request_id: str
    workflow_id: str
    correlation_id: str
    causation_id: str | None = None
    canonical_hash: str

    @field_validator("created_at")
    @classmethod
    def _validate_created_at(cls, value: datetime) -> datetime:
        """Validate the creation timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        return _utc(value, "created_at")

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        """Validate the request trace identity.

        Args:
            value: Candidate trace identifier.

        Returns:
            Validated trace identifier.
        """
        return _trace(value, "request_id", "req")

    @field_validator("workflow_id")
    @classmethod
    def _validate_workflow_id(cls, value: str) -> str:
        """Validate the workflow trace identity.

        Args:
            value: Candidate trace identifier.

        Returns:
            Validated trace identifier.
        """
        return _trace(value, "workflow_id", "wf")

    @field_validator("correlation_id")
    @classmethod
    def _validate_correlation_id(cls, value: str) -> str:
        """Validate the correlation trace identity.

        Args:
            value: Candidate trace identifier.

        Returns:
            Validated trace identifier.
        """
        return _trace(value, "correlation_id", "cor")

    @field_validator("causation_id")
    @classmethod
    def _validate_causation_id(cls, value: str | None) -> str | None:
        """Validate the optional causation trace identity.

        Args:
            value: Candidate trace identifier.

        Returns:
            Validated trace identifier, or None.
        """
        if value is None:
            return None
        return _trace(value, "causation_id", "cau")

    @field_validator("canonical_hash")
    @classmethod
    def _validate_canonical_hash(cls, value: str) -> str:
        """Validate the canonical content digest.

        Args:
            value: Candidate digest.

        Returns:
            Validated digest.
        """
        return _hash(value, "canonical_hash")


class BudgetUsage(_IdentifiedContract):
    """Bounded consumption recorded against one governed unit of work.

    Usage is reported against the same dimensions an `AgentTask` bounds, so a
    limit and its consumption remain directly comparable.

    Attributes:
        contract_version: Compatibility version.
        schema_id: Namespaced schema identity.
        usage_id: Immutable usage identity.
        task_id: Owning task identity.
        tokens: Consumed model tokens.
        model_calls: Completed model invocations.
        tool_calls: Completed tool invocations.
        cost: Consumed monetary cost.
        compute_seconds: Consumed compute seconds.
        storage_bytes: Consumed staging storage bytes.
        search_trials: Consumed lifetime search trials.
        created_at: UTC creation time.
        request_id: Request trace identity.
        workflow_id: Workflow trace identity.
        correlation_id: Correlation trace identity.
        causation_id: Optional causing-event trace identity.
        canonical_hash: Canonical content digest.
    """

    schema_id: Literal["agentic.budget_usage.v1"] = "agentic.budget_usage.v1"
    usage_id: str
    task_id: str
    tokens: int
    model_calls: int
    tool_calls: int
    cost: Decimal
    compute_seconds: Decimal
    storage_bytes: int
    search_trials: int

    @field_validator("usage_id", "task_id")
    @classmethod
    def _validate_identity(cls, value: str) -> str:
        """Validate one usage identity field.

        Args:
            value: Candidate identifier.

        Returns:
            Validated identifier.
        """
        return _identity(value, "budget usage identity")

    @field_validator(
        "tokens",
        "model_calls",
        "tool_calls",
        "storage_bytes",
        "search_trials",
    )
    @classmethod
    def _validate_counter(cls, value: int) -> int:
        """Validate one non-negative usage counter.

        Args:
            value: Candidate counter.

        Returns:
            Validated counter.
        """
        return _count(value, "budget usage counter")

    @field_validator("cost", "compute_seconds")
    @classmethod
    def _validate_amount(cls, value: Decimal) -> Decimal:
        """Validate one finite non-negative usage amount.

        Args:
            value: Candidate amount.

        Returns:
            Validated amount.
        """
        return _amount(value, "budget usage amount")

    @field_serializer("cost", "compute_seconds", mode="plain")
    def _serialize_amount(self, value: Decimal) -> str:
        """Serialize an exact amount without precision loss.

        Args:
            value: Exact amount.

        Returns:
            Canonical decimal string.
        """
        return str(value)


class AgentProvenance(_IdentifiedContract):
    """Reproducible model, prompt, tool, data, and policy lineage.

    Provenance makes one governed Agentic result reproducible: it pins the
    role, the exact evaluated model, the verified prompt-integrity hashes, and
    the policy under which the work ran (`NFR-AGENTIC-003`).

    Attributes:
        contract_version: Compatibility version.
        schema_id: Namespaced schema identity.
        provenance_id: Immutable provenance identity.
        task_id: Owning task identity.
        role_id: Registered role identity.
        role_version: Exact role manifest version.
        model_profile_id: Evaluated model-profile identity.
        model_provider: Model provider identity.
        model_identifier: Exact pinned model identifier.
        base_prompt_hash: Package-local `prompt.md` content digest.
        manifest_hash: Role manifest digest.
        composite_instruction_hash: Composed instruction digest.
        tool_refs: Ordered registered tool references.
        evidence_refs: Ordered evidence references.
        mandate_id: Firm mandate identity.
        mandate_version: Exact firm mandate version.
        policy_version: Permission-policy version.
        limits_profile_id: Versioned limits-profile identity.
        seed: Optional deterministic seed.
        created_at: UTC creation time.
        request_id: Request trace identity.
        workflow_id: Workflow trace identity.
        correlation_id: Correlation trace identity.
        causation_id: Optional causing-event trace identity.
        canonical_hash: Canonical content digest.
    """

    schema_id: Literal["agentic.agent_provenance.v1"] = "agentic.agent_provenance.v1"
    provenance_id: str
    task_id: str
    role_id: str
    role_version: str
    model_profile_id: str
    model_provider: str
    model_identifier: str
    base_prompt_hash: str
    manifest_hash: str
    composite_instruction_hash: str
    tool_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    mandate_id: str
    mandate_version: str
    policy_version: str
    limits_profile_id: str
    seed: int | None = None

    @field_validator("provenance_id", "task_id")
    @classmethod
    def _validate_identity(cls, value: str) -> str:
        """Validate one provenance identity field.

        Args:
            value: Candidate identifier.

        Returns:
            Validated identifier.
        """
        return _identity(value, "provenance identity")

    @field_validator(
        "role_id",
        "role_version",
        "model_profile_id",
        "model_provider",
        "mandate_id",
        "mandate_version",
        "policy_version",
        "limits_profile_id",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded provenance reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "provenance reference", limit=_MAX_SHORT_TEXT)

    @field_validator("model_identifier")
    @classmethod
    def _validate_model_identifier(cls, value: str) -> str:
        """Validate that the model identifier pins one exact model.

        Args:
            value: Candidate model identifier.

        Returns:
            Validated model identifier.

        Raises:
            ValueError: If the identifier is a floating alias.
        """
        identifier = _text(value, "model_identifier", limit=_MAX_SHORT_TEXT)
        lowered = identifier.lower()
        if "*" in lowered or lowered.rsplit("-", 1)[-1] in _FLOATING_MODEL_ALIASES:
            message = "model_identifier must pin one exact model, not a floating alias"
            raise ValueError(message)
        return identifier

    @field_validator(
        "base_prompt_hash",
        "manifest_hash",
        "composite_instruction_hash",
    )
    @classmethod
    def _validate_integrity_hash(cls, value: str) -> str:
        """Validate one prompt-integrity digest.

        Args:
            value: Candidate digest.

        Returns:
            Validated digest.
        """
        return _hash(value, "provenance integrity digest")

    @field_validator("tool_refs", "evidence_refs")
    @classmethod
    def _validate_refs(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one bounded ordered reference tuple.

        Args:
            value: Candidate references.

        Returns:
            Validated references.
        """
        return _reference_tuple(value, "provenance references")

    @field_validator("seed")
    @classmethod
    def _validate_seed(cls, value: int | None) -> int | None:
        """Validate the optional deterministic seed.

        Args:
            value: Candidate seed.

        Returns:
            Validated seed, or None.
        """
        if value is None:
            return None
        return _count(value, "seed")


class AgentTask(_IdentifiedContract):
    """One bounded unit of governed Agentic work.

    Attributes:
        contract_version: Compatibility version.
        schema_id: Namespaced schema identity.
        task_id: Immutable task identity.
        workflow_name: Registered workflow name.
        workflow_version: Exact workflow version.
        objective: Bounded operator objective.
        input_refs: Ordered typed input references.
        principal_id: Authenticated principal identity.
        scope: Exact governed environment, asset, and account scope.
        deadline_at: UTC deadline after which the task expires.
        idempotency_key: Submission idempotency identity.
        budgets: Bounded limits by supported budget dimension.
        created_at: UTC creation time.
        request_id: Request trace identity.
        workflow_id: Workflow trace identity.
        correlation_id: Correlation trace identity.
        causation_id: Optional causing-event trace identity.
        canonical_hash: Canonical content digest.
    """

    schema_id: Literal["agentic.agent_task.v1"] = "agentic.agent_task.v1"
    task_id: str
    workflow_name: str
    workflow_version: str
    objective: str
    input_refs: tuple[str, ...]
    principal_id: str
    scope: Mapping[str, str]
    deadline_at: datetime
    idempotency_key: str
    budgets: Mapping[str, Decimal]

    @field_validator("task_id")
    @classmethod
    def _validate_identity(cls, value: str) -> str:
        """Validate the task identity.

        Args:
            value: Candidate identifier.

        Returns:
            Validated identifier.
        """
        return _identity(value, "task_id")

    @field_validator(
        "workflow_name",
        "workflow_version",
        "principal_id",
        "idempotency_key",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded task reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "task reference", limit=_MAX_SHORT_TEXT)

    @field_validator("objective")
    @classmethod
    def _validate_objective(cls, value: str) -> str:
        """Validate the bounded objective text.

        Args:
            value: Candidate objective.

        Returns:
            Validated objective.
        """
        return _text(value, "objective")

    @field_validator("input_refs")
    @classmethod
    def _validate_input_refs(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the ordered typed input references.

        Args:
            value: Candidate references.

        Returns:
            Validated references.
        """
        return _reference_tuple(value, "input_refs")

    @field_validator("deadline_at")
    @classmethod
    def _validate_deadline(cls, value: datetime) -> datetime:
        """Validate the task deadline.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        return _utc(value, "deadline_at")

    @field_validator("scope")
    @classmethod
    def _validate_scope(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze the governed task scope.

        Args:
            value: Candidate scope mapping.

        Returns:
            Frozen ordered scope mapping.
        """
        return _freeze_mapping(value, "scope")

    @field_validator("budgets")
    @classmethod
    def _validate_budgets(cls, value: Mapping[str, Decimal]) -> Mapping[str, Decimal]:
        """Validate and freeze the declared budget limits.

        Args:
            value: Candidate budget mapping.

        Returns:
            Frozen ordered budget mapping.

        Raises:
            ValueError: If a dimension is unknown or a limit is invalid.
        """
        logger.debug("Validating Agentic task budgets")
        if not value:
            message = "budgets is required"
            raise ValueError(message)
        unknown = sorted(set(value) - _BUDGET_DIMENSIONS)
        if unknown:
            message = f"budgets contains unsupported dimensions: {', '.join(unknown)}"
            raise ValueError(message)
        frozen = {
            key: _amount(item, "budget limit") for key, item in sorted(value.items())
        }
        return MappingProxyType(frozen)

    @field_serializer("scope", mode="plain")
    def _serialize_scope(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize the governed scope deterministically.

        Args:
            value: Frozen scope mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)

    @field_serializer("budgets", mode="plain")
    def _serialize_budgets(self, value: Mapping[str, Decimal]) -> dict[str, str]:
        """Serialize budget limits without precision loss.

        Args:
            value: Frozen budget mapping.

        Returns:
            Plain ordered mapping of canonical decimal strings.
        """
        return {key: str(item) for key, item in value.items()}


class AgentMessage(_IdentifiedContract):
    """One typed artefact exchanged between registered Agentic roles.

    Messages are typed artefacts, never unrestricted chat. Peer content is
    data and never an instruction, so message content may not carry a
    deterministic execution field.

    Attributes:
        contract_version: Compatibility version.
        schema_id: Namespaced schema identity.
        message_id: Immutable message identity.
        task_id: Owning task identity.
        sender_role_id: Registered sender role identity.
        sender_role_version: Exact sender role version.
        recipient_role_id: Registered recipient role identity.
        message_type: Registered deliberation message type.
        round_index: Zero-based deliberation round.
        content: Bounded typed JSON-safe message content.
        evidence_refs: Ordered evidence references.
        created_at: UTC creation time.
        request_id: Request trace identity.
        workflow_id: Workflow trace identity.
        correlation_id: Correlation trace identity.
        causation_id: Optional causing-event trace identity.
        canonical_hash: Canonical content digest.
    """

    schema_id: Literal["agentic.agent_message.v1"] = "agentic.agent_message.v1"
    message_id: str
    task_id: str
    sender_role_id: str
    sender_role_version: str
    recipient_role_id: str
    message_type: MessageType
    round_index: int
    content: Mapping[str, str]
    evidence_refs: tuple[str, ...]

    @field_validator("message_id", "task_id")
    @classmethod
    def _validate_identity(cls, value: str) -> str:
        """Validate one message identity field.

        Args:
            value: Candidate identifier.

        Returns:
            Validated identifier.
        """
        return _identity(value, "message identity")

    @field_validator("sender_role_id", "sender_role_version", "recipient_role_id")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded role reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "message role reference", limit=_MAX_SHORT_TEXT)

    @field_validator("round_index")
    @classmethod
    def _validate_round_index(cls, value: int) -> int:
        """Validate the deliberation round index.

        Args:
            value: Candidate round index.

        Returns:
            Validated round index.
        """
        return _count(value, "round_index")

    @field_validator("content")
    @classmethod
    def _validate_content(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze bounded typed message content.

        Args:
            value: Candidate content mapping.

        Returns:
            Frozen ordered content mapping.
        """
        return _freeze_mapping(value, "content")

    @field_validator("evidence_refs")
    @classmethod
    def _validate_evidence_refs(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the ordered evidence references.

        Args:
            value: Candidate references.

        Returns:
            Validated references.
        """
        return _reference_tuple(value, "evidence_refs")

    @field_serializer("content", mode="plain")
    def _serialize_content(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize message content deterministically.

        Args:
            value: Frozen content mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


class AgentArtifact(_IdentifiedContract):
    """One immutable content-addressed Agentic artefact reference.

    The artefact contract carries a reference and a digest, never inline
    artefact bytes, so an artefact stays content-addressed and bounded.

    Attributes:
        contract_version: Compatibility version.
        schema_id: Namespaced schema identity.
        artifact_id: Immutable artefact identity.
        task_id: Owning task identity.
        artifact_type: Registered artefact type.
        content_ref: Staging-scoped content reference.
        content_schema_id: Namespaced schema identity of the content.
        content_hash: Canonical digest of the referenced content.
        size_bytes: Referenced content size in bytes.
        provenance_id: Owning provenance identity.
        created_at: UTC creation time.
        request_id: Request trace identity.
        workflow_id: Workflow trace identity.
        correlation_id: Correlation trace identity.
        causation_id: Optional causing-event trace identity.
        canonical_hash: Canonical content digest.
    """

    schema_id: Literal["agentic.agent_artifact.v1"] = "agentic.agent_artifact.v1"
    artifact_id: str
    task_id: str
    artifact_type: str
    content_ref: str
    content_schema_id: str
    content_hash: str
    size_bytes: int
    provenance_id: str

    @field_validator("artifact_id", "task_id", "provenance_id")
    @classmethod
    def _validate_identity(cls, value: str) -> str:
        """Validate one artefact identity field.

        Args:
            value: Candidate identifier.

        Returns:
            Validated identifier.
        """
        return _identity(value, "artifact identity")

    @field_validator("artifact_type", "content_ref", "content_schema_id")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded artefact reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "artifact reference", limit=_MAX_SHORT_TEXT)

    @field_validator("content_hash")
    @classmethod
    def _validate_content_hash(cls, value: str) -> str:
        """Validate the referenced content digest.

        Args:
            value: Candidate digest.

        Returns:
            Validated digest.
        """
        return _hash(value, "content_hash")

    @field_validator("size_bytes")
    @classmethod
    def _validate_size(cls, value: int) -> int:
        """Validate the referenced content size.

        Args:
            value: Candidate size in bytes.

        Returns:
            Validated size.
        """
        return _count(value, "size_bytes")


class WorkflowCheckpoint(_IdentifiedContract):
    """One crash-safe committed position in a durable Agentic workflow.

    Attributes:
        contract_version: Compatibility version.
        schema_id: Namespaced schema identity.
        checkpoint_id: Immutable checkpoint identity.
        task_id: Owning task identity.
        workflow_name: Registered workflow name.
        workflow_version: Exact workflow version.
        node_id: Registered workflow node identity.
        sequence: Monotonic zero-based checkpoint sequence.
        state: Durable workflow state at this checkpoint.
        expected_version: Optimistic-concurrency version guard.
        state_payload_hash: Canonical digest of the committed state payload.
        created_at: UTC creation time.
        request_id: Request trace identity.
        workflow_id: Workflow trace identity.
        correlation_id: Correlation trace identity.
        causation_id: Optional causing-event trace identity.
        canonical_hash: Canonical content digest.
    """

    schema_id: Literal["agentic.workflow_checkpoint.v1"] = (
        "agentic.workflow_checkpoint.v1"
    )
    checkpoint_id: str
    task_id: str
    workflow_name: str
    workflow_version: str
    node_id: str
    sequence: int
    state: WorkflowState
    expected_version: int
    state_payload_hash: str

    @field_validator("checkpoint_id", "task_id")
    @classmethod
    def _validate_identity(cls, value: str) -> str:
        """Validate one checkpoint identity field.

        Args:
            value: Candidate identifier.

        Returns:
            Validated identifier.
        """
        return _identity(value, "checkpoint identity")

    @field_validator("workflow_name", "workflow_version", "node_id")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded checkpoint reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "checkpoint reference", limit=_MAX_SHORT_TEXT)

    @field_validator("sequence", "expected_version")
    @classmethod
    def _validate_counter(cls, value: int) -> int:
        """Validate one non-negative checkpoint counter.

        Args:
            value: Candidate counter.

        Returns:
            Validated counter.
        """
        return _count(value, "checkpoint counter")

    @field_validator("state_payload_hash")
    @classmethod
    def _validate_state_hash(cls, value: str) -> str:
        """Validate the committed state digest.

        Args:
            value: Candidate digest.

        Returns:
            Validated digest.
        """
        return _hash(value, "state_payload_hash")


class AgentResult[T](_IdentifiedContract):
    """Typed outcome of one governed Agentic operation.

    The status separates a completed answer (`ok`) from a governed decision not
    to answer (`refused`) and from a failure of the operation itself
    (`failed`). Refusal is a legitimate terminal outcome, not an error.

    Attributes:
        contract_version: Compatibility version.
        schema_id: Namespaced schema identity.
        result_id: Immutable result identity.
        task_id: Owning task identity.
        status: Completion status.
        payload: Typed payload, present only when the status is `ok`.
        reasons: Ordered enumerated reason codes for refusal or failure.
        detail: Bounded advisory summary carrying no execution authority.
        provenance: Reproducible lineage for this result.
        budget_usage: Bounded consumption for this result.
        created_at: UTC creation time.
        request_id: Request trace identity.
        workflow_id: Workflow trace identity.
        correlation_id: Correlation trace identity.
        causation_id: Optional causing-event trace identity.
        canonical_hash: Canonical content digest.
    """

    schema_id: Literal["agentic.agent_result.v1"] = "agentic.agent_result.v1"
    result_id: str
    task_id: str
    status: ResultStatus
    payload: T | None = None
    reasons: tuple[str, ...] = ()
    detail: str | None = None
    provenance: AgentProvenance
    budget_usage: BudgetUsage

    @field_validator("result_id", "task_id")
    @classmethod
    def _validate_identity(cls, value: str) -> str:
        """Validate one result identity field.

        Args:
            value: Candidate identifier.

        Returns:
            Validated identifier.
        """
        return _identity(value, "result identity")

    @field_validator("reasons")
    @classmethod
    def _validate_reasons(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the enumerated reason codes.

        Free text may not populate a reason: a reason is a stable enumerated
        code so deterministic consumers can branch on it (`FR-AGENTIC-002`).

        Args:
            value: Candidate reason codes.

        Returns:
            Validated reason codes.

        Raises:
            ValueError: If a code is malformed or the tuple is oversized.
        """
        logger.debug("Validating Agentic result reason codes")
        if len(value) > _MAX_SEQUENCE_ITEMS:
            message = f"reasons must not exceed {_MAX_SEQUENCE_ITEMS} entries"
            raise ValueError(message)
        for code in value:
            if _REASON_CODE.fullmatch(code) is None:
                message = "reasons must contain enumerated upper-case codes only"
                raise ValueError(message)
        return value

    @field_validator("detail")
    @classmethod
    def _validate_detail(cls, value: str | None) -> str | None:
        """Validate the bounded advisory detail.

        Args:
            value: Candidate detail text.

        Returns:
            Validated detail text, or None.
        """
        if value is None:
            return None
        return _text(value, "detail")

    @model_validator(mode="after")
    def _validate_status_consistency(self) -> Self:
        """Enforce the status-to-payload contract after field validation.

        Returns:
            The validated result.

        Raises:
            ValueError: If the status and payload or reasons disagree.
        """
        logger.debug("Validating Agentic result status consistency")
        if self.status == "ok":
            if self.payload is None:
                message = "an ok result must carry a typed payload"
                raise ValueError(message)
            if self.reasons:
                message = "an ok result must not carry refusal or failure reasons"
                raise ValueError(message)
            return self
        if self.payload is not None:
            message = "a refused or failed result must not carry a payload"
            raise ValueError(message)
        if not self.reasons:
            message = "a refused or failed result must carry at least one reason"
            raise ValueError(message)
        return self


_PLACEHOLDER_DIGEST = "0" * 64


def _build_contract[M: _IdentifiedContract](
    contract: type[M],
    fields: Mapping[str, object],
) -> M:
    """Build one contract with its canonical content digest computed.

    The digest is derived from the contract's own validated material rather
    than supplied by the caller, so a contract can never carry a hash that
    disagrees with its content.

    Args:
        contract: Concrete contract type to build.
        fields: Complete contract fields excluding `canonical_hash`.

    Returns:
        A validated contract carrying a matching canonical digest.

    Raises:
        ValueError: If the caller supplied the derived digest.
    """
    if "canonical_hash" in fields:
        message = "canonical_hash is derived and must not be supplied"
        raise ValueError(message)
    logger.debug("Building Agentic contract %s", contract.__name__)
    draft = contract.model_validate(
        {**fields, "canonical_hash": _PLACEHOLDER_DIGEST},
    )
    digest = canonical_digest(draft.model_dump(mode="json", exclude={"canonical_hash"}))
    return draft.model_copy(update={"canonical_hash": digest})


def build_agent_task(fields: Mapping[str, object]) -> AgentTask:
    """Build one bounded governed Agentic task.

    Args:
        fields: Complete task fields excluding `canonical_hash`.

    Returns:
        A validated immutable task.
    """
    return _build_contract(AgentTask, fields)


def build_agent_message(fields: Mapping[str, object]) -> AgentMessage:
    """Build one typed deliberation message.

    Args:
        fields: Complete message fields excluding `canonical_hash`.

    Returns:
        A validated immutable message.
    """
    return _build_contract(AgentMessage, fields)


def build_agent_artifact(fields: Mapping[str, object]) -> AgentArtifact:
    """Build one content-addressed artefact reference.

    Args:
        fields: Complete artefact fields excluding `canonical_hash`.

    Returns:
        A validated immutable artefact reference.
    """
    return _build_contract(AgentArtifact, fields)


def build_agent_provenance(fields: Mapping[str, object]) -> AgentProvenance:
    """Build one reproducible provenance record.

    Args:
        fields: Complete provenance fields excluding `canonical_hash`.

    Returns:
        A validated immutable provenance record.
    """
    return _build_contract(AgentProvenance, fields)


def build_budget_usage(fields: Mapping[str, object]) -> BudgetUsage:
    """Build one bounded consumption record.

    Args:
        fields: Complete usage fields excluding `canonical_hash`.

    Returns:
        A validated immutable usage record.
    """
    return _build_contract(BudgetUsage, fields)


def build_workflow_checkpoint(fields: Mapping[str, object]) -> WorkflowCheckpoint:
    """Build one crash-safe workflow checkpoint.

    Args:
        fields: Complete checkpoint fields excluding `canonical_hash`.

    Returns:
        A validated immutable checkpoint.
    """
    return _build_contract(WorkflowCheckpoint, fields)


def build_agent_result[T](fields: Mapping[str, object]) -> AgentResult[T]:
    """Build one typed Agentic result.

    The payload type is supplied by the caller's own return annotation. The
    contract is validated at runtime against the untyped mapping, so the single
    cast below is where that runtime truth is asserted to the type checker;
    callers need no cast of their own.

    Args:
        fields: Complete result fields excluding `canonical_hash`.

    Returns:
        A validated immutable result.
    """
    built = _build_contract(AgentResult[object], fields)
    return cast("AgentResult[T]", built)
