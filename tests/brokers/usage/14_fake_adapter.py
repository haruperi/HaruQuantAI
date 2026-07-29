"""FEAT-BRK-14: deterministic fake-adapter evidence."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

import _support  # noqa: F401
from _support import require_error, require_success
from app.services.brokers import (
    build_broker_connection_config,
    build_broker_value,
    connect_broker,
    create_configured_fake_broker_adapter,
    disconnect_broker,
    get_broker_quote,
    get_broker_value_field,
    set_fake_broker_error,
)

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _quote() -> object:
    """Return one valid deterministic quote fixture."""
    return build_broker_value(
        "quote",
        symbol="EURUSD",
        price_unit="USD",
        quantity_unit="units",
        retrieved_at=_NOW,
        bid=Decimal("1.10"),
        ask=Decimal("1.11"),
    )


async def fr_brokers_133(adapter: object) -> None:
    """FR-BRK-133: Inject and return one exact fake-adapter fixture."""
    _header("FR-BRK-133: Inject and return one exact fake-adapter fixture.")
    result = await get_broker_quote(adapter, "EURUSD")
    require_success("Result", result)
    assert get_broker_value_field(result, "data") == _quote()


async def fr_brokers_134(adapter: object) -> None:
    """FR-BRK-134: Inject and clear one exact fake-adapter error."""
    _header("FR-BRK-134: Inject and clear one exact fake-adapter error.")
    require_success(
        "Injected fixture",
        set_fake_broker_error(
            adapter, "get_quote", "BROKER_TIMEOUT", "bounded timeout"
        ),
    )
    require_error(
        "Injected result",
        await get_broker_quote(adapter, "EURUSD"),
        "BROKER_TIMEOUT",
    )
    require_success("Cleared fixture", set_fake_broker_error(adapter, "get_quote"))
    require_success("Cleared result", await get_broker_quote(adapter, "EURUSD"))


async def fr_brokers_135(adapter: object) -> None:
    """FR-BRK-135: Preserve the package-root API boundary export."""
    del adapter
    _header("FR-BRK-135: Preserve the package-root API boundary export.")
    print(
        "Result root export verified", callable(create_configured_fake_broker_adapter)
    )
    assert callable(create_configured_fake_broker_adapter)


async def _run() -> None:
    """Execute the feature whose explicit purpose is deterministic fake behavior."""
    quote = _quote()
    adapter = create_configured_fake_broker_adapter(
        build_broker_connection_config(
            broker_id="yahoo",
            environment="sandbox",
            provider_enabled=True,
        ),
        {"get_quote": quote},
    )
    require_success("connect", await connect_broker(adapter))
    try:
        await fr_brokers_133(adapter)
        await fr_brokers_134(adapter)
        await fr_brokers_135(adapter)
    finally:
        require_success("disconnect", await disconnect_broker(adapter))


def main() -> None:
    """Run the standalone deterministic fake-adapter feature program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
