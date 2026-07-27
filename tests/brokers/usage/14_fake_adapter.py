"""FEAT-BRK-14: deterministic fake-adapter evidence."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

import _support  # noqa: F401
from _support import config, require_error, require_success
from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerError,
    BrokerErrorCode,
    BrokerId,
    BrokerQuote,
    create_broker_adapter,
)
from app.services.brokers.testing import FakeBrokerAdapter

_NOW = datetime(2026, 1, 1, tzinfo=UTC)
_MUTATIONS = frozenset(
    {
        BrokerCapabilityId.CHECK_ORDER,
        BrokerCapabilityId.PLACE_ORDER,
        BrokerCapabilityId.MODIFY_ORDER,
        BrokerCapabilityId.CANCEL_ORDER,
        BrokerCapabilityId.MODIFY_POSITION,
        BrokerCapabilityId.CLOSE_POSITION,
        BrokerCapabilityId.REPLACE_ORDER,
    }
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    """Declare the bounded non-production fake capability surface."""
    return {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability=("UNAVAILABLE" if operation in _MUTATIONS else "AVAILABLE"),
            access_mode="WRITE" if operation in _MUTATIONS else "READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="TEST_DOUBLE",
        )
        for operation in BrokerCapabilityId
    }


def _quote() -> BrokerQuote:
    """Return one valid deterministic quote fixture."""
    return BrokerQuote(
        symbol="EURUSD",
        price_unit="USD",
        quantity_unit="units",
        retrieved_at=_NOW,
        bid=Decimal("1.10"),
        ask=Decimal("1.11"),
    )


async def fr_brokers_133(adapter: FakeBrokerAdapter) -> None:
    """FR-BRK-133: Inject and return one exact fake-adapter fixture."""
    _header("FR-BRK-133: Inject and return one exact fake-adapter fixture.")
    result = await adapter.get_quote("EURUSD")
    require_success("Result", result)
    assert result.data == _quote()


async def fr_brokers_134(adapter: FakeBrokerAdapter) -> None:
    """FR-BRK-134: Inject and clear one exact fake-adapter error."""
    _header("FR-BRK-134: Inject and clear one exact fake-adapter error.")
    adapter.inject_error(
        BrokerCapabilityId.GET_QUOTE,
        BrokerError(code=BrokerErrorCode.BROKER_TIMEOUT, message="bounded timeout"),
    )
    require_error(
        "Injected result",
        await adapter.get_quote("EURUSD"),
        BrokerErrorCode.BROKER_TIMEOUT,
    )
    adapter.inject_error(BrokerCapabilityId.GET_QUOTE, None)
    require_success("Cleared result", await adapter.get_quote("EURUSD"))


async def fr_brokers_135(adapter: FakeBrokerAdapter) -> None:
    """FR-BRK-135: Preserve the package-root API boundary export."""
    del adapter
    _header("FR-BRK-135: Preserve the package-root API boundary export.")
    print("Result root export verified", callable(create_broker_adapter))
    assert callable(create_broker_adapter)


async def _run() -> None:
    """Execute the feature whose explicit purpose is deterministic fake behavior."""
    quote = _quote()
    adapter = FakeBrokerAdapter(
        config(BrokerId.YAHOO),
        _capabilities(),
        fixtures={BrokerCapabilityId.GET_QUOTE: quote},
    )
    require_success("connect", await adapter.connect())
    try:
        await fr_brokers_133(adapter)
        await fr_brokers_134(adapter)
        await fr_brokers_135(adapter)
    finally:
        require_success("disconnect", await adapter.disconnect())


def main() -> None:
    """Run the standalone deterministic fake-adapter feature program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
