"""Deterministic error-code mapping for the simulator service boundary.

Reuses the shared HaruQuant error taxonomy from ``app.utils.exceptions`` instead of
defining a parallel code registry. This module documents the subset of
approved codes relevant to Simulator, and provides a single redacted mapping
helper for official Simulator tool boundaries.
"""

from typing import TypedDict

from app.utils.logger import logger
from app.utils.security import redact_text


class ErrorPayload(TypedDict):
    """Structured error payload used by standard error envelopes."""

    code: str
    details: str


SIMULATOR_ERROR_CODES: frozenset[str] = frozenset(
    {
        "VALIDATION_FAILED",
        "INVALID_INPUT",
        "UNSUPPORTED_OPERATION",
        "UNKNOWN_ERROR",
        # Custom Simulation Codes
        "SIM_ACCOUNT_INVARIANT_BROKEN",
        "SIM_CALIBRATION_REQUIRED",
        "SIM_CANARY_DIVERGENCE",
        "SIM_CHECKPOINT_INCOMPATIBLE",
        "SIM_COMMISSION_CALCULATION_FAILED",
        "SIM_CONCENTRATION_LIMIT_EXCEEDED",
        "SIM_CORRELATION_LIMIT_EXCEEDED",
        "SIM_DATA_DUPLICATE_TIMESTAMP",
        "SIM_DATA_EMPTY",
        "SIM_DATA_INVALID_OHLC",
        "SIM_DATA_MISSING_COLUMN",
        "SIM_DATA_NEGATIVE_SPREAD",
        "SIM_DATA_NON_MONOTONIC_TIME",
        "SIM_DATA_PARTIAL",
        "SIM_DATA_PRICE_OUTLIER",
        "SIM_DATA_QUALITY_FAILED",
        "SIM_DATA_STALE",
        "SIM_ENVIRONMENT_DRIFT_WARNING",
        "SIM_EVENT_PRIORITY_CONFLICT",
        "SIM_FEATURE_LOOKAHEAD_DETECTED",
        "SIM_FREEZE_LEVEL_VIOLATION",
        "SIM_FX_CROSS_RATE_REJECTED",
        "SIM_FX_RATE_STALE",
        "SIM_GAP_HANDLING_REJECTED",
        "SIM_INSUFFICIENT_MARGIN",
        "SIM_INTERNAL_ERROR",
        "SIM_INVALID_CONFIG",
        "SIM_INVALID_DATE_RANGE",
        "SIM_INVALID_PRICE",
        "SIM_INVALID_STOPS_LEVEL",
        "SIM_INVALID_VOLUME",
        "SIM_IOC_REMAINDER_CANCELLED",
        "SIM_KILL_SWITCH_TRIGGERED",
        "SIM_LIMIT_QUEUE_NOT_FILLED",
        "SIM_LIQUIDITY_UNAVAILABLE",
        "SIM_LOOKAHEAD_DETECTED",
        "SIM_MARKET_CLOSED",
        "SIM_MARKET_HALT_ACTIVE",
        "SIM_MISSING_SYMBOL",
        "SIM_MODEL_GOVERNANCE_EXPIRED",
        "SIM_MONTE_CARLO_FAILED",
        "SIM_OPTIMIZATION_FAILED",
        "SIM_OPTIONAL_SERVICE_DEGRADED",
        "SIM_ORDER_NOT_FOUND",
        "SIM_PARTIAL_FILL_REMAINDER",
        "SIM_PENDING_ORDER_EXPIRED",
        "SIM_PERFORMANCE_GATE_FAILED",
        "SIM_PERSISTENCE_FAILED",
        "SIM_POISON_WORK_UNIT_QUARANTINED",
        "SIM_PORTFOLIO_RISK_REJECTED",
        "SIM_POSITION_NOT_FOUND",
        "SIM_PROMOTION_EVIDENCE_MISSING",
        "SIM_QUEUE_LIMIT_EXCEEDED",
        "SIM_RESEARCH_PROTOCOL_MISSING",
        "SIM_RESOURCE_QUOTA_EXCEEDED",
        "SIM_RUN_ID_CONFLICT",
        "SIM_SIZING_FAILED",
        "SIM_SIZING_INVALID_ATR",
        "SIM_SIZING_INVALID_KELLY_INPUTS",
        "SIM_SIZING_REQUIRES_STOP_LOSS",
        "SIM_SLIPPAGE_EXCEEDED",
        "SIM_SPREAD_MISSING",
        "SIM_SWAP_CALCULATION_FAILED",
        "SIM_SYNTHETIC_TICK_GENERATION_FAILED",
        "SIM_UNSUPPORTED_COMMISSION_MODEL",
        "SIM_UNSUPPORTED_FILL_POLICY",
        "SIM_UNSUPPORTED_LIQUIDITY_MODEL",
        "SIM_UNSUPPORTED_SLIPPAGE_MODEL",
        "SIM_UNSUPPORTED_SPREAD_MODEL",
        "SIM_UNSUPPORTED_SWAP_MODEL",
        "SIM_UNSUPPORTED_TICK_MODEL",
        "SIM_VENDOR_DATA_POLICY_VIOLATION",
        "SIM_VOLUME_ABOVE_MAX",
        "SIM_VOLUME_BELOW_MIN",
        "SIM_VOLUME_STEP_MISMATCH",
        "SIM_WORKER_LOST_REQUEUED",
    }
)
"""Deterministic codes expected at the Simulator official-tool boundary."""


