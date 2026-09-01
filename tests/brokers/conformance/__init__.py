"""Reusable broker adapter conformance fixtures, fakes, and test suites."""

from __future__ import annotations

from typing import Any

from tests.brokers.conformance.fake import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerError,
    BrokerErrorCode,
    FakeBrokerAdapter,
    StandardResponse,
)
from tests.brokers.conformance.suite import (
    SCHEMA_ID,
    run_adapter_conformance,
)


def create_fake_broker_adapter(*args: Any, **kwargs: Any) -> FakeBrokerAdapter:
    """Create a deterministic fake broker adapter."""
    return FakeBrokerAdapter(*args, **kwargs)


def set_fake_broker_error(
    adapter: FakeBrokerAdapter,
    capability_id: str,
    error_code: str | None = None,
    message: str = "bounded fake-adapter error",
) -> StandardResponse[None]:
    """Set or clear one deterministic fake-adapter error fixture."""
    error = (
        None
        if error_code is None
        else BrokerError(code=BrokerErrorCode(error_code), message=message)
    )
    return adapter.inject_error(BrokerCapabilityId(capability_id), error)


def create_configured_fake_broker_adapter(
    config: Any, fixtures: dict[str, Any] | None = None
) -> FakeBrokerAdapter:
    """Create a deterministic fake adapter from connection configuration."""
    return FakeBrokerAdapter(config, fixtures=fixtures)


async def run_broker_adapter_conformance(
    *,
    adapter: Any,
    broker_id: str,
    environment: str,
    unsupported_capability_id: str,
    unsupported_operation: str,
    evaluated_at: Any = None,
) -> dict[str, Any]:
    """Run canonical adapter conformance."""
    return await run_adapter_conformance(
        adapter=adapter,
        broker_id=broker_id,
        environment=environment,
        unsupported_capability=BrokerCapabilityId(unsupported_capability_id),
        unsupported_operation=unsupported_operation,
        evaluated_at=evaluated_at,
    )


__all__ = [
    "SCHEMA_ID",
    "BrokerCapability",
    "BrokerCapabilityId",
    "BrokerConnectionConfig",
    "BrokerError",
    "BrokerErrorCode",
    "FakeBrokerAdapter",
    "StandardResponse",
    "create_configured_fake_broker_adapter",
    "create_fake_broker_adapter",
    "run_adapter_conformance",
    "run_broker_adapter_conformance",
    "set_fake_broker_error",
]
