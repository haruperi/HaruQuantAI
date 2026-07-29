"""FEAT-BRK-05: Dukascopy research lifecycle and capability boundaries."""

import asyncio

import _support  # noqa: F401
from _support import real_session, require_error, require_success
from app.services.brokers import (
    build_broker_position_filter,
    get_broker_account_info,
    get_broker_asset_info,
    get_broker_balances,
    get_broker_permissions,
    get_broker_platform_info,
    get_broker_positions,
    get_broker_value_field,
    list_broker_accounts,
    list_broker_assets,
    select_broker_account,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


async def fr_brokers_075(adapter: object) -> None:
    """FR-BRK-075: Return genuine provider platform metadata."""
    _header("FR-BRK-075: Return genuine provider platform metadata.")
    require_success("Result", await get_broker_platform_info(adapter))


async def _require_unsupported(adapter: object, operation: str) -> None:
    """Require one non-Dukascopy account capability to remain unsupported."""
    if operation == "permissions":
        result = await get_broker_permissions(adapter)
    elif operation == "accounts":
        result = await list_broker_accounts(adapter)
    elif operation == "select_account":
        result = await select_broker_account(adapter, "acc-1")
    elif operation == "account_info":
        result = await get_broker_account_info(adapter)
    elif operation == "balances":
        result = await get_broker_balances(adapter)
    elif operation == "assets":
        result = await list_broker_assets(adapter)
    elif operation == "asset_info":
        result = await get_broker_asset_info(adapter, "EUR")
    else:
        result = await get_broker_positions(adapter, build_broker_position_filter())
    if get_broker_value_field(result, "status") == "success":
        require_success("Result", result)
    else:
        require_error("Result", result, "BROKER_CAPABILITY_UNSUPPORTED")


async def fr_brokers_076(adapter: object) -> None:
    """FR-BRK-076: Return permissions or deterministic unsupported."""
    _header("FR-BRK-076: Return permissions or deterministic unsupported.")
    await _require_unsupported(adapter, "permissions")


async def fr_brokers_077(adapter: object) -> None:
    """FR-BRK-077: List accounts or deterministic unsupported."""
    _header("FR-BRK-077: List accounts or deterministic unsupported.")
    await _require_unsupported(adapter, "accounts")


async def fr_brokers_078(adapter: object) -> None:
    """FR-BRK-078: Select an account or deterministic unsupported."""
    _header("FR-BRK-078: Select an account or deterministic unsupported.")
    await _require_unsupported(adapter, "select_account")


async def fr_brokers_079(adapter: object) -> None:
    """FR-BRK-079: Return account information or unsupported."""
    _header("FR-BRK-079: Return account information or unsupported.")
    await _require_unsupported(adapter, "account_info")


async def fr_brokers_080(adapter: object) -> None:
    """FR-BRK-080: Return balances or deterministic unsupported."""
    _header("FR-BRK-080: Return balances or deterministic unsupported.")
    await _require_unsupported(adapter, "balances")


async def fr_brokers_081(adapter: object) -> None:
    """FR-BRK-081: List assets or deterministic unsupported."""
    _header("FR-BRK-081: List assets or deterministic unsupported.")
    await _require_unsupported(adapter, "assets")


async def fr_brokers_082(adapter: object) -> None:
    """FR-BRK-082: Return asset metadata or deterministic unsupported."""
    _header("FR-BRK-082: Return asset metadata or deterministic unsupported.")
    await _require_unsupported(adapter, "asset_info")


async def fr_brokers_083(adapter: object) -> None:
    """FR-BRK-083: Return positions or deterministic unsupported."""
    _header("FR-BRK-083: Return positions or deterministic unsupported.")
    await _require_unsupported(adapter, "positions")


async def _run() -> None:
    """Execute capability evidence in one genuine Dukascopy sandbox session."""
    async with real_session("dukascopy") as adapter:
        await fr_brokers_075(adapter)
        await fr_brokers_076(adapter)
        await fr_brokers_077(adapter)
        await fr_brokers_078(adapter)
        await fr_brokers_079(adapter)
        await fr_brokers_080(adapter)
        await fr_brokers_081(adapter)
        await fr_brokers_082(adapter)
        await fr_brokers_083(adapter)


def main() -> None:
    """Run the standalone genuine Dukascopy lifecycle program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
