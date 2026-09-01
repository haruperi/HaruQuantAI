"""Exactly-once critical operational alert delivery boundary."""

from __future__ import annotations

import hashlib
from typing import Literal

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_json
from app.kernel.time import utc_now
from app.services.api.alerts.models import (
    CriticalAlertDeliveryResult,
    CriticalAlertSink,
    CriticalOperationalAlert,
)

logger = get_logger(__name__)


def deliver_critical_alert(
    alert: CriticalOperationalAlert,
    sink: CriticalAlertSink,
) -> CriticalAlertDeliveryResult:
    """Attempt one channel-neutral delivery without changing source truth.

    Args:
        alert: Validated critical alert.
        sink: Injected channel-neutral delivery boundary.

    Returns:
        Structured delivered or failed result.
    """
    logger.warning("Attempting one critical operational alert delivery")
    attempted_at = utc_now()
    status: Literal["delivered", "failed"] = "delivered"
    failure_code: Literal["ALERT_DELIVERY_FAILED"] | None = None
    try:
        sink(alert, idempotency_key=alert.alert_id)
    except Exception:
        logger.exception(
            "Critical alert delivery failed without changing authoritative state"
        )
        status = "failed"
        failure_code = "ALERT_DELIVERY_FAILED"
    delivery_id = hashlib.sha256(
        canonical_json(
            {
                "alert_id": alert.alert_id,
                "attempted_at": attempted_at.isoformat(),
                "status": status,
            }
        ).encode("utf-8")
    ).hexdigest()
    return CriticalAlertDeliveryResult(
        delivery_id=delivery_id,
        alert_id=alert.alert_id,
        status=status,
        attempted_at=attempted_at,
        failure_code=failure_code,
        request_id=alert.request_id,
        workflow_id=alert.workflow_id,
        correlation_id=alert.correlation_id,
    )


__all__ = ("deliver_critical_alert",)