ERROR_MESSAGES: dict[str, str] = {
    "SIM_ACCOUNT_INVARIANT_BROKEN": "Account invariant broken.",
    "SIM_CALIBRATION_REQUIRED": "Calibration required.",
    "SIM_CANARY_DIVERGENCE": "Canary divergence.",
    "SIM_CHECKPOINT_INCOMPATIBLE": "Checkpoint incompatible.",
    "SIM_COMMISSION_CALCULATION_FAILED": "Commission calculation failed.",
    "SIM_CONCENTRATION_LIMIT_EXCEEDED": "Concentration limit exceeded.",
    "SIM_CORRELATION_LIMIT_EXCEEDED": "Correlation limit exceeded.",
    "SIM_DATA_DUPLICATE_TIMESTAMP": "Data duplicate timestamp.",
    "SIM_DATA_EMPTY": "Data empty.",
    "SIM_DATA_INVALID_OHLC": "Data invalid ohlc.",
    "SIM_DATA_MISSING_COLUMN": "Data missing column.",
    "SIM_DATA_NEGATIVE_SPREAD": "Data negative spread.",
    "SIM_DATA_NON_MONOTONIC_TIME": "Data non monotonic time.",
    "SIM_DATA_PARTIAL": "Data partial.",
    "SIM_DATA_PRICE_OUTLIER": "Data price outlier.",
    "SIM_DATA_QUALITY_FAILED": "Data quality failed.",
    "SIM_DATA_STALE": "Data stale.",
    "SIM_ENVIRONMENT_DRIFT_WARNING": "Environment drift warning.",
    "SIM_EVENT_PRIORITY_CONFLICT": "Event priority conflict.",
    "SIM_FEATURE_LOOKAHEAD_DETECTED": "Feature lookahead detected.",
    "SIM_FREEZE_LEVEL_VIOLATION": "Freeze level violation.",
    "SIM_FX_CROSS_RATE_REJECTED": "Fx cross rate rejected.",
    "SIM_FX_RATE_STALE": "Fx rate stale.",
    "SIM_GAP_HANDLING_REJECTED": "Gap handling rejected.",
    "SIM_INSUFFICIENT_MARGIN": "Insufficient margin.",
    "SIM_INTERNAL_ERROR": "Internal simulator calculations failed.",
    "SIM_INVALID_CONFIG": "Simulator configuration failed validation.",
    "SIM_INVALID_DATE_RANGE": "Simulator date range is invalid.",
    "SIM_INVALID_PRICE": "Simulator order price violates constraints.",
    "SIM_INVALID_STOPS_LEVEL": "Stops level configuration is invalid.",
    "SIM_INVALID_VOLUME": "Simulator order volume violates constraints.",
    "SIM_IOC_REMAINDER_CANCELLED": "Immediate-or-cancel remainder cancelled.",
    "SIM_KILL_SWITCH_TRIGGERED": "Simulator kill switch triggered.",
    "SIM_LIMIT_QUEUE_NOT_FILLED": "Limit queue is not filled.",
    "SIM_LIQUIDITY_UNAVAILABLE": "Liquidity is unavailable in simulated venue.",
    "SIM_LOOKAHEAD_DETECTED": "Lookahead bias detected in sim data access.",
    "SIM_MARKET_CLOSED": "Market is closed at order time.",
    "SIM_MARKET_HALT_ACTIVE": "Trading halt active for the asset.",
    "SIM_MISSING_SYMBOL": "Asset symbol is missing in data feed.",
    "SIM_MODEL_GOVERNANCE_EXPIRED": "Sim model governance period has expired.",
    "SIM_MONTE_CARLO_FAILED": "Monte Carlo projection failed.",
    "SIM_OPTIMIZATION_FAILED": "Optimization engine failed to converge.",
    "SIM_OPTIONAL_SERVICE_DEGRADED": "Optional dependency degraded; continuing in fallback.",
    "SIM_ORDER_NOT_FOUND": "Order was not found in sim manager.",
    "SIM_PARTIAL_FILL_REMAINDER": "Order partially filled; remainder kept in book.",
    "SIM_PENDING_ORDER_EXPIRED": "Pending order expired in book.",
    "SIM_PERFORMANCE_GATE_FAILED": "Sim results failed to meet performance gates.",
    "SIM_PERSISTENCE_FAILED": "Saving sim state to persistence layer failed.",
    "SIM_POISON_WORK_UNIT_QUARANTINED": "Poison work unit detected and quarantined.",
    "SIM_PORTFOLIO_RISK_REJECTED": "Portfolio risk limits rejected sim execution.",
    "SIM_POSITION_NOT_FOUND": "Position not found in sim account.",
    "SIM_PROMOTION_EVIDENCE_MISSING": "Promotion rejected due to missing sim evidence.",
    "SIM_QUEUE_LIMIT_EXCEEDED": "Queue limit exceeded.",
    "SIM_RESEARCH_PROTOCOL_MISSING": "Research protocol configuration is missing.",
    "SIM_RESOURCE_QUOTA_EXCEEDED": "Worker limits exceeded quota limits.",
    "SIM_RUN_ID_CONFLICT": "Simulation run ID conflict detected.",
    "SIM_SIZING_FAILED": "Sim order sizing calculation failed.",
    "SIM_SIZING_INVALID_ATR": "Invalid ATR input for sizing.",
    "SIM_SIZING_INVALID_KELLY_INPUTS": "Invalid inputs for Kelly sizing.",
    "SIM_SIZING_REQUIRES_STOP_LOSS": "Position sizing requires a valid stop loss.",
    "SIM_SLIPPAGE_EXCEEDED": "Slippage exceeds threshold.",
    "SIM_SPREAD_MISSING": "Spread is missing.",
    "SIM_SWAP_CALCULATION_FAILED": "Swap calculation failed.",
    "SIM_SYNTHETIC_TICK_GENERATION_FAILED": "Synthetic tick generation failed.",
    "SIM_UNSUPPORTED_COMMISSION_MODEL": "Commission model is unsupported.",
    "SIM_UNSUPPORTED_FILL_POLICY": "Fill policy is unsupported.",
    "SIM_UNSUPPORTED_LIQUIDITY_MODEL": "Liquidity model is unsupported.",
    "SIM_UNSUPPORTED_SLIPPAGE_MODEL": "Slippage model is unsupported.",
    "SIM_UNSUPPORTED_SPREAD_MODEL": "Spread model is unsupported.",
    "SIM_UNSUPPORTED_SWAP_MODEL": "Swap model is unsupported.",
    "SIM_UNSUPPORTED_TICK_MODEL": "Tick model is unsupported.",
    "SIM_VENDOR_DATA_POLICY_VIOLATION": "Vendor data policy violation.",
    "SIM_VOLUME_ABOVE_MAX": "Volume above max.",
    "SIM_VOLUME_BELOW_MIN": "Volume below min.",
    "SIM_VOLUME_STEP_MISMATCH": "Volume step mismatch.",
    "SIM_WORKER_LOST_REQUEUED": "Worker lost requeued.",
}


