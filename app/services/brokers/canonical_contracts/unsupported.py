"""Private deterministic unsupported-response construction."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from app.services.brokers.canonical_contracts.enums import (
    BrokerCapabilityId,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
)
from app.services.brokers.canonical_contracts.models import BrokerError
from app.services.brokers.canonical_contracts.responses import (
    broker_start_time,
    build_broker_response,
)
from app.utils import utc_now

if TYPE_CHECKING:
    from app.services.brokers.canonical_contracts.responses import StandardResponse


def _unsupported_result[T](
    *,
    broker: BrokerId,
    environment: BrokerEnvironment,
    operation: BrokerCapabilityId,
    request_id: str,
    adapter_version: str,
) -> StandardResponse[T]:
    """Build a redacted unsupported result without accessing a provider.

    Args:
        broker: Value supplied to the operation.
        environment: Value supplied to the operation.
        operation: Value supplied to the operation.
        request_id: Value supplied to the operation.
        adapter_version: Value supplied to the operation.

    Returns:
        Canonical unsupported-operation result.
    """
    return build_broker_response(
        broker=broker,
        operation=operation,
        request_id=request_id,
        timestamp=utc_now(),
        environment=environment,
        adapter_version=adapter_version,
        start_time=broker_start_time(),
        error=BrokerError(
            code=BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
            message=f"Capability {operation.value} is unavailable for {broker.value}",
            capability=operation,
        ),
    )


def _utc_now() -> datetime:
    """Return the shared UTC clock value for private protocol defaults.

    Returns:
        Current timezone-aware UTC instant.
    """
    current: datetime = utc_now()
    return current
