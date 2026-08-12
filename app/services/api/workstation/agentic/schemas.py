"""Agentic gateway request schemas."""

from typing import Literal

from pydantic import Field, field_validator

from app.services.api.contracts.models import (
    _HASH_HEX_LENGTH,
    _MAX_REFERENCE_LENGTH,
    _MAX_SEQUENCE_ITEMS,
    _MAX_TEXT_LENGTH,
    _BaseApiContract,
)


class AgenticRunSubmitRequest(_BaseApiContract):
    """Bounded authenticated request to reserve one Agentic run.

    Submitting reserves a run identifier; it does **not** execute agents. The
    bridge forwards these fields to the Agentic operator surface, which refuses
    an unregistered workflow deterministically.
    """

    workflow_name: str
    objective: str
    input_refs: tuple[str, ...] = ()
    deadline_seconds: int = Field(default=1_800, gt=0, le=86_400)
    cost_budget: str | None = Field(default=None, max_length=64)

    @field_validator("workflow_name", "objective")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate non-empty trimmed bounded text.

        Args:
            value: Candidate text.

        Returns:
            The validated, trimmed text.

        Raises:
            ValueError: If the text is empty, untrimmed, or oversized.
        """
        if not value or value != value.strip():
            msg = "field must be non-empty trimmed text"
            raise ValueError(msg)
        if len(value) > _MAX_TEXT_LENGTH:
            msg = "field must not exceed 2000 characters"
            raise ValueError(msg)
        return value

    @field_validator("input_refs", mode="before")
    @classmethod
    def _coerce_input_refs(cls, value: object) -> tuple[str, ...]:
        """Normalize one JSON-style evidence-reference sequence.

        Args:
            value: Candidate sequence.

        Returns:
            Tuple of trimmed non-empty references.

        Raises:
            ValueError: If any reference is blank or the tuple is oversized.
        """
        if isinstance(value, str):
            items: tuple[str, ...] = (value,)
        elif isinstance(value, tuple | list):
            items = tuple(str(item) for item in value)
        else:
            items = ()
        normalized = tuple(item for item in items if item)
        if len(normalized) != len(items):
            msg = "input_refs must not contain blank entries"
            raise ValueError(msg)
        if len(normalized) > _MAX_SEQUENCE_ITEMS:
            msg = "input_refs must not exceed 64 entries"
            raise ValueError(msg)
        return normalized


class AgenticHandoffApprovalRequest(_BaseApiContract):
    """Bounded authenticated human approval of one staged Agentic artefact."""

    artifact_hash: str
    artifact_id: str
    rationale: str

    @field_validator("artifact_hash")
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        """Validate one lowercase SHA-256 artefact digest.

        Args:
            value: Candidate digest.

        Returns:
            The validated digest.

        Raises:
            ValueError: If the digest is not 64 lowercase hex characters.
        """
        if len(value) != _HASH_HEX_LENGTH or any(
            ch not in "0123456789abcdef" for ch in value
        ):
            msg = "artifact_hash must be 64 lowercase hex characters"
            raise ValueError(msg)
        return value

    @field_validator("artifact_id", "rationale")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate non-empty trimmed bounded text.

        Args:
            value: Candidate text.

        Returns:
            The validated, trimmed text.

        Raises:
            ValueError: If the text is empty, untrimmed, or oversized.
        """
        if not value or value != value.strip():
            msg = "field must be non-empty trimmed text"
            raise ValueError(msg)
        if len(value) > _MAX_TEXT_LENGTH:
            msg = "field must not exceed 2000 characters"
            raise ValueError(msg)
        return value


class AgenticQuarantineRequest(_BaseApiContract):
    """Bounded authenticated request to classify, contain, and record one incident."""

    run_id: str
    kind: Literal[
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
    trigger: str
    role_id: str
    preserved_evidence_refs: tuple[str, ...]
    checkpoint_ref: str

    @field_validator("run_id", "role_id", "checkpoint_ref")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one short non-empty trimmed reference.

        Args:
            value: Candidate reference.

        Returns:
            The validated, trimmed reference.

        Raises:
            ValueError: If the reference is empty, untrimmed, or oversized.
        """
        if not value or value != value.strip():
            msg = "reference must be non-empty trimmed text"
            raise ValueError(msg)
        if len(value) > _MAX_REFERENCE_LENGTH:
            msg = "reference must not exceed 200 characters"
            raise ValueError(msg)
        return value

    @field_validator("trigger")
    @classmethod
    def _validate_trigger(cls, value: str) -> str:
        """Validate the bounded incident trigger description.

        Args:
            value: Candidate trigger text.

        Returns:
            The validated, trimmed trigger text.

        Raises:
            ValueError: If the trigger is empty, untrimmed, or oversized.
        """
        if not value or value != value.strip():
            msg = "trigger must be non-empty trimmed text"
            raise ValueError(msg)
        if len(value) > _MAX_TEXT_LENGTH:
            msg = "trigger must not exceed 2000 characters"
            raise ValueError(msg)
        return value

    @field_validator("preserved_evidence_refs", mode="before")
    @classmethod
    def _coerce_evidence(cls, value: object) -> tuple[str, ...]:
        """Normalize one non-empty JSON-style evidence-reference sequence.

        Args:
            value: Candidate sequence.

        Returns:
            Tuple of trimmed non-empty references.

        Raises:
            ValueError: If the sequence is empty, blank, or oversized.
        """
        if isinstance(value, str):
            items: tuple[str, ...] = (value,)
        elif isinstance(value, tuple | list):
            items = tuple(str(item) for item in value)
        else:
            items = ()
        normalized = tuple(item.strip() for item in items if item.strip())
        if not normalized:
            msg = "preserved_evidence_refs must name at least one reference"
            raise ValueError(msg)
        if len(normalized) != len(items):
            msg = "preserved_evidence_refs must not contain blank entries"
            raise ValueError(msg)
        if len(normalized) > _MAX_SEQUENCE_ITEMS:
            msg = "preserved_evidence_refs must not exceed 64 entries"
            raise ValueError(msg)
        return normalized


class AgenticDisableRequest(_BaseApiContract):
    """Bounded authenticated request to stop the Agentic firm and settle runs."""

    run_ids: tuple[str, ...] = ()
    policy: Literal["cancel", "drain"] = "drain"

    @field_validator("run_ids", mode="before")
    @classmethod
    def _coerce_run_ids(cls, value: object) -> tuple[str, ...]:
        """Normalize one optional JSON-style run-identifier sequence.

        Args:
            value: Candidate sequence.

        Returns:
            Tuple of trimmed non-empty run identifiers.

        Raises:
            ValueError: If any identifier is blank or the tuple is oversized.
        """
        if isinstance(value, str):
            items: tuple[str, ...] = (value,)
        elif isinstance(value, tuple | list):
            items = tuple(str(item) for item in value)
        else:
            items = ()
        normalized = tuple(item.strip() for item in items if item.strip())
        if len(normalized) != len(items):
            msg = "run_ids must not contain blank entries"
            raise ValueError(msg)
        if len(normalized) > _MAX_SEQUENCE_ITEMS:
            msg = "run_ids must not exceed 64 entries"
            raise ValueError(msg)
        return normalized


__all__ = (
    "AgenticDisableRequest",
    "AgenticHandoffApprovalRequest",
    "AgenticQuarantineRequest",
    "AgenticRunSubmitRequest",
)
