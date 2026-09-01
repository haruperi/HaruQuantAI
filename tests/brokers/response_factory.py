"""Shared StandardResponse fixture construction for Broker consumer tests."""

import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from app.contracts.common.models import get_standard_response_type
from app.kernel.identity import generate_id
from app.kernel.time import utc_now


class BrokerCapabilityId(StrEnum):
    GET_QUOTE = "get_quote"
    CONNECT = "connect"


class BrokerEnvironment(StrEnum):
    DEMO = "demo"
    LIVE = "live"


class BrokerId(StrEnum):
    MT5 = "mt5"
    BINANCE = "binance"
    CTRADER = "ctrader"


class BrokerErrorCode(StrEnum):
    BROKER_OK = "BROKER_OK"
    BROKER_PROVIDER_ERROR = "BROKER_PROVIDER_ERROR"


@dataclass(frozen=True)
class BrokerError:
    code: Any
    message: str


def build_broker_response(*args: Any, **kwargs: Any) -> Any:
    @dataclass(frozen=True)
    class _Res:
        status: str = "success"
        data: Any = None
        error: Any = None

    return _Res()


StandardResponse: Any = get_standard_response_type()


def broker_response(
    operation: BrokerCapabilityId,
    *,
    broker: BrokerId = BrokerId.MT5,
    environment: BrokerEnvironment = BrokerEnvironment.DEMO,
    request_id: str | None = None,
    timestamp: datetime | None = None,
    adapter_version: str = "1.0",
    data: object = None,
    error: BrokerError | object | None = None,
    provider_metadata: Mapping[str, object] | None = None,
) -> StandardResponse[Any]:
    """Build one validated standard Broker fixture response.

    Args:
        operation: Canonical Broker operation.
        broker: Provider/profile identity.
        environment: Provider environment.
        request_id: Optional stable request identity.
        timestamp: Optional stable completion timestamp.
        adapter_version: Adapter version evidence.
        data: Raw successful payload.
        error: Canonical Broker error or a test sentinel mapped to a safe error.
        provider_metadata: Optional provider evidence.

    Returns:
        Validated standard Broker response.
    """
    canonical_error: BrokerError | None
    if error is None or isinstance(error, BrokerError):
        canonical_error = error
    else:
        canonical_error = BrokerError(
            code=BrokerErrorCode.BROKER_RESPONSE_INVALID,
            message=str(error),
            capability=operation,
        )
    return build_broker_response(
        broker=broker,
        operation=operation,
        request_id=request_id or generate_id("req"),
        timestamp=timestamp or utc_now(),
        environment=environment,
        adapter_version=adapter_version,
        start_time=time.perf_counter_ns(),
        data=data,
        error=canonical_error,
        provider_metadata=provider_metadata,
    )


__all__ = ["broker_response"]
