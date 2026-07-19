"""Immutable packaging of officially stored Trading execution evidence."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.trading.contracts import (
    TRADING_CONTRACT_VERSION,
    StandardTradingEnvelope,
    TradingError,
    TradingRequest,
)
from app.services.trading.contracts.errors import _redacted_envelope_data
from app.utils import logger, to_json_safe

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


def build_trading_report(
    request: TradingRequest,
    store: TradingStateStore,
) -> StandardTradingEnvelope:
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
    data = _redacted_envelope_data(
        {
            "contract_version": TRADING_CONTRACT_VERSION,
            "schema_id": "trading.execution_evidence_report.v1",
            "scope": {
                "route": request.route,
                "account_id": request.account_id,
                "authority_id": authority,
            },
            "evidence": evidence,
        }
    )
    return StandardTradingEnvelope(
        status="success",
        message="Immutable Trading execution evidence packaged",
        data=data,
        errors=(),
        warnings=(),
        audit_metadata={
            "operation": "build_trading_report",
            "request_id": request.request_id,
            "workflow_id": request.workflow_id,
            "correlation_id": request.correlation_id,
            "redaction_applied": True,
        },
    )


__all__ = ["build_trading_report"]
