"""Receiver-owned request contract for external proposal evaluation."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from pydantic import Field, field_validator, model_validator

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest
from app.services.strategy.contracts._base import (
    _Contract,
    _hash,
    _text,
    _utc,
)

logger = get_logger(__name__)

_MAX_HORIZON_SECONDS = 31 * 24 * 60 * 60


class StrategyProposalEvaluationRequest(_Contract):
    """Immutable request to evaluate an untrusted external proposal."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.proposal_evaluation_request.v1"] = (
        "strategy.proposal_evaluation_request.v1"
    )
    evaluation_request_id: str
    principal_id: str
    source_proposal_id: str
    source_task_id: str
    source_content_hash: str
    strategy_id: str
    strategy_version: str
    instrument: str
    requested_direction: Literal["BUY", "SELL"]
    horizon_seconds: int = Field(gt=0, le=_MAX_HORIZON_SECONDS)
    thesis_evidence_refs: tuple[str, ...]
    invalidation_evidence_refs: tuple[str, ...]
    evaluation_scope: Literal["SIGNAL_ONLY", "TRADE_INTENT_IF_SUPPORTED"]
    requested_at: datetime
    expires_at: datetime
    request_id: str
    workflow_id: str
    correlation_id: str
    idempotency_key: str

    @field_validator(
        "principal_id",
        "source_proposal_id",
        "source_task_id",
        "strategy_id",
        "strategy_version",
        "instrument",
        "request_id",
        "workflow_id",
        "correlation_id",
    )
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one required bounded text field.

        Returns:
            Validated bounded text.
        """
        return _text(value)

    @field_validator("source_content_hash", "idempotency_key")
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        """Validate one lowercase SHA-256 identity.

        Returns:
            Validated SHA-256 identity.
        """
        return _hash(value)

    @field_validator("requested_at", "expires_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one aware UTC timestamp.

        Returns:
            Validated UTC timestamp.
        """
        return _utc(value)

    @field_validator("thesis_evidence_refs", "invalidation_evidence_refs")
    @classmethod
    def _validate_evidence_refs(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate a non-empty unique evidence-reference collection.

        Returns:
            Validated unique evidence references.

        Raises:
            ValueError: If references are empty or duplicated.
        """
        refs = tuple(_text(item) for item in value)
        if not refs or len(set(refs)) != len(refs):
            raise ValueError(
                "proposal evidence references must be non-empty and unique"
            )
        return refs

    @model_validator(mode="after")
    def _validate_identity_and_time(self) -> StrategyProposalEvaluationRequest:
        """Validate derived identity and bounded evaluation lifetime.

        Returns:
            Validated proposal-evaluation request.

        Raises:
            ValueError: If time bounds or derived identities disagree.
        """
        if self.expires_at <= self.requested_at:
            raise ValueError("proposal expiry must follow its request time")
        if self.expires_at > self.requested_at + timedelta(
            seconds=self.horizon_seconds
        ):
            raise ValueError("proposal expiry exceeds its declared horizon")
        expected = canonical_digest(
            self.model_dump(
                mode="python",
                exclude={"evaluation_request_id", "idempotency_key"},
            )
        )
        if self.idempotency_key != expected:
            raise ValueError("proposal idempotency key does not match request content")
        if self.evaluation_request_id != f"proposal-eval-{expected}":
            raise ValueError(
                "proposal evaluation identity does not match request content"
            )
        return self


__all__ = ["StrategyProposalEvaluationRequest"]
