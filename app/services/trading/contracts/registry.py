"""Exact public contract catalog and non-executable Trading drafts."""

from collections.abc import Mapping
from types import MappingProxyType

from pydantic import ValidationError as PydanticValidationError

from app.services.trading.contracts.models import (
    TRADING_CONTRACT_VERSION,
    JsonValue,
    TradingRequest,
)
from app.services.trading.contracts.responses import (
    error_trading_response,
    success_trading_response,
)
from app.utils import RiskLevel, StandardResponse, logger, redact_text_value


def _contract_entry(
    symbol: str,
    kind: str,
    schema_id: str | None,
    *,
    side_effects: list[str] | None = None,
    approval_required: bool = False,
    idempotency: str = "none",
    statuses: list[str] | None = None,
    errors: list[str] | None = None,
) -> Mapping[str, JsonValue]:
    """Build one immutable public-catalog entry.

    Args:
        symbol: Public Python symbol.
        kind: Contract category.
        schema_id: Versioned schema identifier when applicable.
        side_effects: Declared external side effects.
        approval_required: Whether execution approval is required.
        idempotency: Idempotency behavior.
        statuses: Finite result statuses.
        errors: Finite error families.

    Returns:
        Immutable JSON-safe catalog entry.
    """
    logger.debug("Building Trading public-catalog entry for %s", symbol)
    safe_side_effects: list[JsonValue] = list(side_effects or [])
    safe_statuses: list[JsonValue] = list(statuses or [])
    safe_errors: list[JsonValue] = list(errors or [])
    entry: dict[str, JsonValue] = {
        "symbol": symbol,
        "kind": kind,
        "contract_version": TRADING_CONTRACT_VERSION,
        "schema_id": schema_id,
        "routes": ["sim", "paper", "live"],
        "side_effects": safe_side_effects,
        "approval_required": approval_required,
        "idempotency": idempotency,
        "statuses": safe_statuses,
        "errors": safe_errors,
        "stability": "stable",
    }
    return MappingProxyType(entry)


_ENVELOPE_STATUSES = [
    "success",
    "rejected",
    "blocked",
    "pending_approval",
    "packaged",
    "sent",
    "partial",
    "filled",
    "cancelled",
    "unknown_outcome",
    "error",
]


def _build_public_contracts() -> tuple[Mapping[str, JsonValue], ...]:
    """Build the immutable ordered public API catalog on demand.

    Returns:
        Immutable ordered public-contract entries.
    """
    logger.debug("Building the Trading public-contract catalog")
    return (
        _contract_entry("TRADING_CONTRACT_VERSION", "constant", None),
        _contract_entry("TradingRoute", "enum", None),
        _contract_entry(
            "TradingRequest",
            "model",
            "trading.trading_request.v1",
            approval_required=True,
            idempotency="caller_key",
        ),
        _contract_entry(
            "StandardResponse",
            "response",
            "utils.standard_response.v1",
            statuses=["success", "error"],
        ),
        _contract_entry(
            "OrderIntent",
            "model",
            "trading.order_intent.v1",
            approval_required=True,
            idempotency="canonical_hash",
        ),
        _contract_entry(
            "ExecutionReceipt",
            "model",
            "trading.execution_receipt.v1",
            statuses=[
                "accepted",
                "rejected",
                "partial",
                "filled",
                "cancelled",
                "unknown_outcome",
            ],
        ),
        _contract_entry(
            "TradeRecord",
            "model",
            "trading.trade_record.v1",
        ),
        _contract_entry(
            "PortfolioRebalanceExecutionRequest",
            "model",
            "trading.portfolio_rebalance_execution_request.v1",
            approval_required=True,
            idempotency="canonical_hash",
        ),
        _contract_entry(
            "ExecutionEvidenceReport",
            "model",
            "trading.execution_evidence_report.v1",
        ),
        _contract_entry("TradingError", "error", None),
        _contract_entry("map_trading_error", "function", None),
        _contract_entry("redact_trading_payload", "function", None),
        _contract_entry("get_public_contracts", "function", None),
        _contract_entry(
            "create_trading_action_draft",
            "function",
            None,
            approval_required=True,
            idempotency="caller_key",
            statuses=["packaged"],
            errors=["INVALID_DRAFT"],
        ),
    )


def get_public_contracts() -> StandardResponse[tuple[Mapping[str, JsonValue], ...]]:
    """Return the exact stable Trading contracts API catalog.

    Returns:
        Immutable ordered public-contract entries.
    """
    logger.debug("Returning the Trading public-contract catalog")
    return success_trading_response(
        _build_public_contracts(),
        operation="trading.get_public_contracts",
        message="Trading public contracts returned",
        risk_level=RiskLevel.LOW,
        read_only=True,
    )


def create_trading_action_draft(
    request: Mapping[str, JsonValue],
) -> StandardResponse[TradingRequest]:
    """Validate and package a request without invoking route authority.

    Args:
        request: Canonical request material to package.

    Returns:
        Non-executable packaged Trading envelope.

    Raises:
        TradingError: If request material is invalid.
    """
    logger.info("Creating a non-executable Trading action draft")
    try:
        validated = TradingRequest.model_validate(dict(request))
    except PydanticValidationError:
        logger.warning("Rejecting invalid Trading draft material")
        return error_trading_response(
            code="INVALID_DRAFT",
            details={
                "request_id": request.get("request_id")
                if isinstance(request.get("request_id"), str)
                else None,
                "correlation_id": request.get("correlation_id")
                if isinstance(request.get("correlation_id"), str)
                else None,
            },
            operation="trading.create_trading_action_draft",
            message="Trading draft material is invalid",
            risk_level=RiskLevel.HIGH,
            read_only=True,
        )
    safe_validated = validated
    if validated.control_reason is not None:
        safe_validated = validated.model_copy(
            update={
                "control_reason": str(redact_text_value(validated.control_reason).value)
            }
        )
    return success_trading_response(
        safe_validated,
        operation="trading.create_trading_action_draft",
        message="Trading action draft packaged without execution",
        risk_level=RiskLevel.HIGH,
        request_id=safe_validated.request_id,
        correlation_id=safe_validated.correlation_id,
        read_only=True,
        legacy_status="packaged",
        extensions={
            "route": safe_validated.route.value,
            "provider_id": safe_validated.provider_id,
            "approval_token_ref": safe_validated.approval_token_ref,
            "risk_decision_id": safe_validated.risk_decision_id,
            "risk_classification": "risk_approved",
            "side_effect_classification": "none",
            "idempotency_key": safe_validated.idempotency_key,
            "payload_version": safe_validated.canonical_material_version,
            "redaction_applied": True,
        },
    )


__all__ = ["create_trading_action_draft", "get_public_contracts"]
