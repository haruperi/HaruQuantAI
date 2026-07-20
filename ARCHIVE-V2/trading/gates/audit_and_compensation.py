"""Pre-mutation audit recording gate primitive.

Pre-mutation audit logs must be successfully written to the injected audit
sink before any broker dispatch is attempted; an audit write failure
immediately blocks the mutation rather than allowing it to proceed
unaudited (TRD-FR-101). Compensating-action orchestration after a broker
outcome is resolved belongs to the future ``reconciliation/`` unit.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.trading.security.error_mapping import TradingMappedError
from app.utils.logger import logger

if TYPE_CHECKING:
    from datetime import datetime

    from app.services.trading.contracts import JsonObject
    from app.services.trading.state.ports import AuditSink


def record_pre_mutation_audit(
    *,
    audit_sink: AuditSink,
    event: JsonObject,
    recorded_at: datetime,
) -> str:
    """Persist a pre-mutation audit event, blocking on write failure.

    Args:
        audit_sink: Injected audit sink.
        event: JSON-safe pre-mutation audit event.
        recorded_at: UTC timestamp from an injected Clock.

    Returns:
        str: Audit reference for this event.

    Raises:
        TradingMappedError: If the audit sink write fails.
    """
    logger.info("Recording pre-mutation audit event.")
    try:
        reference = audit_sink.append(event=event, recorded_at=recorded_at)
    except Exception as exc:
        logger.error("Pre-mutation audit write failed: {}.", exc)
        raise TradingMappedError(
            "Pre-mutation audit write failed; mutation is blocked.",
            code="LIVE_AUDIT_WRITE_FAILED",
        ) from exc
    logger.debug("Pre-mutation audit recorded with reference {}.", reference)
    return reference
