"""Authoritative closed Simulation error catalog."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from app.utils import get_logger


@dataclass(frozen=True, slots=True)
class ErrorDefinition:
    """Immutable domain-owned error catalogue entry."""

    code: str
    domain: str
    description: str
    category: str
    severity: Literal["info", "warning", "error", "critical"]
    retryable: bool
    operator_action: str


logger = get_logger(__name__)

_GROUPS: dict[str, tuple[str, ...]] = {
    "request_scope": (
        "SIM_INVALID_CONFIG",
        "SIM_INVALID_DATE_RANGE",
        "SIM_MISSING_SYMBOL",
        "SIM_ARBITRARY_CODE_REJECTED",
        "SIM_UNSUPPORTED_OPERATION",
        "SIM_UNSUPPORTED_ASSET_CLASS",
        "SIM_UNSUPPORTED_FEATURE",
        "SIM_CHECKLIST_INVALID",
        "SIM_ALERT_TRANSITION_INVALID",
        "SIM_RECOVERY_STATE_INVALID",
    ),
    "data_timing": (
        "SIM_DATA_CHECKSUM_MISMATCH",
        "SIM_DATA_SCHEMA_INVALID",
        "SIM_DATA_NON_MONOTONIC",
        "SIM_DATA_DUPLICATE_TIMESTAMP",
        "SIM_DATA_OHLC_INVALID",
        "SIM_DATA_SPREAD_NEGATIVE",
        "SIM_DATA_STALE",
        "SIM_DATA_COVERAGE_INSUFFICIENT",
        "SIM_LOOKAHEAD_DETECTED",
        "SIM_FEATURE_LOOKAHEAD_DETECTED",
        "SIM_UNSUPPORTED_TICK_MODEL",
        "SIM_SPREAD_MISSING",
    ),
    "execution_accounting": (
        "SIM_INVALID_PRICE",
        "SIM_INVALID_VOLUME",
        "SIM_VOLUME_BELOW_MIN",
        "SIM_VOLUME_ABOVE_MAX",
        "SIM_VOLUME_STEP_MISMATCH",
        "SIM_SLIPPAGE_EXCEEDED",
        "SIM_LIQUIDITY_UNAVAILABLE",
        "SIM_GAP_UNCROSSABLE",
        "SIM_MARKET_CLOSED",
        "SIM_UNSUPPORTED_FILL_POLICY",
        "SIM_INSUFFICIENT_MARGIN",
        "SIM_COMMISSION_CALCULATION_FAILED",
        "SIM_SWAP_CALCULATION_FAILED",
        "SIM_FX_EVIDENCE_UNAVAILABLE",
        "SIM_POSITION_NOT_FOUND",
        "SIM_ORDER_NOT_FOUND",
        "SIM_EVENT_PRIORITY_AMBIGUOUS",
        "SIM_ACCOUNT_INVARIANT_BROKEN",
        "SIM_INTEGRITY_FAILURE",
    ),
    "persistence_replay": (
        "SIM_PERSISTENCE_FAILED",
        "SIM_CHECKPOINT_INCOMPATIBLE",
        "SIM_RUN_ID_CONFLICT",
        "SIM_SESSION_NOT_FOUND",
        "SIM_SESSION_EXPIRED",
        "SIM_PLAYBACK_CURSOR_INVALID",
        "SIM_CHECKLIST_BYPASS_DENIED",
        "SIM_RECOVERY_REWIND_DENIED",
        "SIMULATION_RESULT_NOT_FOUND",
        "ANALYTICS_REPORT_INVALID",
        "ANALYTICS_REPORT_CONFLICT",
        "SIMULATION_SEEK_REWIND_FORBIDDEN",
        "SIMULATION_SEEK_LIMIT_EXCEEDED",
        "SIMULATION_SESSION_FINALIZED",
    ),
    "portfolio": (
        "SIM_COMPONENT_INCOMPLETE",
        "SIM_AGGREGATE_UNRECONCILED",
    ),
    "safe_fallback": ("SIM_INTERNAL_ERROR",),
}

_DATA_STALE_CODES = frozenset(
    {
        "SIM_DATA_STALE",
        "SIM_DATA_COVERAGE_INSUFFICIENT",
        "SIM_SPREAD_MISSING",
        "SIM_LIQUIDITY_UNAVAILABLE",
        "SIM_FX_EVIDENCE_UNAVAILABLE",
        "SIM_POSITION_NOT_FOUND",
        "SIM_ORDER_NOT_FOUND",
        "SIM_SESSION_NOT_FOUND",
        "SIM_SESSION_EXPIRED",
    }
)
_INTEGRITY_CODES = frozenset(
    {
        "SIM_DATA_CHECKSUM_MISMATCH",
        "SIM_DATA_SCHEMA_INVALID",
        "SIM_DATA_NON_MONOTONIC",
        "SIM_DATA_DUPLICATE_TIMESTAMP",
        "SIM_DATA_OHLC_INVALID",
        "SIM_DATA_SPREAD_NEGATIVE",
        "SIM_LOOKAHEAD_DETECTED",
        "SIM_FEATURE_LOOKAHEAD_DETECTED",
        "SIM_EVENT_PRIORITY_AMBIGUOUS",
        "SIM_ACCOUNT_INVARIANT_BROKEN",
        "SIM_COMPONENT_INCOMPLETE",
        "SIM_AGGREGATE_UNRECONCILED",
        "SIM_INTEGRITY_FAILURE",
    }
)
_POLICY_CODES = frozenset(
    {
        "SIM_ARBITRARY_CODE_REJECTED",
        "SIM_SLIPPAGE_EXCEEDED",
        "SIM_MARKET_CLOSED",
        "SIM_INSUFFICIENT_MARGIN",
        "SIM_CHECKLIST_BYPASS_DENIED",
        "SIM_RECOVERY_REWIND_DENIED",
    }
)
_TRANSIENT_CODES = frozenset(
    {
        "SIM_COMMISSION_CALCULATION_FAILED",
        "SIM_SWAP_CALCULATION_FAILED",
    }
)
_UNKNOWN_STATE_CODES = frozenset(
    {
        "SIM_PERSISTENCE_FAILED",
        "SIM_RUN_ID_CONFLICT",
        "SIM_INTERNAL_ERROR",
    }
)


def _category_for(code: str) -> str:
    """Return the Utils-owned closed category for one Simulation error code."""
    if code in _DATA_STALE_CODES:
        return "DATA_STALE"
    if code in _INTEGRITY_CODES:
        return "INTEGRITY"
    if code in _POLICY_CODES:
        return "POLICY"
    if code in _TRANSIENT_CODES:
        return "TRANSIENT"
    if code in _UNKNOWN_STATE_CODES:
        return "UNKNOWN_STATE"
    return "PERMANENT"


def _build_catalog() -> Mapping[str, ErrorDefinition]:
    """Build the immutable authoritative error catalog.

    Returns:
        Immutable mapping from error code to public metadata.
    """
    logger.debug("Building the Simulation error catalog")
    catalog = {
        code: ErrorDefinition(
            code=code,
            domain="simulation",
            description=code.removeprefix("SIM_").replace("_", " ").capitalize(),
            category=_category_for(code),
            severity="critical" if group == "safe_fallback" else "error",
            retryable=False,
            operator_action="Review Simulation evidence and correct the request",
        )
        for group, codes in _GROUPS.items()
        for code in codes
    }
    return MappingProxyType(catalog)


SIM_ERROR_CATALOG = _build_catalog()

__all__ = ["SIM_ERROR_CATALOG"]
