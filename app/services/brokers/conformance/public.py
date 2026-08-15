"""Public adapter conformance and deterministic fixture operations."""

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

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from app.services.brokers.canonical_contracts.responses import StandardResponse


def create_fake_broker_adapter(*args: Any, **kwargs: Any) -> object:  # noqa: ANN401
    """Create a deterministic fake broker adapter for contract testing.

    Args:
        *args: Positional fake-adapter constructor arguments.
        **kwargs: Keyword fake-adapter constructor arguments.

    Returns:
        Opaque deterministic fake broker adapter.
    """
    from app.services.brokers.conformance.fake import FakeBrokerAdapter

    return FakeBrokerAdapter(*args, **kwargs)


def set_fake_broker_error(
    adapter: object,
    capability_id: str,
    error_code: str | None = None,
    message: str = "bounded fake-adapter error",
) -> StandardResponse[None]:
    """Set or clear one deterministic fake-adapter error fixture.

    Args:
        adapter: Opaque fake adapter created through the package root.
        capability_id: Capability identifier whose result is controlled.
        error_code: Canonical error code, or ``None`` to clear the fixture.
        message: Bounded non-sensitive error message.

    Returns:
        Canonical fixture-update result.

    Raises:
        TypeError: If ``adapter`` is not a package-root fake adapter value.
    """
    from app.services.brokers.conformance.fake import FakeBrokerAdapter

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
) -> object:
    """Create an opaque deterministic fake adapter from root-built values.

    Args:
        config: Opaque Broker connection configuration.
        fixtures: Optional capability-ID to opaque fixture-value mapping.

    Returns:
        Opaque deterministic fake adapter.

    Raises:
        TypeError: If config is not a Broker connection configuration.
    """
    from app.services.brokers.conformance.fake import FakeBrokerAdapter

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
    adapter: object,
    broker_id: str,
    environment: str,
    unsupported_capability_id: str,
    unsupported_operation: str,
) -> dict[str, object]:
    """Run canonical adapter conformance through the package-root boundary.

    Args:
        adapter: Opaque canonical adapter under test.
        broker_id: Exact broker identity.
        environment: Exact broker environment.
        unsupported_capability_id: Capability used to prove fail-closed gating.
        unsupported_operation: Method used to prove unsupported behavior.

    Returns:
        Deterministic conformance verdict mapping.

    Raises:
        TypeError: If ``adapter`` does not satisfy the canonical protocol.
    """
    from app.services.brokers.canonical_contracts.protocols import BrokerAdapter
    from app.services.brokers.conformance.suite import run_adapter_conformance

    if not isinstance(adapter, BrokerAdapter):
        raise TypeError("adapter must satisfy BrokerAdapter")
    return await run_adapter_conformance(
        adapter=adapter,
        broker_id=broker_id,
        environment=environment,
        unsupported_capability=BrokerCapabilityId(unsupported_capability_id),
        unsupported_operation=unsupported_operation,
    )


def build_broker_calculation_fixture(**fields: object) -> object:
    """Build one immutable sanitized calculation fixture.

    Args:
        **fields: Complete bounded fixture fields.

    Returns:
        Opaque checksummed fixture.

    Raises:
        TypeError: If field types are invalid.
        ValueError: If fixture invariants are invalid.
    """
    from app.services.brokers.conformance.fixtures import build_calculation_fixture

    return build_calculation_fixture(**fields)


def dump_broker_calculation_fixture(value: object) -> dict[str, object]:
    """Dump one verified fixture to canonical JSON-safe fields.

    Args:
        value: Opaque calculation fixture.

    Returns:
        Canonical fixture mapping.

    Raises:
        TypeError: If value is not a fixture.
        ValueError: If checksum verification fails.
    """
    from app.services.brokers.conformance.fixtures import dump_calculation_fixture

    return dump_calculation_fixture(value)


def parse_broker_calculation_fixture(value: Mapping[str, object]) -> object:
    """Parse and verify one canonical calculation fixture mapping.

    Args:
        value: Canonical JSON-safe fixture mapping.

    Returns:
        Opaque immutable fixture.

    Raises:
        ValueError: If fields or checksum are invalid.
    """
    from app.services.brokers.conformance.fixtures import parse_calculation_fixture

    return parse_calculation_fixture(value)


async def collect_broker_calculation_fixture(
    *,
    app_environment: str,
    broker_environment: str,
    account_id: str,
    provider_specification_checksum: str,
    terminal_build: str,
    observed_at: datetime,
    inputs: Mapping[str, object],
    provider_call: Callable[[], Awaitable[Mapping[str, object]]],
) -> object:
    """Collect one separately approved dev/demo provider fixture.

    Args:
        app_environment: Application environment, required to be ``dev``.
        broker_environment: Provider environment, required to be ``demo``.
        account_id: Raw account identity digested before artifact construction.
        provider_specification_checksum: Bound provider-specification checksum.
        terminal_build: Bound terminal build.
        observed_at: Aware-UTC observation time.
        inputs: Sanitized calculation inputs.
        provider_call: Separately approved asynchronous provider invocation.

    Returns:
        Opaque sanitized checksummed fixture.

    Raises:
        PermissionError: If the dev/demo guard fails.
        ValueError: If identity or fixture evidence is invalid.
    """
    from app.services.brokers.conformance.fixtures import collect_calculation_fixture

    return await collect_calculation_fixture(
        app_environment=app_environment,
        broker_environment=broker_environment,
        account_id=account_id,
        provider_specification_checksum=provider_specification_checksum,
        terminal_build=terminal_build,
        observed_at=observed_at,
        inputs=inputs,
        provider_call=provider_call,
    )
