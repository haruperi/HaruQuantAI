"""Public adapter conformance and deterministic fixture operations."""

from collections.abc import Mapping
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
