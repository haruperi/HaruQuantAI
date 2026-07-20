"""Deterministic limit-check contracts.

Defines the typed limit-check result, the typed limit-check registry entry
(name, required evidence, severity, precedence, and evaluator), and the
aggregate assessment contracts consumed by the limits engine. Contracts here
own shape only; ordering and evaluation live in :mod:`app.services.risk.limits.engine`.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Protocol

from app.services.risk.models import (
    RiskAssessmentRequest,
    RiskConfig,
    RiskContract,
    RiskDecisionStatus,
    RiskReasonCode,
    RiskSeverity,
)
from app.utils.logger import logger
from pydantic import Field


class LimitResult(RiskContract):
    """The result of evaluating a single limit check."""

    limit_name: str = Field(
        ..., description="Unique name of the evaluated limit check."
    )
    status: RiskDecisionStatus = Field(
        ..., description="Decision outcome status for this limit."
    )
    reason_code: RiskReasonCode = Field(
        ..., description="Reason code associated with any breach."
    )
    message: str = Field(..., description="Human-readable detail message.")
    severity: RiskSeverity = Field(..., description="Severity level of any violation.")
    breached: bool = Field(..., description="True if a breach was triggered.")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Calculated values or context info."
    )


class LimitCheckFunction(Protocol):
    """Protocol for a single deterministic pre-trade limit check callable."""

    def __call__(
        self, request: RiskAssessmentRequest, config: RiskConfig, /
    ) -> LimitResult:
        """Evaluate the limit check."""
        ...


class LimitCheck(RiskContract):
    """Typed limit-name, required-evidence, severity, evaluator, precedence contract.

    Wraps a pure :class:`LimitCheckFunction` evaluator with the metadata needed
    to run it in a stable, explainable order.
    """

    limit_name: str = Field(..., description="Unique name of this limit check.")
    required_evidence: tuple[str, ...] = Field(
        default=(), description="Evidence keys required for this check to run."
    )
    severity: RiskSeverity = Field(
        default=RiskSeverity.HARD_BREACH,
        description="Default severity classification if this check breaches.",
    )
    precedence: int = Field(
        default=0, description="Stable ordering precedence (lower runs first)."
    )
    evaluator: Callable[[RiskAssessmentRequest, RiskConfig], LimitResult] = Field(
        ..., description="Pure evaluator callable for this check.", exclude=True
    )


LimitContext = RiskAssessmentRequest
"""Type alias: pure limit checks operate directly on the canonical
`RiskAssessmentRequest`, which already carries portfolio, market, and policy
evidence, so no narrower context type is introduced."""

LimitPrecedence = Mapping[RiskDecisionStatus, int]
"""Type alias for a status-to-rank mapping used to select the stable primary
failure among multiple limit results (lower rank wins)."""

DEFAULT_LIMIT_PRECEDENCE: LimitPrecedence = {
    RiskDecisionStatus.BLOCK: 0,
    RiskDecisionStatus.HALT_ALL: 0,
    RiskDecisionStatus.HALT_STRATEGY: 0,
    RiskDecisionStatus.REJECT: 1,
    RiskDecisionStatus.NEEDS_MORE_EVIDENCE: 2,
    RiskDecisionStatus.NEEDS_APPROVAL: 3,
    RiskDecisionStatus.REDUCE_SIZE: 3,
    RiskDecisionStatus.APPROVE: 4,
}


class LimitAssessment(RiskContract):
    """Aggregated outcome of evaluating an ordered limit-check sequence."""

    results: tuple[LimitResult, ...] = Field(
        default_factory=tuple, description="Ordered outcome of every executed check."
    )
    status: RiskDecisionStatus = Field(
        ..., description="Stable aggregated decision status."
    )
    primary_failure: LimitResult | None = Field(
        default=None, description="The stable principal failing result, if any."
    )
    composite_breach_flags: frozenset[RiskReasonCode] = Field(
        default_factory=frozenset,
        description="Distinct reason codes across all breached/non-approve results.",
    )


logger.info("Limits contracts module initialized successfully.")
