"""Receiver-owned result contract for external proposal evaluation."""

from __future__ import annotations

from typing import Literal

from pydantic import field_validator, model_validator

from app.composition.logging import get_logger
from app.services.strategy.contracts._base import _Contract, _hash, _text
from app.services.strategy.contracts.signals import StrategySignal  # noqa: TC001
from app.services.strategy.intents.intent import TradeIntent  # noqa: TC001

logger = get_logger(__name__)

type ProposalEvaluationStatus = Literal[
    "accepted_for_evaluation",
    "rejected",
    "expired",
    "no_signal",
]


class StrategyProposalEvaluationResult(_Contract):
    """Deterministic result of evaluating one external proposal."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.proposal_evaluation_result.v1"] = (
        "strategy.proposal_evaluation_result.v1"
    )
    evaluation_id: str
    evaluation_request_id: str
    status: ProposalEvaluationStatus
    reason_codes: tuple[str, ...] = ()
    source_proposal_id: str
    source_task_id: str
    source_content_hash: str
    strategy_id: str
    strategy_version: str
    evaluated_signals: tuple[StrategySignal, ...] = ()
    trade_intent: TradeIntent | None = None
    request_id: str
    correlation_id: str
    audit_event_ref: str | None = None

    @field_validator(
        "evaluation_id",
        "evaluation_request_id",
        "source_proposal_id",
        "source_task_id",
        "strategy_id",
        "strategy_version",
        "request_id",
        "correlation_id",
        "audit_event_ref",
    )
    @classmethod
    def _validate_text(cls, value: str | None) -> str | None:
        """Validate optional and required bounded text.

        Returns:
            Validated text or ``None``.
        """
        return None if value is None else _text(value)

    @field_validator("source_content_hash")
    @classmethod
    def _validate_source_hash(cls, value: str) -> str:
        """Validate the bound source-proposal hash.

        Returns:
            Validated SHA-256 hash.
        """
        return _hash(value)

    @field_validator("reason_codes")
    @classmethod
    def _validate_reasons(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate unique stable reason codes.

        Returns:
            Validated reason-code tuple.

        Raises:
            ValueError: If reason codes are duplicated.
        """
        reasons = tuple(_text(item) for item in value)
        if len(set(reasons)) != len(reasons):
            raise ValueError("proposal evaluation reason codes must be unique")
        return reasons

    @model_validator(mode="after")
    def _validate_result_shape(self) -> StrategyProposalEvaluationResult:
        """Validate status, evidence, and intent consistency.

        Returns:
            Validated proposal-evaluation result.

        Raises:
            ValueError: If status, reasons, signals, and intent conflict.
        """
        if self.status == "accepted_for_evaluation":
            if self.reason_codes:
                raise ValueError("accepted proposal evaluations cannot have reasons")
        elif not self.reason_codes:
            raise ValueError("non-accepted proposal evaluations require reasons")
        if self.status != "accepted_for_evaluation" and self.trade_intent is not None:
            raise ValueError("only accepted proposal evaluations may expose an intent")
        if self.status == "expired" and self.evaluated_signals:
            raise ValueError("expired proposals cannot expose evaluated signals")
        if self.trade_intent is not None:
            matching = tuple(
                signal
                for signal in self.evaluated_signals
                if signal.active
                and signal.symbol == self.trade_intent.symbol
                and signal.side == self.trade_intent.side
            )
            if not matching:
                raise ValueError("proposal intent requires a matching active signal")
        return self


__all__ = ["StrategyProposalEvaluationResult"]
