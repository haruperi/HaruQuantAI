"""Shared gate step contracts for the deterministic gate pipeline.

Every gate in ``trading/gates/`` returns a :class:`GateStepResult` so the
pipeline orchestrator (``gates/pipeline.py``) can uniformly short-circuit on
failure, stamp per-gate latency into the audit record (TRD-FR-088), and mark
diagnostic-only gates that still ran after an upstream failure
(TRD-FR-087).
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from app.services.trading.contracts import TradingContract
from app.utils.logger import logger
from pydantic import Field, model_validator


class GateName(StrEnum):
    """Canonical gate identifiers for the 16-step live route pipeline."""

    LOCAL_SCHEMA_VALIDATION = "local_schema_validation"
    COMPLIANCE = "compliance"
    PROMOTION_STAGE = "promotion_stage"
    SESSION_STATUS = "session_status"
    KILL_SWITCH = "kill_switch"
    OPERATOR_APPROVAL = "operator_approval"
    RISK_DECISION = "risk_decision"
    MARKET_TURBULENCE = "market_turbulence"
    BROKER_READINESS = "broker_readiness"
    CLOCK_DRIFT = "clock_drift"
    IDEMPOTENCY = "idempotency"
    CONCURRENCY_LEASE = "concurrency_lease"
    RECONCILIATION_AUTHORITY = "reconciliation_authority"
    AUDIT_PRE_RECORD = "audit_pre_record"
    ADAPTER_PERMISSION = "adapter_permission"
    DISPATCH = "dispatch"


class GateStepStatus(StrEnum):
    """Outcome status for one gate evaluation."""

    PASSED = "passed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class GateStepResult(TradingContract):
    """Outcome of one gate evaluation within the pipeline.

    Attributes:
        gate: Gate identifier.
        status: Evaluation outcome status.
        reason_code: Stable public error code, required when blocked.
        message: Human-readable, redacted outcome message.
        latency_ms: Decision latency stamped into the audit record.
        diagnostic_after_failure: Whether this gate ran only for diagnostics
            after an upstream failure (TRD-FR-087).
        mutates_state: Whether this gate mutates local state.
        calls_broker: Whether this gate calls the broker adapter.
        requires_network: Whether this gate requires network access.
    """

    gate: GateName
    status: GateStepStatus
    reason_code: str | None = None
    message: str = ""
    latency_ms: Decimal = Field(default=Decimal(0), ge=0)
    diagnostic_after_failure: bool = False
    mutates_state: bool = False
    calls_broker: bool = False
    requires_network: bool = False

    @model_validator(mode="after")
    def validate_step_result(self) -> GateStepResult:
        """Validate that blocked results always carry a reason code.

        Returns:
            GateStepResult: Validated gate step result.

        Raises:
            ValueError: If ``status`` is blocked without a ``reason_code``.
        """
        logger.info("Validating gate step result for {}.", self.gate.value)
        if self.status is GateStepStatus.BLOCKED and not self.reason_code:
            raise ValueError("reason_code is required when status is blocked.")
        return self


def passed_step(
    *,
    gate: GateName,
    latency_ms: Decimal = Decimal(0),
    message: str = "",
) -> GateStepResult:
    """Build a passing gate step result.

    Args:
        gate: Gate identifier.
        latency_ms: Decision latency stamped into the audit record.
        message: Optional human-readable outcome message.

    Returns:
        GateStepResult: Passing gate step result.
    """
    logger.debug("Building passed gate step result for {}.", gate.value)
    return GateStepResult(
        gate=gate,
        status=GateStepStatus.PASSED,
        latency_ms=latency_ms,
        message=message,
    )


def blocked_step(
    *,
    gate: GateName,
    reason_code: str,
    message: str,
    latency_ms: Decimal = Decimal(0),
) -> GateStepResult:
    """Build a blocking gate step result.

    Args:
        gate: Gate identifier.
        reason_code: Stable public error code.
        message: Human-readable, redacted outcome message.
        latency_ms: Decision latency stamped into the audit record.

    Returns:
        GateStepResult: Blocking gate step result.
    """
    logger.debug(
        "Building blocked gate step result for {}: {}.", gate.value, reason_code
    )
    return GateStepResult(
        gate=gate,
        status=GateStepStatus.BLOCKED,
        reason_code=reason_code,
        message=message,
        latency_ms=latency_ms,
    )


def diagnostic_skipped_step(*, gate: GateName) -> GateStepResult:
    """Build a diagnostic-only skipped gate result (TRD-FR-087).

    Args:
        gate: Gate identifier.

    Returns:
        GateStepResult: Skipped gate result explicitly marked as
        diagnostic-only, non-mutating, broker-free, and network-free.
    """
    logger.debug("Building diagnostic-skipped gate step result for {}.", gate.value)
    return GateStepResult(
        gate=gate,
        status=GateStepStatus.SKIPPED,
        diagnostic_after_failure=True,
        mutates_state=False,
        calls_broker=False,
        requires_network=False,
        message="Skipped after upstream gate failure.",
    )
