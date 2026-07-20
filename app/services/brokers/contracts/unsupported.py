"""Private deterministic unsupported-result construction."""

from datetime import datetime

from app.services.brokers.contracts.enums import (
    BrokerCapabilityId,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
)
from app.services.brokers.contracts.models import BrokerError, BrokerResult
from app.utils import utc_now


def _unsupported_result[T](
    *,
    broker: BrokerId,
    environment: BrokerEnvironment,
    operation: BrokerCapabilityId,
    request_id: str,
    adapter_version: str,
) -> BrokerResult[T]:
    """Build a redacted unsupported result without accessing a provider.

    Returns:
        Canonical unsupported-operation result.
    """
    return BrokerResult(
        status="error",
        broker=broker,
        operation=operation,
        request_id=request_id,
        timestamp=utc_now(),
        environment=environment,
        adapter_version=adapter_version,
        error=BrokerError(
            code=BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED,
            message=f"Capability {operation.value} is unavailable for {broker.value}",
            capability=operation,
        ),
    )


def _utc_now() -> datetime:
    """Return the shared UTC clock value for private protocol defaults."""
    return utc_now()