def to_simulator_error_payload(
    exception: BaseException,
    *,
    request_id: str | None = None,
) -> ErrorPayload:
    """Map an exception to a redacted, deterministic Simulator error payload.

    Use this at the simulator tool boundary instead of returning raw exceptions
    or unredacted messages to callers.

    Args:
        exception: Exception raised by native Simulator functions.
        request_id: Optional trace identifier for log correlation.

    Returns:
        ErrorPayload: Mapping with deterministic ``code`` and redacted
        ``details`` text.
    """
    raw_code = getattr(exception, "code", None)
    code = (
        raw_code
        if isinstance(raw_code, str) and raw_code.strip()
        else "SIM_INTERNAL_ERROR"
    )
    details = f"{exception.__class__.__name__}: {exception}"
    safe_details = redact_text(details)
    logger.warning(
        f"Simulator service error mapped to boundary payload: code={code}",
        extra={"request_id": request_id},
    )
    return {"code": code, "details": safe_details}


# --- Simulation Domain Exceptions ---


class SimulationError(Exception):
    """Base error type for all simulation and backtesting operations.

    Ensures that custom SIM_ error codes are retained on the exception object.
    """

    code = "VALIDATION_FAILED"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        """Initialize with message and optional custom code."""
        super().__init__(message)
        self.code = code if code is not None else self.__class__.code


class SimLookaheadDetectedError(SimulationError):
    """Raised when strategy attempts to access future data."""

    code = "SIM_LOOKAHEAD_DETECTED"


class SimPersistenceFailedError(SimulationError):
    """Raised when journal persistence operations fail."""

    code = "SIM_PERSISTENCE_FAILED"
