"""Immutable packaging of officially stored Trading execution evidence."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from app.composition.logging import get_logger
from app.kernel.serialization import to_json_safe
from app.services.trading.contracts import (
    ExecutionEvidenceReport,
    TradingError,
    TradingRequest,
)
from app.services.trading.contracts.responses import success_trading_response

type StandardResponse[T] = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.trading.contracts.models import JsonValue
    from app.services.trading.state import TradingStateStore

_REQUIRED_EVIDENCE = frozenset(
    {
        "receipts",
        "trade_records",
        "readiness",
        "reconciliation",
        "incidents",
        "warnings",
        "unresolved_actions",
    }
)


def _build_trading_report_value(
    request: TradingRequest,
    store: TradingStateStore,
) -> StandardResponse[ExecutionEvidenceReport]:
    """Package exact stored Trading facts without deriving performance metrics.

    Args:
        request: Governed report request and exact state scope.
        store: Injected Trading state query port.

    Returns:
        Immutable standard envelope containing exact stored evidence.

    Raises:
        TradingError: If stored evidence is missing, inconsistent, or unsafe.
    """
    logger.info("Building immutable Trading evidence report")
    authority = request.provider_id or "simulation"
    try:
        stored = store.load_report_evidence(
            (request.route, request.account_id, authority)
        )
        safe = to_json_safe(stored)
    except TradingError:
        raise
    except Exception as error:
        raise TradingError(
            "PERSISTENCE_FAILED", "Trading report evidence query failed"
        ) from error
    if not isinstance(safe, dict) or not _REQUIRED_EVIDENCE.issubset(safe):
        raise TradingError(
            "RECONCILIATION_REQUIRED", "Trading report evidence is incomplete"
        )
    evidence: dict[str, JsonValue] = {
        key: safe[key] for key in sorted(_REQUIRED_EVIDENCE)
    }
    report = ExecutionEvidenceReport(
        scope={
            "route": request.route.value,
            "account_id": request.account_id,
            "authority_id": authority,
        },
        evidence=evidence,
        request_id=request.request_id,
        workflow_id=request.workflow_id,
        correlation_id=request.correlation_id,
    )
    return success_trading_response(
        report,
        risk_level="low",
        legacy_status="packaged",
        extensions={
            "request_id": request.request_id,
            "workflow_id": request.workflow_id,
            "correlation_id": request.correlation_id,
            "redaction_applied": True,
        },
    )


def build_trading_report(
    request: TradingRequest,
    store: TradingStateStore,
) -> StandardResponse[ExecutionEvidenceReport]:
    """Build the official Trading report in a standard response.

    Args:
        request: Governed report request and exact state scope.
        store: Injected Trading state query port.

    Returns:
        Canonical response containing the exact stored evidence report.
    """
    try:
        return _build_trading_report_value(request, store)
    except Exception as error:  # noqa: BLE001 - normalize report boundary errors.
        from app.services.trading.contracts.errors import map_trading_error

        return map_trading_error(error, {"request_id": request.request_id})


__all__ = ["build_trading_report"]
