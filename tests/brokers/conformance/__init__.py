"""Reusable broker adapter conformance fixtures, fakes, and test suites."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING, Any

from app.services.brokers.canonical_contracts.enums import (
    BrokerCapabilityId,
    BrokerErrorCode,
)
from app.services.brokers.canonical_contracts.models import (
    BrokerCapability,
    BrokerConnectionConfig,
    BrokerError,
)

from tests.brokers.conformance.fake import FakeBrokerAdapter
from tests.brokers.conformance.fixtures import (
    build_calculation_fixture,
    collect_calculation_fixture,
    dump_calculation_fixture,
    parse_calculation_fixture,
)
from tests.brokers.conformance.suite import (
    SCHEMA_ID,
    run_adapter_conformance,
)

if TYPE_CHECKING:
    from app.services.brokers.canonical_contracts.protocols import BrokerAdapter
    from app.services.brokers.canonical_contracts.responses import StandardResponse


def create_fake_broker_adapter(*args: Any, **kwargs: Any) -> FakeBrokerAdapter:
    """Create a deterministic fake broker adapter for contract testing.

    Args:
        *args: Positional fake-adapter constructor arguments.
        **kwargs: Keyword fake-adapter constructor arguments.

    Returns:
        Deterministic fake broker adapter.
    """
    return FakeBrokerAdapter(*args, **kwargs)


def set_fake_broker_error(
    adapter: object,
    capability_id: str,
    error_code: str | None = None,
    message: str = "bounded fake-adapter error",
) -> StandardResponse[None]:
    """Set or clear one deterministic fake-adapter error fixture.

    Args:
        adapter: Fake adapter instance.
        capability_id: Capability identifier whose result is controlled.
        error_code: Canonical error code, or ``None`` to clear the fixture.
        message: Bounded non-sensitive error message.

    Returns:
        Canonical fixture-update result.

    Raises:
        TypeError: If ``adapter`` is not a FakeBrokerAdapter.
    """
    if not isinstance(adapter, FakeBrokerAdapter):
        raise TypeError("adapter must be a fake broker adapter")
    error = (
        None
        if error_code is None
        else BrokerError(code=BrokerErrorCode(error_code), message=message)
    )
    return adapter.inject_error(BrokerCapabilityId(capability_id), error)


def create_configured_fake_broker_adapter(
    config: object, fixtures: Mapping[str, object] | None = None
) -> FakeBrokerAdapter:
    """Create a deterministic fake adapter from connection configuration.

    Args:
        config: Broker connection configuration.
        fixtures: Optional capability-ID to fixture-value mapping.

    Returns:
        Configured deterministic fake adapter.

    Raises:
        TypeError: If config is not a BrokerConnectionConfig.
    """
    if not isinstance(config, BrokerConnectionConfig):
        raise TypeError("config must be a Broker connection configuration")
    mutations = {
        BrokerCapabilityId.CHECK_ORDER,
        BrokerCapabilityId.PLACE_ORDER,
        BrokerCapabilityId.MODIFY_ORDER,
        BrokerCapabilityId.CANCEL_ORDER,
        BrokerCapabilityId.MODIFY_POSITION,
        BrokerCapabilityId.CLOSE_POSITION,
        BrokerCapabilityId.REPLACE_ORDER,
        BrokerCapabilityId.ATTACH_PROTECTION,
        BrokerCapabilityId.REDUCE_POSITION,
    }
    capabilities = {
        capability: BrokerCapability(
            capability=capability,
            implementation_status="IMPLEMENTED",
            availability="UNAVAILABLE" if capability in mutations else "AVAILABLE",
            access_mode="WRITE" if capability in mutations else "READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="TEST_DOUBLE",
        )
        for capability in BrokerCapabilityId
    }
    mapped_fixtures = {
        BrokerCapabilityId(capability): fixture
        for capability, fixture in (fixtures or {}).items()
    }
    return FakeBrokerAdapter(config, capabilities, fixtures=mapped_fixtures)


async def run_broker_adapter_conformance(
    *,
    adapter: BrokerAdapter,
    broker_id: str,
    environment: str,
    unsupported_capability_id: str,
    unsupported_operation: str,
    evaluated_at: datetime | None = None,
) -> dict[str, object]:
    """Run canonical adapter conformance.

    Args:
        adapter: Adapter under test.
        broker_id: Exact broker identity.
        environment: Exact broker environment.
        unsupported_capability_id: Capability used to prove fail-closed gating.
        unsupported_operation: Method used to prove unsupported behavior.
        evaluated_at: Optional aware UTC evaluation timestamp.

    Returns:
        Deterministic conformance verdict mapping.
    """
    return await run_adapter_conformance(
        adapter=adapter,
        broker_id=broker_id,
        environment=environment,
        unsupported_capability=BrokerCapabilityId(unsupported_capability_id),
        unsupported_operation=unsupported_operation,
        evaluated_at=evaluated_at,
    )


# Backward-compatibility aliases for test suites
build_broker_calculation_fixture = build_calculation_fixture
dump_broker_calculation_fixture = dump_calculation_fixture
parse_broker_calculation_fixture = parse_calculation_fixture
collect_broker_calculation_fixture = collect_calculation_fixture

__all__ = [
    "SCHEMA_ID",
    "FakeBrokerAdapter",
    "build_broker_calculation_fixture",
    "build_calculation_fixture",
    "collect_broker_calculation_fixture",
    "collect_calculation_fixture",
    "create_configured_fake_broker_adapter",
    "create_fake_broker_adapter",
    "dump_broker_calculation_fixture",
    "dump_calculation_fixture",
    "parse_broker_calculation_fixture",
    "parse_calculation_fixture",
    "run_adapter_conformance",
    "run_broker_adapter_conformance",
    "set_fake_broker_error",
]
