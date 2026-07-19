"""Controlled Simulation errors and the closed Phase 1 error catalog."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from app.utils import logger, redact_mapping_value, redact_text_value

_GROUPS: dict[str, tuple[str, ...]] = {
    "request_scope": (
        "SIM_INVALID_CONFIG",
        "SIM_INVALID_DATE_RANGE",
        "SIM_MISSING_SYMBOL",
        "SIM_ARBITRARY_CODE_REJECTED",
        "SIM_UNSUPPORTED_OPERATION",
        "SIM_UNSUPPORTED_ASSET_CLASS",
        "SIM_UNSUPPORTED_FEATURE",
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
    ),
    "persistence_replay": (
        "SIM_PERSISTENCE_FAILED",
        "SIM_CHECKPOINT_INCOMPATIBLE",
        "SIM_RUN_ID_CONFLICT",
    ),
    "portfolio": (
        "SIM_COMPONENT_INCOMPLETE",
        "SIM_AGGREGATE_UNRECONCILED",
    ),
    "safe_fallback": ("SIM_INTERNAL_ERROR",),
}


def _build_catalog() -> Mapping[str, Mapping[str, object]]:
    """Build the immutable authoritative error catalog.

    Returns:
        Immutable mapping from error code to public metadata.
    """
    logger.debug("Building the Simulation error catalog")
    catalog = {
        code: MappingProxyType(
            {
                "group": group,
                "meaning": code.removeprefix("SIM_").lower(),
                "effect": "fail_closed",
            }
        )
        for group, codes in _GROUPS.items()
        for code in codes
    }
    return MappingProxyType(catalog)


SIM_ERROR_CATALOG = _build_catalog()


class SimulationError(Exception):
    """Controlled fail-closed exception at the Simulation boundary.

    Attributes:
        code: Cataloged stable error code.
        message: Bounded safe explanation.
        request_id: Optional safe trace identifier.
    """

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Mapping[str, object] | None = None,
        request_id: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize a controlled Simulation error.

        Args:
            code: Cataloged Simulation error code.
            message: Secret-safe explanation.
            details: Optional bounded details to redact.
            request_id: Optional trace identifier.
            correlation_id: Optional correlation identifier.

        Raises:
            ValueError: If the code is absent or text is invalid.
        """
        logger.debug("Creating SimulationError with code %s", code)
        if code not in SIM_ERROR_CATALOG:
            raise ValueError("Simulation error code is not cataloged")
        if not message or message != message.strip():
            raise ValueError("Simulation error message must be non-empty and trimmed")
        for value, field in (
            (request_id, "request_id"),
            (correlation_id, "correlation_id"),
        ):
            if value is not None and (not value or value != value.strip()):
                identity_error = f"{field} must be non-empty and trimmed"
                raise ValueError(identity_error)
        safe_message = str(redact_text_value(message).value)[:512]
        safe_details: Mapping[str, object] = MappingProxyType({})
        if details is not None:
            redacted = redact_mapping_value(details).value
            if not isinstance(redacted, Mapping):
                raise ValueError("Simulation error details must be a mapping")
            safe_details = MappingProxyType(dict(redacted))
        self.code = code
        self.message = safe_message
        self.details = safe_details
        self.request_id = request_id
        self.correlation_id = correlation_id
        super().__init__(self.message)


def to_simulation_error_payload(error: Exception) -> dict[str, object]:
    """Convert an exception into a bounded redacted public payload.

    Args:
        error: Exception to classify.

    Returns:
        Bounded payload containing only controlled fields.
    """
    logger.info("Converting an exception to a Simulation error payload")
    controlled = (
        error
        if isinstance(error, SimulationError)
        else SimulationError(
            "SIM_INTERNAL_ERROR",
            "Simulation failed safely",
        )
    )
    payload: dict[str, object] = {
        "code": controlled.code,
        "message": controlled.message,
    }
    if controlled.details:
        payload["details"] = dict(controlled.details)
    if controlled.request_id is not None:
        payload["request_id"] = controlled.request_id
    if controlled.correlation_id is not None:
        payload["correlation_id"] = controlled.correlation_id
    return payload


__all__ = ["SIM_ERROR_CATALOG", "SimulationError", "to_simulation_error_payload"]
