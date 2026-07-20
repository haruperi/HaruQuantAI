"""Broker response and execution event classification primitives.

This module converts provider-specific broker responses and dynamically
pushed execution events into the package's standardized
:class:`~app.services.trading.contracts.NormalizedTradeResult` shape
(TRD-FR-117, TRD-FR-119), classifies unknown/timeout outcomes so callers can
force reconciliation and block retries (TRD-FR-118), classifies
broker-initiated (non-commanded) execution events (TRD-FR-120, TRD-FR-122),
and classifies corporate-action notifications (TRD-FR-121).

Provider retcode-to-error-code mapping is delegated to
``app.utils.standard.classify_broker_error`` (the single source of truth for
deterministic error classification, per the project's error consolidation
decision) rather than duplicated here.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import model_validator

from app.services.trading.contracts import (
    JsonObject,
    NormalizedTradeResult,
    RetrySafety,
    TradingContract,
)
from app.services.trading.errors import classify_broker_error
from app.services.trading.security.error_mapping import TradingMappedError
from app.utils.logger import logger

UNKNOWN_OUTCOME_RETCODE = "10005"
_SUCCESS_RETCODES = frozenset({"10008", "10009"})


class BrokerOutcomeStatus(StrEnum):
    """Classified broker execution outcome status."""

    SUCCESS = "success"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


class BrokerInitiatedEventKind(StrEnum):
    """Sub-classification for broker-initiated (non-commanded) events."""

    SERVER_SIDE_SL_TP_FILL = "server_side_sl_tp_fill"
    STOP_OUT = "stop_out"
    MARGIN_CALL_ACTION = "margin_call_action"
    BROKER_ADMIN_ACTION = "broker_admin_action"
    EXPIRATION = "expiration"


class CorporateActionKind(StrEnum):
    """Corporate action classification."""

    SPLIT = "split"
    REVERSE_SPLIT = "reverse_split"
    SYMBOL_CHANGE = "symbol_change"
    NAME_CHANGE = "name_change"


_CORPORATE_ACTION_KIND_MAP = {
    "split": CorporateActionKind.SPLIT,
    "reverse_split": CorporateActionKind.REVERSE_SPLIT,
    "symbol_change": CorporateActionKind.SYMBOL_CHANGE,
    "name_change": CorporateActionKind.NAME_CHANGE,
}


class BrokerOutcomeClassification(TradingContract):
    """Classified broker execution outcome (TRD-FR-118).

    Attributes:
        status: Classified outcome status.
        retry_safety: Retry safety classification for this outcome.
        requires_reconciliation: Whether this outcome must force
            reconciliation before any retry.
        error_code: Standard public error code, when rejected.
    """

    status: BrokerOutcomeStatus
    retry_safety: RetrySafety
    requires_reconciliation: bool
    error_code: str | None = None


class BrokerInitiatedExecutionEvent(TradingContract):
    """Classified broker-initiated execution event (TRD-FR-120, TRD-FR-122).

    Attributes:
        kind: Broker-initiated event sub-classification.
        normalized_result: Normalized broker-facing trade result.
        requires_critical_incident: Whether this event must raise a critical
            operational incident and force account-scope reconciliation.
        recommended_operational_mode: Recommended session operational mode
            transition, when a critical incident is required. Actually
            transitioning the session is the future responsibility of
            ``runtime/session_manager.py``; this field only recommends it.
    """

    kind: BrokerInitiatedEventKind
    normalized_result: NormalizedTradeResult
    requires_critical_incident: bool
    recommended_operational_mode: str | None = None


class CorporateActionEvent(TradingContract):
    """Classified corporate action notification (TRD-FR-121).

    Attributes:
        kind: Corporate action classification.
        symbol: Affected instrument symbol.
        ratio: Split/reverse-split ratio, required for those kinds.
        new_symbol: Replacement symbol, required for symbol changes.
        effective_at: Effective timestamp of the corporate action.
    """

    kind: CorporateActionKind
    symbol: str
    ratio: Decimal | None = None
    new_symbol: str | None = None
    effective_at: str

    @model_validator(mode="after")
    def validate_action(self) -> CorporateActionEvent:
        """Validate corporate action identifiers and per-kind requirements.

        Returns:
            CorporateActionEvent: Validated corporate action event.

        Raises:
            ValueError: If identifiers are blank or a required per-kind
                field (``ratio``/``new_symbol``) is missing.
        """
        logger.info("Validating corporate action event for {}.", self.symbol)
        if not self.symbol.strip():
            raise ValueError("symbol must be non-empty.")
        if not self.effective_at.strip():
            raise ValueError("effective_at must be non-empty.")
        splits = {CorporateActionKind.SPLIT, CorporateActionKind.REVERSE_SPLIT}
        if self.kind in splits and self.ratio is None:
            raise ValueError("ratio is required for split/reverse_split actions.")
        if self.kind is CorporateActionKind.SYMBOL_CHANGE and not self.new_symbol:
            raise ValueError("new_symbol is required for symbol_change actions.")
        return self


def _get_raw(raw_response: object, name: str) -> object | None:
    """Read a field from a broker response object or mapping.

    Args:
        raw_response: Raw broker response object or mapping.
        name: Field name to read.

    Returns:
        object | None: Field value when present.
    """
    logger.debug("Reading raw broker response field {}.", name)
    if isinstance(raw_response, dict):
        return raw_response.get(name)
    return getattr(raw_response, name, None)


def _extract_decimal(raw_response: object, name: str) -> Decimal | None:
    """Extract an optional Decimal field from a broker response.

    Args:
        raw_response: Raw broker response object or mapping.
        name: Field name to read.

    Returns:
        Decimal | None: Parsed value, or ``None`` when absent or unparsable.
    """
    value = _get_raw(raw_response, name)
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (ArithmeticError, ValueError, TypeError):
        logger.warning("Broker response field {} could not be parsed as Decimal.", name)
        return None


def _extract_str(raw_response: object, name: str) -> str | None:
    """Extract an optional non-blank string field from a broker response.

    Args:
        raw_response: Raw broker response object or mapping.
        name: Field name to read.

    Returns:
        str | None: Parsed value, or ``None`` when absent or blank.
    """
    value = _get_raw(raw_response, name)
    if value is None:
        return None
    text = str(value)
    return text if text.strip() else None


def normalize_broker_response(
    *,
    provider: str,
    raw_response: object,
    request_id: str,
) -> NormalizedTradeResult:
    """Convert a provider-specific broker response into a normalized result.

    Args:
        provider: Broker provider name.
        raw_response: Raw provider response object or mapping.
        request_id: Request identifier associated with this response.

    Returns:
        NormalizedTradeResult: Standardized broker-facing trade result.

    Raises:
        TradingMappedError: If ``provider`` or ``request_id`` is blank.
    """
    logger.info(
        "Normalizing broker response from {} for request {}.", provider, request_id
    )
    if not provider.strip():
        raise TradingMappedError("provider must be non-empty.", code="INVALID_INPUT")
    if not request_id.strip():
        raise TradingMappedError("request_id must be non-empty.", code="INVALID_INPUT")

    retcode = _extract_str(raw_response, "retcode") or UNKNOWN_OUTCOME_RETCODE
    logger.debug("Normalized retcode {} for request {}.", retcode, request_id)
    return NormalizedTradeResult(
        retcode=retcode,
        deal=_extract_str(raw_response, "deal"),
        order=_extract_str(raw_response, "order"),
        volume=_extract_decimal(raw_response, "volume"),
        price=_extract_decimal(raw_response, "price"),
        bid=_extract_decimal(raw_response, "bid"),
        ask=_extract_decimal(raw_response, "ask"),
        comment=_extract_str(raw_response, "comment"),
        request_id=request_id,
        provider=provider,
    )


def classify_stream_event(
    *,
    provider: str,
    raw_event: object,
    request_id: str,
) -> NormalizedTradeResult:
    """Classify a dynamically pushed WebSocket/FIX execution event.

    Delegates to :func:`normalize_broker_response` (TRD-FR-119); the raw
    stream event is expected to carry the same fields as a synchronous
    broker response.

    Args:
        provider: Broker provider name.
        raw_event: Raw streamed execution event object or mapping.
        request_id: Request identifier associated with this event.

    Returns:
        NormalizedTradeResult: Standardized broker-facing trade result.
    """
    logger.info("Classifying streamed execution event from {}.", provider)
    return normalize_broker_response(
        provider=provider, raw_response=raw_event, request_id=request_id
    )


def classify_broker_outcome(
    *,
    normalized: NormalizedTradeResult,
    timed_out: bool = False,
    transport_disconnected: bool = False,
    malformed: bool = False,
) -> BrokerOutcomeClassification:
    """Classify a normalized broker result into an execution outcome.

    Unknown outcomes (timeouts, transport disconnects, or malformed success
    envelopes) always classify as ``unknown`` with ``do_not_retry`` and force
    reconciliation (TRD-FR-118), independent of the reported retcode.

    Args:
        normalized: Normalized broker-facing trade result.
        timed_out: Whether the broker call timed out.
        transport_disconnected: Whether the transport disconnected mid-call.
        malformed: Whether the response envelope was malformed.

    Returns:
        BrokerOutcomeClassification: Classified execution outcome.
    """
    logger.info("Classifying broker outcome for request {}.", normalized.request_id)
    if timed_out or transport_disconnected or malformed:
        logger.debug("Broker outcome for {} is unknown.", normalized.request_id)
        return BrokerOutcomeClassification(
            status=BrokerOutcomeStatus.UNKNOWN,
            retry_safety=RetrySafety.DO_NOT_RETRY,
            requires_reconciliation=True,
        )
    if normalized.retcode in _SUCCESS_RETCODES:
        logger.debug("Broker outcome for {} is success.", normalized.request_id)
        return BrokerOutcomeClassification(
            status=BrokerOutcomeStatus.SUCCESS,
            retry_safety=RetrySafety.DO_NOT_RETRY,
            requires_reconciliation=False,
        )

    classification = classify_broker_error({"retcode": normalized.retcode})
    error_code = str(classification["code"])
    retry_safety = (
        RetrySafety.RETRY_AFTER_DELAY
        if classification["classification"] == "transient"
        else RetrySafety.DO_NOT_RETRY
    )
    logger.debug(
        "Broker outcome for {} rejected with code {}.",
        normalized.request_id,
        error_code,
    )
    return BrokerOutcomeClassification(
        status=BrokerOutcomeStatus.REJECTED,
        retry_safety=retry_safety,
        requires_reconciliation=False,
        error_code=error_code,
    )


def classify_broker_initiated_event(
    *,
    normalized: NormalizedTradeResult,
) -> BrokerInitiatedExecutionEvent:
    """Classify a deal/execution not commanded by this runtime (TRD-FR-120).

    ``stop_out`` and ``margin_call_action`` classifications are flagged as
    requiring a critical incident and a recommended ``close_only`` session
    transition (TRD-FR-122); actually raising the incident and transitioning
    the session is the future responsibility of the monitoring and session
    manager units.

    Args:
        normalized: Normalized broker-facing trade result.

    Returns:
        BrokerInitiatedExecutionEvent: Classified broker-initiated event.
    """
    logger.info(
        "Classifying broker-initiated event for request {}.",
        normalized.request_id,
    )
    comment = (normalized.comment or "").strip().lower()
    if "margin call" in comment:
        kind = BrokerInitiatedEventKind.MARGIN_CALL_ACTION
    elif "stop out" in comment or comment == "so":
        kind = BrokerInitiatedEventKind.STOP_OUT
    elif "expir" in comment:
        kind = BrokerInitiatedEventKind.EXPIRATION
    elif "sl" in comment or "tp" in comment:
        kind = BrokerInitiatedEventKind.SERVER_SIDE_SL_TP_FILL
    else:
        kind = BrokerInitiatedEventKind.BROKER_ADMIN_ACTION

    critical_kinds = {
        BrokerInitiatedEventKind.STOP_OUT,
        BrokerInitiatedEventKind.MARGIN_CALL_ACTION,
    }
    requires_critical_incident = kind in critical_kinds
    recommended_operational_mode = "close_only" if requires_critical_incident else None
    logger.debug("Classified broker-initiated event as {}.", kind.value)
    return BrokerInitiatedExecutionEvent(
        kind=kind,
        normalized_result=normalized,
        requires_critical_incident=requires_critical_incident,
        recommended_operational_mode=recommended_operational_mode,
    )


def classify_corporate_action(*, raw_event: JsonObject) -> CorporateActionEvent:
    """Classify a corporate-action notification payload (TRD-FR-121).

    Args:
        raw_event: JSON-safe corporate action payload carrying
            ``action_type``, ``symbol``, ``effective_at``, and (depending on
            ``action_type``) ``ratio`` and/or ``new_symbol``.

    Returns:
        CorporateActionEvent: Classified corporate action event.

    Raises:
        TradingMappedError: If ``action_type`` is missing or unrecognized.
    """
    logger.info("Classifying corporate action event.")
    action_type = raw_event.get("action_type")
    if (
        not isinstance(action_type, str)
        or action_type not in _CORPORATE_ACTION_KIND_MAP
    ):
        raise TradingMappedError(
            "Unknown or missing corporate action_type.",
            code="INVALID_INPUT",
            details={"action_type": action_type},
        )
    kind = _CORPORATE_ACTION_KIND_MAP[action_type]
    symbol = raw_event.get("symbol")
    effective_at = raw_event.get("effective_at")
    ratio_raw = raw_event.get("ratio")
    new_symbol_raw = raw_event.get("new_symbol")
    logger.debug("Building corporate action event kind {}.", kind.value)
    return CorporateActionEvent(
        kind=kind,
        symbol=str(symbol) if symbol is not None else "",
        ratio=Decimal(str(ratio_raw)) if ratio_raw is not None else None,
        new_symbol=str(new_symbol_raw) if isinstance(new_symbol_raw, str) else None,
        effective_at=str(effective_at) if effective_at is not None else "",
    )
